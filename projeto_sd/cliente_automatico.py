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

usuario = os.environ.get("CLIENT_NAME")
if not usuario:
    usuario = f"bot_{random.randint(1000, 9999)}"

print(f"[BOT {usuario}] Iniciado", flush=True)

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

mensagens_disponiveis = [
    "Ola a todos!",
    "Mensagem automatica.",
    "Testando o canal.",
    "Mensagem de exemplo.",
    "Pub/Sub funcionando.",
    "Mais uma mensagem.",
    "Python e legal.",
    "Distribuido e melhor.",
    "ZeroMQ test.",
    "Fim das mensagens."
]

canais_padrao = ["geral", "noticias"]

while True:
    try:
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
        if not canais:
            canais = canais_padrao
        
        canal_escolhido = random.choice(canais)
        
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
            
            print(f"[BOT {usuario}] {canal_escolhido}: {mensagem}", flush=True)
            time.sleep(0.5)
        
        time.sleep(2)
    except:
        time.sleep(5)

