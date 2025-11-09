#include <zmq.h>
#include <msgpack.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef struct {
    int clock;
} RelogioLogico;

void relogio_init(RelogioLogico *r) {
    r->clock = 0;
}

int relogio_tick(RelogioLogico *r) {
    r->clock++;
    return r->clock;
}

void relogio_update(RelogioLogico *r, int clock_recebido) {
    if (clock_recebido > r->clock) {
        r->clock = clock_recebido;
    }
}

int relogio_get(RelogioLogico *r) {
    return r->clock;
}

void enviar_requisicao(void *socket, const char *service, RelogioLogico *relogio,
                       const char *user, const char *channel, const char *message,
                       const char *src, const char *dst) {
    msgpack_sbuffer sbuf;
    msgpack_packer pk;
    
    msgpack_sbuffer_init(&sbuf);
    msgpack_packer_init(&pk, &sbuf, msgpack_sbuffer_write);
    
    msgpack_pack_map(&pk, 2);
    
    msgpack_pack_str(&pk, 7);
    msgpack_pack_str_body(&pk, "service", 7);
    msgpack_pack_str(&pk, strlen(service));
    msgpack_pack_str_body(&pk, service, strlen(service));
    
    msgpack_pack_str(&pk, 4);
    msgpack_pack_str_body(&pk, "data", 4);
    
    int data_fields = 2;
    if (user) data_fields++;
    if (channel) data_fields++;
    if (message) data_fields++;
    if (src) data_fields++;
    if (dst) data_fields++;
    
    msgpack_pack_map(&pk, data_fields);
    
    if (user) {
        msgpack_pack_str(&pk, 4);
        msgpack_pack_str_body(&pk, "user", 4);
        msgpack_pack_str(&pk, strlen(user));
        msgpack_pack_str_body(&pk, user, strlen(user));
    }
    
    if (channel) {
        msgpack_pack_str(&pk, 7);
        msgpack_pack_str_body(&pk, "channel", 7);
        msgpack_pack_str(&pk, strlen(channel));
        msgpack_pack_str_body(&pk, channel, strlen(channel));
    }
    
    if (message) {
        msgpack_pack_str(&pk, 7);
        msgpack_pack_str_body(&pk, "message", 7);
        msgpack_pack_str(&pk, strlen(message));
        msgpack_pack_str_body(&pk, message, strlen(message));
    }
    
    if (src) {
        msgpack_pack_str(&pk, 3);
        msgpack_pack_str_body(&pk, "src", 3);
        msgpack_pack_str(&pk, strlen(src));
        msgpack_pack_str_body(&pk, src, strlen(src));
    }
    
    if (dst) {
        msgpack_pack_str(&pk, 3);
        msgpack_pack_str_body(&pk, "dst", 3);
        msgpack_pack_str(&pk, strlen(dst));
        msgpack_pack_str_body(&pk, dst, strlen(dst));
    }
    
    msgpack_pack_str(&pk, 9);
    msgpack_pack_str_body(&pk, "timestamp", 9);
    msgpack_pack_double(&pk, (double)time(NULL));
    
    msgpack_pack_str(&pk, 5);
    msgpack_pack_str_body(&pk, "clock", 5);
    msgpack_pack_int(&pk, relogio_tick(relogio));
    
    zmq_send(socket, sbuf.data, sbuf.size, 0);
    
    char buffer[4096];
    int size = zmq_recv(socket, buffer, sizeof(buffer), 0);
    
    if (size > 0) {
        msgpack_unpacked result;
        msgpack_unpacked_init(&result);
        
        if (msgpack_unpack_next(&result, buffer, size, NULL) == MSGPACK_UNPACK_SUCCESS) {
            msgpack_object obj = result.data;
            
            if (obj.type == MSGPACK_OBJECT_MAP) {
                for (int i = 0; i < obj.via.map.size; i++) {
                    msgpack_object_kv kv = obj.via.map.ptr[i];
                    if (kv.key.type == MSGPACK_OBJECT_STR) {
                        if (strncmp(kv.key.via.str.ptr, "data", 4) == 0 && kv.val.type == MSGPACK_OBJECT_MAP) {
                            for (int j = 0; j < kv.val.via.map.size; j++) {
                                msgpack_object_kv data_kv = kv.val.via.map.ptr[j];
                                if (data_kv.key.type == MSGPACK_OBJECT_STR) {
                                    if (strncmp(data_kv.key.via.str.ptr, "clock", 5) == 0) {
                                        if (data_kv.val.type == MSGPACK_OBJECT_POSITIVE_INTEGER) {
                                            relogio_update(relogio, data_kv.val.via.u64);
                                        }
                                    } else if (strncmp(data_kv.key.via.str.ptr, "status", 6) == 0) {
                                        if (data_kv.val.type == MSGPACK_OBJECT_STR) {
                                            if (strncmp(data_kv.val.via.str.ptr, "erro", 4) == 0) {
                                                printf("Erro\n");
                                            } else {
                                                if (strcmp(service, "login") == 0) printf("Login OK\n");
                                                else if (strcmp(service, "channel") == 0) printf("Canal cadastrado\n");
                                                else if (strcmp(service, "publish") == 0) printf("Publicado\n");
                                                else if (strcmp(service, "message") == 0) printf("Enviado\n");
                                            }
                                        }
                                    } else if (strncmp(data_kv.key.via.str.ptr, "users", 5) == 0) {
                                        if (data_kv.val.type == MSGPACK_OBJECT_ARRAY) {
                                            printf("Usuarios (%d):\n", data_kv.val.via.array.size);
                                            for (int k = 0; k < data_kv.val.via.array.size; k++) {
                                                msgpack_object item = data_kv.val.via.array.ptr[k];
                                                if (item.type == MSGPACK_OBJECT_STR) {
                                                    printf("  %.*s\n", (int)item.via.str.size, item.via.str.ptr);
                                                }
                                            }
                                        }
                                    } else if (strncmp(data_kv.key.via.str.ptr, "channels", 8) == 0) {
                                        if (data_kv.val.type == MSGPACK_OBJECT_ARRAY) {
                                            printf("Canais (%d):\n", data_kv.val.via.array.size);
                                            for (int k = 0; k < data_kv.val.via.array.size; k++) {
                                                msgpack_object item = data_kv.val.via.array.ptr[k];
                                                if (item.type == MSGPACK_OBJECT_STR) {
                                                    printf("  %.*s\n", (int)item.via.str.size, item.via.str.ptr);
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        msgpack_unpacked_destroy(&result);
    }
    
    msgpack_sbuffer_destroy(&sbuf);
    fflush(stdout);
}

int main() {
    void *context = zmq_ctx_new();
    void *socket = zmq_socket(context, ZMQ_REQ);
    
    int timeout = 10000;
    zmq_setsockopt(socket, ZMQ_RCVTIMEO, &timeout, sizeof(timeout));
    zmq_setsockopt(socket, ZMQ_SNDTIMEO, &timeout, sizeof(timeout));
    
    zmq_connect(socket, "tcp://broker:5555");
    
    RelogioLogico relogio;
    relogio_init(&relogio);
    
    printf("BulletInBoard\n");
    printf("[1] Login\n");
    printf("[2] Listar usuarios\n");
    printf("[3] Cadastrar canal\n");
    printf("[4] Listar canais\n");
    printf("[5] Publicar em canal\n");
    printf("[6] Mensagem privada\n");
    printf("[0] Sair\n");
    fflush(stdout);
    
    char opcao[10];
    char buffer[256];
    
    while (1) {
        printf("\nOpcao: ");
        fflush(stdout);
        
        if (fgets(opcao, sizeof(opcao), stdin) == NULL) break;
        opcao[strcspn(opcao, "\n")] = 0;
        
        if (strcmp(opcao, "0") == 0) {
            break;
        } else if (strcmp(opcao, "1") == 0) {
            printf("Entre com seu usuario: ");
            fflush(stdout);
            fgets(buffer, sizeof(buffer), stdin);
            buffer[strcspn(buffer, "\n")] = 0;
            enviar_requisicao(socket, "login", &relogio, buffer, NULL, NULL, NULL, NULL);
            
        } else if (strcmp(opcao, "2") == 0) {
            enviar_requisicao(socket, "users", &relogio, NULL, NULL, NULL, NULL, NULL);
            
        } else if (strcmp(opcao, "3") == 0) {
            printf("Entre com o canal: ");
            fflush(stdout);
            fgets(buffer, sizeof(buffer), stdin);
            buffer[strcspn(buffer, "\n")] = 0;
            enviar_requisicao(socket, "channel", &relogio, NULL, buffer, NULL, NULL, NULL);
            
        } else if (strcmp(opcao, "4") == 0) {
            enviar_requisicao(socket, "channels", &relogio, NULL, NULL, NULL, NULL, NULL);
            
        } else if (strcmp(opcao, "5") == 0) {
            char usuario[256], canal[256], mensagem[256];
            
            printf("Entre com seu usuario: ");
            fflush(stdout);
            fgets(usuario, sizeof(usuario), stdin);
            usuario[strcspn(usuario, "\n")] = 0;
            
            printf("Entre com o canal: ");
            fflush(stdout);
            fgets(canal, sizeof(canal), stdin);
            canal[strcspn(canal, "\n")] = 0;
            
            printf("Entre com a mensagem: ");
            fflush(stdout);
            fgets(mensagem, sizeof(mensagem), stdin);
            mensagem[strcspn(mensagem, "\n")] = 0;
            
            enviar_requisicao(socket, "publish", &relogio, usuario, canal, mensagem, NULL, NULL);
            
        } else if (strcmp(opcao, "6") == 0) {
            char src[256], dst[256], mensagem[256];
            
            printf("Entre com seu usuario (de): ");
            fflush(stdout);
            fgets(src, sizeof(src), stdin);
            src[strcspn(src, "\n")] = 0;
            
            printf("Entre com o destinatario (para): ");
            fflush(stdout);
            fgets(dst, sizeof(dst), stdin);
            dst[strcspn(dst, "\n")] = 0;
            
            printf("Entre com a mensagem: ");
            fflush(stdout);
            fgets(mensagem, sizeof(mensagem), stdin);
            mensagem[strcspn(mensagem, "\n")] = 0;
            
            enviar_requisicao(socket, "message", &relogio, NULL, NULL, mensagem, src, dst);
            
        } else {
            printf("Opcao invalida\n");
            fflush(stdout);
        }
    }
    
    zmq_close(socket);
    zmq_ctx_destroy(context);
    
    return 0;
}

