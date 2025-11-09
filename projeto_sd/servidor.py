import threading
import zmq
import msgpack
import time
import json
import os

# Lista de endereços dos outros servidores (exemplo, ajuste conforme sua rede)
OUTROS_SERVIDORES = [
    "tcp://servidor2:5556",
    "tcp://servidor3:5556"
]

# Função para salvar mensagens no arquivo de log
def salvar_log(mensagem):
    try:
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(f"{mensagem}\n")
    except Exception as e:
        print(f"Erro ao salvar no log: {e}", flush=True)

# Função para carregar dados persistidos
def carregar_dados():
    usuarios = []
    canais = []
    
    # Carregar usuários
    if os.path.exists("usuarios.json"):
        try:
            with open("usuarios.json", "r", encoding="utf-8") as f:
                usuarios = json.load(f)
            print(f"[S] - {len(usuarios)} usuários carregados do disco", flush=True)
        except Exception as e:
            print(f"[S] - Erro ao carregar usuários: {e}", flush=True)
    
    # Carregar canais
    if os.path.exists("canais.json"):
        try:
            with open("canais.json", "r", encoding="utf-8") as f:
                canais = json.load(f)
            print(f"[S] - {len(canais)} canais carregados do disco", flush=True)
        except Exception as e:
            print(f"[S] - Erro ao carregar canais: {e}", flush=True)
    
    return usuarios, canais

# Função para salvar usuários em disco
def salvar_usuarios(usuarios):
    try:
        with open("usuarios.json", "w", encoding="utf-8") as f:
            json.dump(usuarios, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[S] - Erro ao salvar usuários: {e}", flush=True)

# Função para salvar canais em disco
def salvar_canais(canais):
    try:
        with open("canais.json", "w", encoding="utf-8") as f:
            json.dump(canais, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[S] - Erro ao salvar canais: {e}", flush=True)

# Função para salvar publicações em disco
def salvar_publicacao(publicacao):
    try:
        publicacoes = []
        if os.path.exists("publicacoes.json"):
            with open("publicacoes.json", "r", encoding="utf-8") as f:
                publicacoes = json.load(f)
        
        publicacoes.append(publicacao)
        
        with open("publicacoes.json", "w", encoding="utf-8") as f:
            json.dump(publicacoes, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[S] - Erro ao salvar publicação: {e}", flush=True)

# Função para salvar mensagens privadas em disco
def salvar_mensagem_privada(mensagem):
    try:
        mensagens = []
        if os.path.exists("mensagens.json"):
            with open("mensagens.json", "r", encoding="utf-8") as f:
                mensagens = json.load(f)
        
        mensagens.append(mensagem)
        
        with open("mensagens.json", "w", encoding="utf-8") as f:
            json.dump(mensagens, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[S] - Erro ao salvar mensagem: {e}", flush=True)

# Função para replicar mensagem para outros servidores
def replicar_para_outros_servidores(mensagem, lista_enderecos):
    def enviar(endereco):
        try:
            ctx = zmq.Context()
            sock = ctx.socket(zmq.REQ)
            sock.connect(endereco)
            sock.send(msgpack.packb(mensagem))
            sock.close()
            ctx.term()
        except Exception as e:
            print(f"Erro ao replicar para {endereco}: {e}")
    for endereco in lista_enderecos:
        threading.Thread(target=enviar, args=(endereco,)).start()

# Classe do relógio lógico
class RelogioLogico:
    def __init__(self):
        self.clock = 0
    def tick(self):
        self.clock += 1
        return self.clock
    def update(self, clock_recebido):
        self.clock = max(self.clock, clock_recebido)
        return self.clock
    def get(self):
        return self.clock

relogio = RelogioLogico()

# Variáveis para sincronização e eleição
import socket as sock
NOME_SERVIDOR = sock.gethostname()  # Nome único do servidor
rank_servidor = None
coordenador_atual = None
contador_mensagens = 0
ajuste_relogio = 0.0  # Ajuste do relógio físico (Berkeley)

# Socket para comunicação com servidor de referência
ref_context = zmq.Context()
ref_socket = ref_context.socket(zmq.REQ)
ref_socket.connect("tcp://referencia:5560")

# Socket PUB para eleições (tópico "servers")
election_pub_socket = ref_context.socket(zmq.PUB)
election_pub_socket.connect("tcp://proxy:5557")

# Socket SUB para eleições
election_sub_socket = ref_context.socket(zmq.SUB)
election_sub_socket.connect("tcp://proxy:5558")
election_sub_socket.setsockopt_string(zmq.SUBSCRIBE, "servers")

def registrar_no_servidor_referencia():
    """Registra o servidor e obtém seu rank"""
    global rank_servidor
    try:
        # Configurar timeout
        ref_socket.setsockopt(zmq.RCVTIMEO, 5000)
        ref_socket.setsockopt(zmq.SNDTIMEO, 5000)
        
        request = {
            "service": "rank",
            "data": {
                "user": NOME_SERVIDOR,
                "timestamp": time.time(),
                "clock": relogio.tick()
            }
        }
        print(f"[S] Tentando registrar servidor {NOME_SERVIDOR}...", flush=True)
        ref_socket.send(msgpack.packb(request))
        reply_data = ref_socket.recv()
        reply = msgpack.unpackb(reply_data, raw=False)
        
        if "data" in reply and "clock" in reply["data"]:
            relogio.update(reply["data"]["clock"])
        
        rank_servidor = reply.get("data", {}).get("rank")
        print(f"[S] ✅ Servidor {NOME_SERVIDOR} registrado com rank {rank_servidor}", flush=True)
    except zmq.Again:
        print(f"[S] ⚠️ Timeout ao registrar. Servidor de referência não disponível.", flush=True)
        print(f"[S] Continuando sem registro (modo standalone)...", flush=True)
        rank_servidor = None
    except Exception as e:
        print(f"[S] ❌ Erro ao registrar no servidor de referência: {e}", flush=True)
        print(f"[S] Continuando sem registro (modo standalone)...", flush=True)
        rank_servidor = None

def enviar_heartbeat():
    """Envia heartbeat periodicamente ao servidor de referência"""
    while True:
        time.sleep(10)  # Enviar a cada 10 segundos
        try:
            ctx = zmq.Context()
            sock = ctx.socket(zmq.REQ)
            sock.connect("tcp://referencia:5560")
            
            request = {
                "service": "heartbeat",
                "data": {
                    "user": NOME_SERVIDOR,
                    "timestamp": time.time(),
                    "clock": relogio.tick()
                }
            }
            sock.send(msgpack.packb(request))
            reply_data = sock.recv()
            reply = msgpack.unpackb(reply_data, raw=False)
            
            if "data" in reply and "clock" in reply["data"]:
                relogio.update(reply["data"]["clock"])
            
            print(f"[S] Heartbeat enviado por {NOME_SERVIDOR}", flush=True)
            
            sock.close()
            ctx.term()
        except Exception as e:
            print(f"[S] Erro ao enviar heartbeat: {e}", flush=True)

def obter_lista_servidores():
    """Obtém a lista de servidores do servidor de referência"""
    try:
        ctx = zmq.Context()
        sock = ctx.socket(zmq.REQ)
        sock.connect("tcp://referencia:5560")
        
        request = {
            "service": "list",
            "data": {
                "timestamp": time.time(),
                "clock": relogio.tick()
            }
        }
        sock.send(msgpack.packb(request))
        reply_data = sock.recv()
        reply = msgpack.unpackb(reply_data, raw=False)
        
        if "data" in reply and "clock" in reply["data"]:
            relogio.update(reply["data"]["clock"])
        
        lista = reply.get("data", {}).get("list", [])
        
        sock.close()
        ctx.term()
        
        return lista
    except Exception as e:
        print(f"[S] Erro ao obter lista de servidores: {e}", flush=True)
        return []

def sincronizar_relogio():
    """Sincroniza o relógio com o coordenador usando algoritmo de Berkeley"""
    global ajuste_relogio, contador_mensagens
    
    while True:
        time.sleep(30)  # Sincronizar a cada 30 segundos
        
        if coordenador_atual and coordenador_atual != NOME_SERVIDOR:
            try:
                # Solicitar horário do coordenador
                ctx = zmq.Context()
                sock = ctx.socket(zmq.REQ)
                
                # Encontrar endereço do coordenador
                lista_servidores = obter_lista_servidores()
                endereco_coord = None
                
                for servidor in lista_servidores:
                    if servidor.get("name") == coordenador_atual:
                        # Usar nome do container
                        endereco_coord = f"tcp://{coordenador_atual}:5561"
                        break
                
                if not endereco_coord:
                    print(f"[S] Coordenador {coordenador_atual} não encontrado", flush=True)
                    continue
                
                sock.connect(endereco_coord)
                sock.setsockopt(zmq.RCVTIMEO, 5000)  # Timeout de 5 segundos
                
                t1 = time.time()
                request = {
                    "service": "clock",
                    "data": {
                        "timestamp": t1,
                        "clock": relogio.tick()
                    }
                }
                sock.send(msgpack.packb(request))
                reply_data = sock.recv()
                t2 = time.time()
                
                reply = msgpack.unpackb(reply_data, raw=False)
                
                if "data" in reply and "clock" in reply["data"]:
                    relogio.update(reply["data"]["clock"])
                
                tempo_coord = reply.get("data", {}).get("time")
                
                if tempo_coord:
                    # Calcular ajuste (Berkeley simplificado)
                    rtt = t2 - t1
                    tempo_estimado_coord = tempo_coord + (rtt / 2)
                    ajuste_relogio = tempo_estimado_coord - time.time()
                    
                    print(f"[S] Relógio sincronizado. Ajuste: {ajuste_relogio:.6f}s", flush=True)
                
                sock.close()
                ctx.term()
                
            except zmq.Again:
                print(f"[S] Timeout ao sincronizar com coordenador {coordenador_atual}", flush=True)
                # Iniciar eleição
                iniciar_eleicao()
            except Exception as e:
                print(f"[S] Erro ao sincronizar relógio: {e}", flush=True)

def iniciar_eleicao():
    """Inicia o processo de eleição (Bully Algorithm)"""
    global coordenador_atual
    
    print(f"[S] Iniciando eleição...", flush=True)
    
    lista_servidores = obter_lista_servidores()
    meu_rank = rank_servidor
    
    # Enviar election para servidores com rank maior
    servidores_maiores = [s for s in lista_servidores if s.get("rank", 0) > meu_rank]
    
    recebeu_ok = False
    
    for servidor in servidores_maiores:
        try:
            ctx = zmq.Context()
            sock = ctx.socket(zmq.REQ)
            sock.connect(f"tcp://{servidor['name']}:5561")
            sock.setsockopt(zmq.RCVTIMEO, 2000)
            
            request = {
                "service": "election",
                "data": {
                    "timestamp": time.time(),
                    "clock": relogio.tick()
                }
            }
            sock.send(msgpack.packb(request))
            reply_data = sock.recv()
            reply = msgpack.unpackb(reply_data, raw=False)
            
            if reply.get("data", {}).get("election") == "OK":
                recebeu_ok = True
            
            sock.close()
            ctx.term()
        except:
            pass
    
    # Se nenhum servidor maior respondeu, este servidor é o coordenador
    if not recebeu_ok:
        coordenador_atual = NOME_SERVIDOR
        print(f"[S] {NOME_SERVIDOR} eleito como coordenador!", flush=True)
        
        # Publicar no tópico "servers"
        pub_msg = {
            "type": "election",
            "topic": "servers",
            "service": "election",
            "data": {
                "coordinator": NOME_SERVIDOR,
                "timestamp": time.time(),
                "clock": relogio.tick()
            }
        }
        election_pub_socket.send_string("servers", zmq.SNDMORE)
        election_pub_socket.send(msgpack.packb(pub_msg))

def monitor_eleicoes():
    """Monitora publicações de eleição no tópico servers"""
    global coordenador_atual
    
    while True:
        try:
            topic = election_sub_socket.recv_string()
            msg_data = election_sub_socket.recv()
            msg = msgpack.unpackb(msg_data, raw=False)
            
            if msg.get("type") == "election":
                novo_coord = msg.get("data", {}).get("coordinator")
                if novo_coord:
                    coordenador_atual = novo_coord
                    print(f"[S] Novo coordenador: {coordenador_atual}", flush=True)
                    
                    if "clock" in msg.get("data", {}):
                        relogio.update(msg["data"]["clock"])
        except Exception as e:
            print(f"[S] Erro ao monitorar eleições: {e}", flush=True)

# Registrar no servidor de referência
print(f"[S] Iniciando servidor {NOME_SERVIDOR}...", flush=True)
registrar_no_servidor_referencia()

# Iniciar threads de manutenção apenas se registrado
if rank_servidor is not None:
    print(f"[S] Iniciando threads de manutenção...", flush=True)
    threading.Thread(target=enviar_heartbeat, daemon=True).start()
    threading.Thread(target=sincronizar_relogio, daemon=True).start()
    threading.Thread(target=monitor_eleicoes, daemon=True).start()
    
    # Se for o primeiro servidor (rank 1), se elege como coordenador
    if rank_servidor == 1:
        coordenador_atual = NOME_SERVIDOR
        print(f"[S] {NOME_SERVIDOR} é o coordenador inicial", flush=True)
else:
    print(f"[S] ⚠️ Servidor operando em modo standalone (sem sincronização)", flush=True)

PUB_PORT = 5559  # Porta para publisher

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.connect("tcp://broker:5556")

# Socket para responder requisições de sincronização e eleição
sync_socket = context.socket(zmq.REP)
sync_socket.bind("tcp://*:5561")

# Criar socket PUB uma única vez e reutilizar
pub_socket = context.socket(zmq.PUB)
pub_socket.bind(f"tcp://*:{PUB_PORT}")
print(f"[S] - Socket PUB criado e bind na porta {PUB_PORT}", flush=True)

# Carregar dados persistidos
usuarios, canais = carregar_dados()

# Configurar poller para gerenciar múltiplos sockets
poller = zmq.Poller()
poller.register(socket, zmq.POLLIN)       # Socket principal (clientes)
poller.register(sync_socket, zmq.POLLIN)  # Socket de sincronização

print(f"[S] ✅ Servidor {NOME_SERVIDOR} pronto para receber mensagens!", flush=True)
print(f"[S] Aguardando requisições...", flush=True)

while True:
    try:
        socks = dict(poller.poll())
        
        # Mensagens de clientes (através do broker)
        if socket in socks:
            # Recebe mensagem serializada com MessagePack
            print(f"[S] 📨 Mensagem recebida do cliente", flush=True)
            request_data = socket.recv()
            request = msgpack.unpackb(request_data, raw=False)
            service = request.get("service", request.get("opcao"))  # Suporta ambos por compatibilidade temporária
            data = request.get("data", request.get("dados"))  # Suporta ambos por compatibilidade temporária
            
            print(f"[S] 🔍 Service: {service} | User: {data.get('user', 'N/A')}", flush=True)
            
            # Salva a mensagem recebida no log
            salvar_log(f"[{time.time()}] Service: {service} | Data: {data}")
            
            # Atualiza relógio lógico ao receber
            if data and "clock" in data:
                relogio.update(data["clock"])
            
            # Incrementar contador de mensagens
            contador_mensagens += 1
            
            # Processar requisição do cliente
            match service:
            # FEITO
            case "login":
                user = data.get("user")
                timestamp = data.get("timestamp")
                
                # Verificar se o usuário já existe
                usuario_existe = any(u.get("user") == user for u in usuarios)
                
                if usuario_existe:
                    reply = {
                        "service": "login",
                        "data": {
                            "status": "erro",
                            "timestamp": time.time(),
                            "description": "Usuário já cadastrado",
                            "clock": relogio.tick()
                        }
                    }
                    print(f"[S] - Tentativa de login com usuário existente: {user}", flush=True)
                else:
                    # Adicionar novo usuário
                    usuarios.append({
                        "user": user,
                        "timestamp": timestamp
                    })
                    salvar_usuarios(usuarios)  # Persistir em disco
                    
                    reply = {
                        "service": "login",
                        "data": {
                            "status": "sucesso",
                            "timestamp": time.time(),
                            "clock": relogio.tick()
                        }
                    }
                    print(f"[S] - Login do {user} feito!", flush=True)
                    # Replicar para outros servidores
                    replicar_para_outros_servidores({"service": "login", "data": data}, OUTROS_SERVIDORES)

            # FEITO
            case "users" | "listar":  # Suporta ambos por compatibilidade
                # Extrair apenas os nomes dos usuários
                lista_usuarios = [u.get("user") for u in usuarios]
                
                reply = {
                    "service": "users",
                    "data": {
                        "timestamp": time.time(),
                        "users": lista_usuarios,
                        "clock": relogio.tick()
                    }
                }
                print(f"[S] - Usuários listados: {lista_usuarios}", flush=True)
            
            # FEITO
            case "channel" | "cadastrarCanal":  # Suporta ambos por compatibilidade
                channel = data.get("channel", data.get("canal"))
                timestamp = data.get("timestamp")
                
                # Verificar se o canal já existe
                canal_existe = any(c.get("channel") == channel for c in canais)
                
                if canal_existe:
                    reply = {
                        "service": "channel",
                        "data": {
                            "status": "erro",
                            "timestamp": time.time(),
                            "description": "Canal já cadastrado",
                            "clock": relogio.tick()
                        }
                    }
                    print(f"[S] - Tentativa de criar canal existente: {channel}", flush=True)
                else:
                    # Adicionar novo canal
                    canais.append({
                        "channel": channel,
                        "timestamp": timestamp
                    })
                    salvar_canais(canais)  # Persistir em disco
                    
                    reply = {
                        "service": "channel",
                        "data": {
                            "status": "sucesso",
                            "timestamp": time.time(),
                            "clock": relogio.tick()
                        }
                    }
                    print(f"[S] - Cadastro do canal {channel} feito!", flush=True)
                    # Replicar para outros servidores
                    replicar_para_outros_servidores({"service": "channel", "data": data}, OUTROS_SERVIDORES)

            # FEITO
            case "channels" | "listarCanal":  # Suporta ambos por compatibilidade
                # Extrair apenas os nomes dos canais
                lista_canais = [c.get("channel") for c in canais]
                
                reply = {
                    "service": "channels",
                    "data": {
                        "timestamp": time.time(),
                        "channels": lista_canais,
                        "clock": relogio.tick()
                    }
                }
                print(f"[S] - Canais listados: {lista_canais}", flush=True)

            # FEITO
            case "publish":
                user = data.get("user")
                channel = data.get("channel")
                message = data.get("message")
                timestamp = data.get("timestamp")
                
                # Verificar se o canal existe
                canal_existe = any(c.get("channel") == channel for c in canais)
                
                if not canal_existe:
                    reply = {
                        "service": "publish",
                        "data": {
                            "status": "erro",
                            "message": f"Canal '{channel}' não existe",
                            "timestamp": time.time(),
                            "clock": relogio.tick()
                        }
                    }
                    print(f"[S] - Tentativa de publicar em canal inexistente: {channel}", flush=True)
                else:
                    try:
                        pub_msg = {
                            "type": "channel",
                            "topic": channel,  # Tópico é o nome do canal
                            "user": user,
                            "channel": channel,
                            "message": message,
                            "timestamp": timestamp,
                            "clock": relogio.get()
                        }
                        # Usar o socket PUB já criado
                        pub_socket.send(msgpack.packb(pub_msg))
                        
                        # Persistir a publicação
                        salvar_publicacao({
                            "user": user,
                            "channel": channel,
                            "message": message,
                            "timestamp": timestamp
                        })
                        
                        reply = {
                            "service": "publish",
                            "data": {
                                "status": "OK",
                                "timestamp": time.time(),
                                "clock": relogio.tick()
                            }
                        }
                        print(f"[S] - Mensagem publicada no canal {channel}: {message}", flush=True)
                        # Replicar para outros servidores
                        replicar_para_outros_servidores({"service": "publish", "data": data}, OUTROS_SERVIDORES)
                    except Exception as e:
                        reply = {
                            "service": "publish",
                            "data": {
                                "status": "erro",
                                "message": f"Erro ao publicar: {str(e)}",
                                "timestamp": time.time(),
                                "clock": relogio.tick()
                            }
                        }
                        print(f"[S] - Falha ao publicar mensagem: {e}", flush=True)

            # FEITO
            case "message":
                src = data.get("src")
                dst = data.get("dst")
                message = data.get("message")
                timestamp = data.get("timestamp")
                
                # Verificar se o usuário de destino existe
                usuario_existe = any(u.get("user") == dst for u in usuarios)
                
                if not usuario_existe:
                    reply = {
                        "service": "message",
                        "data": {
                            "status": "erro",
                            "message": f"Usuário '{dst}' não existe",
                            "timestamp": time.time(),
                            "clock": relogio.tick()
                        }
                    }
                    print(f"[S] - Tentativa de enviar mensagem para usuário inexistente: {dst}", flush=True)
                else:
                    try:
                        pub_msg = {
                            "type": "user",
                            "topic": dst,  # Tópico é o nome do usuário de destino
                            "src": src,
                            "dst": dst,
                            "message": message,
                            "timestamp": timestamp,
                            "clock": relogio.get()
                        }
                        # Usar o socket PUB já criado
                        pub_socket.send(msgpack.packb(pub_msg))
                        
                        # Persistir a mensagem
                        salvar_mensagem_privada({
                            "src": src,
                            "dst": dst,
                            "message": message,
                            "timestamp": timestamp
                        })
                        
                        reply = {
                            "service": "message",
                            "data": {
                                "status": "OK",
                                "timestamp": time.time(),
                                "clock": relogio.tick()
                            }
                        }
                        print(f"[S] - Mensagem privada enviada de {src} para {dst}: {message}", flush=True)
                        # Replicar para outros servidores
                        replicar_para_outros_servidores({"service": "message", "data": data}, OUTROS_SERVIDORES)
                    except Exception as e:
                        reply = {
                            "service": "message",
                            "data": {
                                "status": "erro",
                                "message": f"Erro ao enviar mensagem: {str(e)}",
                                "timestamp": time.time(),
                                "clock": relogio.tick()
                            }
                        }
                        print(f"[S] - Falha ao enviar mensagem: {e}", flush=True)
        
            case _ :
                reply = {
                    "service": service if service else "unknown",
                    "data": {
                        "status": "erro",
                        "timestamp": time.time(),
                        "description": "Serviço não encontrado",
                        "clock": relogio.tick()
                    }
                }

        # Envia resposta usando MessagePack
        print(f"[S] 📤 Enviando resposta: {reply.get('service', 'N/A')} - Status: {reply.get('data', {}).get('status', 'N/A')}", flush=True)
        socket.send(msgpack.packb(reply))
        print(f"[S] ✅ Resposta enviada com sucesso!", flush=True)
    
    # Mensagens de sincronização e eleição (de outros servidores)
    if sync_socket in socks:
        try:
            request_data = sync_socket.recv()
            request = msgpack.unpackb(request_data, raw=False)
            service = request.get("service")
            data = request.get("data", {})
            
            # Atualizar relógio lógico
            if "clock" in data:
                relogio.update(data["clock"])
            
            if service == "clock":
                # Responder com o horário atual
                reply = {
                    "service": "clock",
                    "data": {
                        "time": time.time() + ajuste_relogio,
                        "timestamp": time.time(),
                        "clock": relogio.tick()
                    }
                }
                print(f"[S] Requisição de clock recebida", flush=True)
            
            elif service == "election":
                # Responder OK e iniciar própria eleição
                reply = {
                    "service": "election",
                    "data": {
                        "election": "OK",
                        "timestamp": time.time(),
                        "clock": relogio.tick()
                    }
                }
                print(f"[S] Requisição de eleição recebida", flush=True)
                
                # Iniciar própria eleição em thread separada
                threading.Thread(target=iniciar_eleicao, daemon=True).start()
            
            else:
                reply = {
                    "service": service,
                    "data": {
                        "status": "erro",
                        "message": "Serviço não reconhecido",
                        "timestamp": time.time(),
                        "clock": relogio.tick()
                    }
                }
            
            sync_socket.send(msgpack.packb(reply))
        
        except Exception as e:
            print(f"[S] Erro ao processar mensagem de sincronização: {e}", flush=True)
    
    except KeyboardInterrupt:
        print(f"\n[S] Servidor {NOME_SERVIDOR} encerrando...", flush=True)
        break
    except Exception as e:
        print(f"[S] ❌ Erro no loop principal: {e}", flush=True)
        print(f"[S] Tipo: {type(e).__name__}", flush=True)
        import traceback
        traceback.print_exc()
        print(f"[S] Continuando...", flush=True)
        time.sleep(0.1)
