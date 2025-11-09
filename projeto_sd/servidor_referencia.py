import zmq
import msgpack
import time
import threading
from datetime import datetime

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

# Estrutura para armazenar servidores
# {nome: {"rank": rank, "last_heartbeat": timestamp}}
servidores = {}
proximo_rank = 1
lock = threading.Lock()

# Timeout para heartbeat (em segundos)
HEARTBEAT_TIMEOUT = 30

def limpar_servidores_inativos():
    """Remove servidores que não enviaram heartbeat recentemente"""
    while True:
        time.sleep(10)  # Verificar a cada 10 segundos
        tempo_atual = time.time()
        
        with lock:
            servidores_inativos = []
            for nome, info in servidores.items():
                if tempo_atual - info["last_heartbeat"] > HEARTBEAT_TIMEOUT:
                    servidores_inativos.append(nome)
            
            for nome in servidores_inativos:
                print(f"[REF] Removendo servidor inativo: {nome}", flush=True)
                del servidores[nome]

# Iniciar thread de limpeza
threading.Thread(target=limpar_servidores_inativos, daemon=True).start()

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5560")

print("[REF] Servidor de Referência iniciado na porta 5560", flush=True)

while True:
    try:
        # Receber mensagem
        request_data = socket.recv()
        request = msgpack.unpackb(request_data, raw=False)
        
        service = request.get("service")
        data = request.get("data", {})
        
        # Atualizar relógio lógico
        if "clock" in data:
            relogio.update(data["clock"])
        
        print(f"[REF] Requisição recebida: {service} | Data: {data}", flush=True)
        
        if service == "rank":
            # Atribuir rank ao servidor
            nome_servidor = data.get("user")
            
            with lock:
                if nome_servidor not in servidores:
                    global proximo_rank
                    rank = proximo_rank
                    proximo_rank += 1
                    servidores[nome_servidor] = {
                        "rank": rank,
                        "last_heartbeat": time.time()
                    }
                    print(f"[REF] Novo servidor cadastrado: {nome_servidor} com rank {rank}", flush=True)
                else:
                    rank = servidores[nome_servidor]["rank"]
                    servidores[nome_servidor]["last_heartbeat"] = time.time()
                    print(f"[REF] Servidor existente: {nome_servidor} com rank {rank}", flush=True)
            
            reply = {
                "service": "rank",
                "data": {
                    "rank": rank,
                    "timestamp": time.time(),
                    "clock": relogio.tick()
                }
            }
        
        elif service == "list":
            # Retornar lista de servidores
            with lock:
                lista_servidores = [
                    {"name": nome, "rank": info["rank"]} 
                    for nome, info in servidores.items()
                ]
            
            reply = {
                "service": "list",
                "data": {
                    "list": lista_servidores,
                    "timestamp": time.time(),
                    "clock": relogio.tick()
                }
            }
            print(f"[REF] Lista de servidores: {lista_servidores}", flush=True)
        
        elif service == "heartbeat":
            # Atualizar heartbeat do servidor
            nome_servidor = data.get("user")
            
            with lock:
                if nome_servidor in servidores:
                    servidores[nome_servidor]["last_heartbeat"] = time.time()
                    print(f"[REF] Heartbeat recebido de: {nome_servidor}", flush=True)
                    status = "OK"
                else:
                    print(f"[REF] Heartbeat de servidor desconhecido: {nome_servidor}", flush=True)
                    status = "unknown"
            
            reply = {
                "service": "heartbeat",
                "data": {
                    "status": status,
                    "timestamp": time.time(),
                    "clock": relogio.tick()
                }
            }
        
        else:
            # Serviço desconhecido
            reply = {
                "service": service,
                "data": {
                    "status": "erro",
                    "message": "Serviço não reconhecido",
                    "timestamp": time.time(),
                    "clock": relogio.tick()
                }
            }
        
        # Enviar resposta
        socket.send(msgpack.packb(reply))
        
    except Exception as e:
        print(f"[REF] Erro: {e}", flush=True)
        # Enviar resposta de erro
        error_reply = {
            "service": "error",
            "data": {
                "message": str(e),
                "timestamp": time.time(),
                "clock": relogio.tick()
            }
        }
        socket.send(msgpack.packb(error_reply))

