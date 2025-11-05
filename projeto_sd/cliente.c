#include <zmq.h>
#include <msgpack.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <pthread.h>
#include <unistd.h>

#define MAX_BUFFER 8192
#define MAX_CANAIS 100
#define MAX_USERNAME 256

// Estrutura do relógio lógico
typedef struct {
    int clock;
    pthread_mutex_t lock;
} RelogioLogico;

// Estrutura do cliente
typedef struct {
    RelogioLogico relogio;
    char nome_usuario[MAX_USERNAME];
    char canais_inscritos[MAX_CANAIS][MAX_USERNAME];
    int num_canais;
    void *context;
    void *socket;
    void *sub_socket;
    int running;
} Cliente;

Cliente *cliente_global = NULL;

// Funções do relógio lógico
void relogio_init(RelogioLogico *r) {
    r->clock = 0;
    pthread_mutex_init(&r->lock, NULL);
}

int relogio_tick(RelogioLogico *r) {
    pthread_mutex_lock(&r->lock);
    r->clock++;
    int valor = r->clock;
    pthread_mutex_unlock(&r->lock);
    return valor;
}

void relogio_update(RelogioLogico *r, int clock_recebido) {
    pthread_mutex_lock(&r->lock);
    if (clock_recebido > r->clock) {
        r->clock = clock_recebido;
    }
    pthread_mutex_unlock(&r->lock);
}

// Função para obter timestamp
double get_timestamp() {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return ts.tv_sec + ts.tv_nsec / 1000000000.0;
}

// Thread para receber mensagens
void *receber_mensagens(void *arg) {
    Cliente *c = (Cliente *)arg;
    
    printf("[CLIENTE] Subscriber iniciado, aguardando mensagens...\n");
    fflush(stdout);
    
    while (c->running) {
        zmq_msg_t topic_msg, data_msg;
        zmq_msg_init(&topic_msg);
        zmq_msg_init(&data_msg);
        
        int size = zmq_msg_recv(&topic_msg, c->sub_socket, 0);
        if (size == -1) {
            zmq_msg_close(&topic_msg);
            zmq_msg_close(&data_msg);
            continue;
        }
        
        char topic[256];
        memcpy(topic, zmq_msg_data(&topic_msg), size);
        topic[size] = '\0';
        
        size = zmq_msg_recv(&data_msg, c->sub_socket, 0);
        if (size == -1) {
            zmq_msg_close(&topic_msg);
            zmq_msg_close(&data_msg);
            continue;
        }
        
        msgpack_unpacked result;
        msgpack_unpacked_init(&result);
        
        if (msgpack_unpack_next(&result, zmq_msg_data(&data_msg), size, NULL)) {
            msgpack_object obj = result.data;
            
            if (obj.type == MSGPACK_OBJECT_MAP) {
                char user[256] = "", message[1024] = "", src[256] = "", channel[256] = "";
                int clock = 0;
                double timestamp = 0;
                
                for (uint32_t i = 0; i < obj.via.map.size; i++) {
                    msgpack_object_kv *kv = &obj.via.map.ptr[i];
                    
                    if (kv->key.type == MSGPACK_OBJECT_STR) {
                        char key[64];
                        memcpy(key, kv->key.via.str.ptr, kv->key.via.str.size);
                        key[kv->key.via.str.size] = '\0';
                        
                        if (strcmp(key, "user") == 0 && kv->val.type == MSGPACK_OBJECT_STR) {
                            memcpy(user, kv->val.via.str.ptr, kv->val.via.str.size);
                            user[kv->val.via.str.size] = '\0';
                        }
                        else if (strcmp(key, "message") == 0 && kv->val.type == MSGPACK_OBJECT_STR) {
                            memcpy(message, kv->val.via.str.ptr, kv->val.via.str.size);
                            message[kv->val.via.str.size] = '\0';
                        }
                        else if (strcmp(key, "src") == 0 && kv->val.type == MSGPACK_OBJECT_STR) {
                            memcpy(src, kv->val.via.str.ptr, kv->val.via.str.size);
                            src[kv->val.via.str.size] = '\0';
                        }
                        else if (strcmp(key, "channel") == 0 && kv->val.type == MSGPACK_OBJECT_STR) {
                            memcpy(channel, kv->val.via.str.ptr, kv->val.via.str.size);
                            channel[kv->val.via.str.size] = '\0';
                        }
                        else if (strcmp(key, "clock") == 0 && kv->val.type == MSGPACK_OBJECT_POSITIVE_INTEGER) {
                            clock = kv->val.via.u64;
                            relogio_update(&c->relogio, clock);
                        }
                        else if (strcmp(key, "timestamp") == 0 && kv->val.type == MSGPACK_OBJECT_FLOAT64) {
                            timestamp = kv->val.via.f64;
                        }
                    }
                }
                
                time_t t = (time_t)timestamp;
                struct tm *tm_info = localtime(&t);
                char timestr[20];
                strftime(timestr, sizeof(timestr), "%H:%M:%S", tm_info);
                
                if (strlen(channel) > 0) {
                    printf("\n[%s] %s: %s\n", channel, user, message);
                    printf("   [Clock: %d | %s]\n", clock, timestr);
                } else if (strlen(src) > 0) {
                    printf("\nMensagem privada de %s: %s\n", src, message);
                    printf("   [Clock: %d | %s]\n", clock, timestr);
                }
                fflush(stdout);
            }
        }
        
        msgpack_unpacked_destroy(&result);
        zmq_msg_close(&topic_msg);
        zmq_msg_close(&data_msg);
    }
    
    return NULL;
}

// Função para inscrever em tópico
void inscrever_topico(Cliente *c, const char *topico) {
    zmq_setsockopt(c->sub_socket, ZMQ_SUBSCRIBE, topico, strlen(topico));
    printf("[CLIENTE] Inscrito no tópico: %s\n", topico);
    fflush(stdout);
}

// Função genérica para enviar requisição
void enviar_requisicao(Cliente *c, const char *service, msgpack_sbuffer *sbuf) {
    msgpack_sbuffer req_buf;
    msgpack_sbuffer_init(&req_buf);
    msgpack_packer req_pk;
    msgpack_packer_init(&req_pk, &req_buf, msgpack_sbuffer_write);
    
    // Monta: {"service": "...", "data": {...}}
    msgpack_pack_map(&req_pk, 2);
    
    msgpack_pack_str(&req_pk, 7);
    msgpack_pack_str_body(&req_pk, "service", 7);
    msgpack_pack_str(&req_pk, strlen(service));
    msgpack_pack_str_body(&req_pk, service, strlen(service));
    
    msgpack_pack_str(&req_pk, 4);
    msgpack_pack_str_body(&req_pk, "data", 4);
    msgpack_sbuffer_write(&req_buf, sbuf->data, sbuf->size);
    
    zmq_send(c->socket, req_buf.data, req_buf.size, 0);
    
    char buffer[MAX_BUFFER];
    int size = zmq_recv(c->socket, buffer, MAX_BUFFER, 0);
    
    msgpack_sbuffer_destroy(&req_buf);
    
    if (size > 0) {
        msgpack_unpacked result;
        msgpack_unpacked_init(&result);
        
        if (msgpack_unpack_next(&result, buffer, size, NULL)) {
            msgpack_object obj = result.data;
            
            if (obj.type == MSGPACK_OBJECT_MAP) {
                for (uint32_t i = 0; i < obj.via.map.size; i++) {
                    msgpack_object_kv *kv = &obj.via.map.ptr[i];
                    
                    if (kv->key.type == MSGPACK_OBJECT_STR) {
                        char key[64];
                        memcpy(key, kv->key.via.str.ptr, kv->key.via.str.size);
                        key[kv->key.via.str.size] = '\0';
                        
                        if (strcmp(key, "data") == 0 && kv->val.type == MSGPACK_OBJECT_MAP) {
                            char status[64] = "";
                            char msg[512] = "";
                            int clock_val = 0;
                            char users_str[2048] = "";
                            char channels_str[2048] = "";
                            
                            for (uint32_t j = 0; j < kv->val.via.map.size; j++) {
                                msgpack_object_kv *data_kv = &kv->val.via.map.ptr[j];
                                
                                if (data_kv->key.type == MSGPACK_OBJECT_STR) {
                                    char data_key[64];
                                    memcpy(data_key, data_kv->key.via.str.ptr, data_kv->key.via.str.size);
                                    data_key[data_kv->key.via.str.size] = '\0';
                                    
                                    if (strcmp(data_key, "clock") == 0 && data_kv->val.type == MSGPACK_OBJECT_POSITIVE_INTEGER) {
                                        clock_val = data_kv->val.via.u64;
                                        relogio_update(&c->relogio, clock_val);
                                    }
                                    else if (strcmp(data_key, "status") == 0 && data_kv->val.type == MSGPACK_OBJECT_STR) {
                                        memcpy(status, data_kv->val.via.str.ptr, data_kv->val.via.str.size);
                                        status[data_kv->val.via.str.size] = '\0';
                                    }
                                    else if (strcmp(data_key, "message") == 0 && data_kv->val.type == MSGPACK_OBJECT_STR) {
                                        memcpy(msg, data_kv->val.via.str.ptr, data_kv->val.via.str.size);
                                        msg[data_kv->val.via.str.size] = '\0';
                                    }
                                    else if (strcmp(data_key, "users") == 0 && data_kv->val.type == MSGPACK_OBJECT_ARRAY) {
                                        for (uint32_t k = 0; k < data_kv->val.via.array.size; k++) {
                                            if (data_kv->val.via.array.ptr[k].type == MSGPACK_OBJECT_STR) {
                                                char temp[256];
                                                memcpy(temp, data_kv->val.via.array.ptr[k].via.str.ptr, 
                                                       data_kv->val.via.array.ptr[k].via.str.size);
                                                temp[data_kv->val.via.array.ptr[k].via.str.size] = '\0';
                                                if (k > 0) strcat(users_str, ", ");
                                                strcat(users_str, temp);
                                            }
                                        }
                                    }
                                    else if (strcmp(data_key, "channels") == 0 && data_kv->val.type == MSGPACK_OBJECT_ARRAY) {
                                        for (uint32_t k = 0; k < data_kv->val.via.array.size; k++) {
                                            if (data_kv->val.via.array.ptr[k].type == MSGPACK_OBJECT_STR) {
                                                char temp[256];
                                                memcpy(temp, data_kv->val.via.array.ptr[k].via.str.ptr, 
                                                       data_kv->val.via.array.ptr[k].via.str.size);
                                                temp[data_kv->val.via.array.ptr[k].via.str.size] = '\0';
                                                if (k > 0) strcat(channels_str, ", ");
                                                strcat(channels_str, temp);
                                            }
                                        }
                                    }
                                }
                            }
                            
                            if (strcmp(status, "OK") == 0) {
                                if (strlen(users_str) > 0) {
                                    printf("Usuários cadastrados: %s\n", users_str);
                                } else if (strlen(channels_str) > 0) {
                                    printf("Canais disponíveis: %s\n", channels_str);
                                } else {
                                    printf("Operação realizada com sucesso!\n");
                                }
                                printf("   [Clock: %d]\n", clock_val);
                            } else {
                                if (strlen(msg) > 0) {
                                    printf("Erro: %s\n", msg);
                                } else {
                                    printf("Erro na operação\n");
                                }
                                printf("   [Clock: %d]\n", clock_val);
                            }
                        }
                    }
                }
            }
        }
        
        msgpack_unpacked_destroy(&result);
    }
}

// Menu
void exibir_menu() {
    printf("\n==================================================\n");
    printf("Bem-vindo ao BulletInBoard!\n");
    printf("==================================================\n");
    printf("Opções disponíveis:\n");
    printf("[1] - Login\n");
    printf("[2] - Listar usuários\n");
    printf("[3] - Cadastrar canal\n");
    printf("[4] - Listar canais\n");
    printf("[5] - Inscrever em canal\n");
    printf("[6] - Publicar mensagem em um canal\n");
    printf("[7] - Enviar mensagem privada para usuário\n");
    printf("[0] - Sair do programa\n");
    printf("--------------------------------------------------\n");
}

// Função principal
int main() {
    Cliente c;
    cliente_global = &c;
    
    relogio_init(&c.relogio);
    c.nome_usuario[0] = '\0';
    c.num_canais = 0;
    c.running = 1;
    
    c.context = zmq_ctx_new();
    c.socket = zmq_socket(c.context, ZMQ_REQ);
    zmq_connect(c.socket, "tcp://broker:5555");
    
    c.sub_socket = zmq_socket(c.context, ZMQ_SUB);
    zmq_connect(c.sub_socket, "tcp://proxy:5558");
    
    printf("[CLIENTE] Cliente em C iniciado!\n");
    fflush(stdout);
    
    pthread_t receiver_thread;
    pthread_create(&receiver_thread, NULL, receber_mensagens, &c);
    
    exibir_menu();
    
    char opcao[10];
    while (c.running) {
        printf("\nEntre com a opção: ");
        fflush(stdout);
        
        if (fgets(opcao, sizeof(opcao), stdin) == NULL) break;
        opcao[strcspn(opcao, "\n")] = 0;
        
        if (strcmp(opcao, "0") == 0) {
            printf("Encerrando o programa...\n");
            c.running = 0;
            break;
        }
        else if (strcmp(opcao, "1") == 0) {
            // Login
            printf("\n------ Login ------\n");
            printf("Entre com o seu usuário: ");
            fflush(stdout);
            
            char user[MAX_USERNAME];
            fgets(user, sizeof(user), stdin);
            user[strcspn(user, "\n")] = 0;
            
            msgpack_sbuffer sbuf;
            msgpack_sbuffer_init(&sbuf);
            msgpack_packer pk;
            msgpack_packer_init(&pk, &sbuf, msgpack_sbuffer_write);
            
            msgpack_pack_map(&pk, 3);
            msgpack_pack_str(&pk, 4);
            msgpack_pack_str_body(&pk, "user", 4);
            msgpack_pack_str(&pk, strlen(user));
            msgpack_pack_str_body(&pk, user, strlen(user));
            msgpack_pack_str(&pk, 9);
            msgpack_pack_str_body(&pk, "timestamp", 9);
            msgpack_pack_double(&pk, get_timestamp());
            msgpack_pack_str(&pk, 5);
            msgpack_pack_str_body(&pk, "clock", 5);
            msgpack_pack_int(&pk, relogio_tick(&c.relogio));
            
            enviar_requisicao(&c, "login", &sbuf);
            strcpy(c.nome_usuario, user);
            inscrever_topico(&c, user);
            
            msgpack_sbuffer_destroy(&sbuf);
        }
        else if (strcmp(opcao, "2") == 0) {
            // Listar usuários
            printf("\n------ Listar usuários ------\n");
            
            msgpack_sbuffer sbuf;
            msgpack_sbuffer_init(&sbuf);
            msgpack_packer pk;
            msgpack_packer_init(&pk, &sbuf, msgpack_sbuffer_write);
            
            msgpack_pack_map(&pk, 2);
            msgpack_pack_str(&pk, 9);
            msgpack_pack_str_body(&pk, "timestamp", 9);
            msgpack_pack_double(&pk, get_timestamp());
            msgpack_pack_str(&pk, 5);
            msgpack_pack_str_body(&pk, "clock", 5);
            msgpack_pack_int(&pk, relogio_tick(&c.relogio));
            
            enviar_requisicao(&c, "listar", &sbuf);
            msgpack_sbuffer_destroy(&sbuf);
        }
        else if (strcmp(opcao, "3") == 0) {
            // Cadastrar canal
            printf("\n------ Cadastrar canal ------\n");
            printf("Entre com o nome do canal: ");
            fflush(stdout);
            
            char canal[MAX_USERNAME];
            fgets(canal, sizeof(canal), stdin);
            canal[strcspn(canal, "\n")] = 0;
            
            msgpack_sbuffer sbuf;
            msgpack_sbuffer_init(&sbuf);
            msgpack_packer pk;
            msgpack_packer_init(&pk, &sbuf, msgpack_sbuffer_write);
            
            msgpack_pack_map(&pk, 3);
            msgpack_pack_str(&pk, 5);
            msgpack_pack_str_body(&pk, "canal", 5);
            msgpack_pack_str(&pk, strlen(canal));
            msgpack_pack_str_body(&pk, canal, strlen(canal));
            msgpack_pack_str(&pk, 9);
            msgpack_pack_str_body(&pk, "timestamp", 9);
            msgpack_pack_double(&pk, get_timestamp());
            msgpack_pack_str(&pk, 5);
            msgpack_pack_str_body(&pk, "clock", 5);
            msgpack_pack_int(&pk, relogio_tick(&c.relogio));
            
            enviar_requisicao(&c, "cadastrarCanal", &sbuf);
            msgpack_sbuffer_destroy(&sbuf);
        }
        else if (strcmp(opcao, "4") == 0) {
            // Listar canais
            printf("\n------ Listar canais ------\n");
            
            msgpack_sbuffer sbuf;
            msgpack_sbuffer_init(&sbuf);
            msgpack_packer pk;
            msgpack_packer_init(&pk, &sbuf, msgpack_sbuffer_write);
            
            msgpack_pack_map(&pk, 2);
            msgpack_pack_str(&pk, 9);
            msgpack_pack_str_body(&pk, "timestamp", 9);
            msgpack_pack_double(&pk, get_timestamp());
            msgpack_pack_str(&pk, 5);
            msgpack_pack_str_body(&pk, "clock", 5);
            msgpack_pack_int(&pk, relogio_tick(&c.relogio));
            
            enviar_requisicao(&c, "listarCanal", &sbuf);
            msgpack_sbuffer_destroy(&sbuf);
        }
        else if (strcmp(opcao, "5") == 0) {
            // Inscrever em canal
            printf("\n------ Inscrever em canal ------\n");
            printf("Entre com o nome do canal: ");
            fflush(stdout);
            
            char canal[MAX_USERNAME];
            fgets(canal, sizeof(canal), stdin);
            canal[strcspn(canal, "\n")] = 0;
            
            inscrever_topico(&c, canal);
            strcpy(c.canais_inscritos[c.num_canais++], canal);
            printf("Inscrito no canal '%s' com sucesso!\n", canal);
        }
        else if (strcmp(opcao, "6") == 0) {
            // Publicar mensagem em canal
            printf("\n------ Publicar mensagem em canal ------\n");
            
            if (strlen(c.nome_usuario) == 0) {
                printf("Você precisa fazer login primeiro!\n");
                continue;
            }
            
            printf("Entre com o nome do canal: ");
            fflush(stdout);
            char canal[MAX_USERNAME];
            fgets(canal, sizeof(canal), stdin);
            canal[strcspn(canal, "\n")] = 0;
            
            printf("Entre com a mensagem: ");
            fflush(stdout);
            char mensagem[1024];
            fgets(mensagem, sizeof(mensagem), stdin);
            mensagem[strcspn(mensagem, "\n")] = 0;
            
            msgpack_sbuffer sbuf;
            msgpack_sbuffer_init(&sbuf);
            msgpack_packer pk;
            msgpack_packer_init(&pk, &sbuf, msgpack_sbuffer_write);
            
            msgpack_pack_map(&pk, 5);
            msgpack_pack_str(&pk, 4);
            msgpack_pack_str_body(&pk, "user", 4);
            msgpack_pack_str(&pk, strlen(c.nome_usuario));
            msgpack_pack_str_body(&pk, c.nome_usuario, strlen(c.nome_usuario));
            msgpack_pack_str(&pk, 7);
            msgpack_pack_str_body(&pk, "channel", 7);
            msgpack_pack_str(&pk, strlen(canal));
            msgpack_pack_str_body(&pk, canal, strlen(canal));
            msgpack_pack_str(&pk, 7);
            msgpack_pack_str_body(&pk, "message", 7);
            msgpack_pack_str(&pk, strlen(mensagem));
            msgpack_pack_str_body(&pk, mensagem, strlen(mensagem));
            msgpack_pack_str(&pk, 9);
            msgpack_pack_str_body(&pk, "timestamp", 9);
            msgpack_pack_double(&pk, get_timestamp());
            msgpack_pack_str(&pk, 5);
            msgpack_pack_str_body(&pk, "clock", 5);
            msgpack_pack_int(&pk, relogio_tick(&c.relogio));
            
            enviar_requisicao(&c, "publish", &sbuf);
            msgpack_sbuffer_destroy(&sbuf);
        }
        else if (strcmp(opcao, "7") == 0) {
            // Enviar mensagem privada
            printf("\n------ Enviar mensagem privada ------\n");
            
            if (strlen(c.nome_usuario) == 0) {
                printf("Você precisa fazer login primeiro!\n");
                continue;
            }
            
            printf("Entre com o nome do receptor: ");
            fflush(stdout);
            char receptor[MAX_USERNAME];
            fgets(receptor, sizeof(receptor), stdin);
            receptor[strcspn(receptor, "\n")] = 0;
            
            printf("Entre com a mensagem: ");
            fflush(stdout);
            char mensagem[1024];
            fgets(mensagem, sizeof(mensagem), stdin);
            mensagem[strcspn(mensagem, "\n")] = 0;
            
            msgpack_sbuffer sbuf;
            msgpack_sbuffer_init(&sbuf);
            msgpack_packer pk;
            msgpack_packer_init(&pk, &sbuf, msgpack_sbuffer_write);
            
            msgpack_pack_map(&pk, 5);
            msgpack_pack_str(&pk, 3);
            msgpack_pack_str_body(&pk, "src", 3);
            msgpack_pack_str(&pk, strlen(c.nome_usuario));
            msgpack_pack_str_body(&pk, c.nome_usuario, strlen(c.nome_usuario));
            msgpack_pack_str(&pk, 3);
            msgpack_pack_str_body(&pk, "dst", 3);
            msgpack_pack_str(&pk, strlen(receptor));
            msgpack_pack_str_body(&pk, receptor, strlen(receptor));
            msgpack_pack_str(&pk, 7);
            msgpack_pack_str_body(&pk, "message", 7);
            msgpack_pack_str(&pk, strlen(mensagem));
            msgpack_pack_str_body(&pk, mensagem, strlen(mensagem));
            msgpack_pack_str(&pk, 9);
            msgpack_pack_str_body(&pk, "timestamp", 9);
            msgpack_pack_double(&pk, get_timestamp());
            msgpack_pack_str(&pk, 5);
            msgpack_pack_str_body(&pk, "clock", 5);
            msgpack_pack_int(&pk, relogio_tick(&c.relogio));
            
            enviar_requisicao(&c, "message", &sbuf);
            msgpack_sbuffer_destroy(&sbuf);
        }
        else {
            printf("Opção inválida! Tente novamente.\n");
        }
    }
    
    pthread_cancel(receiver_thread);
    pthread_join(receiver_thread, NULL);
    
    zmq_close(c.socket);
    zmq_close(c.sub_socket);
    zmq_ctx_destroy(c.context);
    
    printf("Cliente encerrado.\n");
    
    return 0;
}
