import zmq
from datetime import datetime
import msgpack
import random
import time
import os

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

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://broker:5555")

# Gerar nome de usuário - prioriza variável de ambiente
usuario = os.environ.get("CLIENT_NAME")
if not usuario:
    usuario = f"bot_{random.randint(1000, 9999)}"

print(f"[{usuario}] Iniciando cliente automático... (clock: {relogio.get()})", flush=True)

# Fazer login
request = {
    "service": "login",
    "data": {
        "user": usuario,
        "timestamp": datetime.now().timestamp(),
        "clock": relogio.tick()
    }
}
socket.send(msgpack.packb(request))
reply_data = socket.recv()
reply = msgpack.unpackb(reply_data, raw=False)
if "data" in reply and "clock" in reply["data"]:
    relogio.update(reply["data"]["clock"])

print(f"[{usuario}] Login realizado (clock: {relogio.get()})", flush=True)

# Listar canais iniciais
request = {
    "service": "channels",
    "data": {
        "timestamp": datetime.now().timestamp(),
        "clock": relogio.tick()
    }
}
socket.send(msgpack.packb(request))
reply_data = socket.recv()
reply = msgpack.unpackb(reply_data, raw=False)
if "data" in reply and "clock" in reply["data"]:
    relogio.update(reply["data"]["clock"])

print(f"[{usuario}] Canais listados (clock: {relogio.get()})", flush=True)

# Mensagens pré-definidas que o bot pode enviar
mensagens_disponiveis = [
    "Olá a todos!",
    "Mensagem automática.",
    "Testando o canal.",
    "Mensagem de exemplo.",
    "Pub/Sub funcionando.",
    "Mais uma mensagem.",
    "Python é legal.",
    "Distribuído é melhor.",
    "ZeroMQ test.",
    "Fim das mensagens."
]

# Canais padrão (fallback caso não existam canais)
canais_padrao = ["geral", "noticias"]

# Loop infinito
while True:
    try:
        # Obter lista de canais disponíveis
        request = {
            "service": "channels",
            "data": {
                "timestamp": datetime.now().timestamp(),
                "clock": relogio.tick()
            }
        }
        socket.send(msgpack.packb(request))
        reply_data = socket.recv()
        reply = msgpack.unpackb(reply_data, raw=False)
        if "data" in reply and "clock" in reply["data"]:
            relogio.update(reply["data"]["clock"])
        
        canais = reply.get("data", {}).get("channels", [])
        
        # Se não há canais cadastrados, usar canais padrão
        if not canais:
            canais = canais_padrao
        
        # Escolher um canal aleatório
        canal_escolhido = random.choice(canais)
        
        # Enviar 10 mensagens no canal escolhido
        for i in range(10):
            mensagem = random.choice(mensagens_disponiveis)
            
            request = {
                "service": "publish",
                "data": {
                    "user": usuario,
                    "channel": canal_escolhido,
                    "message": mensagem,
                    "timestamp": datetime.now().timestamp(),
                    "clock": relogio.tick()
                }
            }
            socket.send(msgpack.packb(request))
            reply_data = socket.recv()
            reply = msgpack.unpackb(reply_data, raw=False)
            if "data" in reply and "clock" in reply["data"]:
                relogio.update(reply["data"]["clock"])
            
            print(f"[{usuario}] Publicou no canal '{canal_escolhido}': {mensagem} (clock: {relogio.get()})", flush=True)
            
            # Delay de 0.5 segundos entre mensagens
            time.sleep(0.5)
        
        # Atualizar lista de canais
        request = {
            "service": "channels",
            "data": {
                "timestamp": datetime.now().timestamp(),
                "clock": relogio.tick()
            }
        }
        socket.send(msgpack.packb(request))
        reply_data = socket.recv()
        reply = msgpack.unpackb(reply_data, raw=False)
        if "data" in reply and "clock" in reply["data"]:
            relogio.update(reply["data"]["clock"])
        
        # Aguardar 2 segundos antes do próximo ciclo
        time.sleep(2)
        
    except Exception as e:
        print(f"[{usuario}] Erro no loop: {e}", flush=True)
        time.sleep(5)

