import zmq
from datetime import datetime
import msgpack
import random
import time

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

# Gerar nome de usuário aleatório
usuario = f"bot_{random.randint(1000, 9999)}"
print(f"[BOT] Iniciando cliente automático com usuário: {usuario}", flush=True)

# Fazer login
print(f"[BOT] Fazendo login com usuário: {usuario}", flush=True)
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
print(f"[BOT] Resposta do login: {reply}", flush=True)

# Aguardar um pouco para garantir que o servidor está pronto
time.sleep(2)

# Mensagens pré-definidas que o bot pode enviar
mensagens_disponiveis = [
    "Olá pessoal! 👋",
    "Como vocês estão?",
    "Alguém aí?",
    "Essa mensagem foi enviada automaticamente",
    "Teste de mensagem automática",
    "Bot funcionando perfeitamente! 🤖",
    "Enviando mensagem número {}",
    "Espero que estejam bem!",
    "Saudações do bot automático",
    "Mensagem teste {}"
]

# Loop infinito
contador = 0
while True:
    try:
        # Obter lista de canais disponíveis
        print(f"\n[BOT] Solicitando lista de canais...", flush=True)
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
        print(f"[BOT] Canais disponíveis: {canais}", flush=True)
        
        if not canais:
            print("[BOT] Nenhum canal disponível. Aguardando 5 segundos...", flush=True)
            time.sleep(5)
            continue
        
        # Escolher um canal aleatório
        canal_escolhido = random.choice(canais)
        print(f"[BOT] Canal escolhido: {canal_escolhido}", flush=True)
        
        # Enviar 10 mensagens
        for i in range(10):
            # Escolher uma mensagem aleatória
            mensagem = random.choice(mensagens_disponiveis)
            if "{}" in mensagem:
                mensagem = mensagem.format(contador + 1)
            
            print(f"[BOT] Enviando mensagem {i+1}/10 para o canal '{canal_escolhido}': {mensagem}", flush=True)
            
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
            
            status = reply.get("data", {}).get("status")
            if status == "OK":
                print(f"[BOT] ✅ Mensagem {i+1} enviada com sucesso!", flush=True)
            else:
                erro = reply.get("data", {}).get("message", "Erro desconhecido")
                print(f"[BOT] ❌ Erro ao enviar mensagem {i+1}: {erro}", flush=True)
            
            contador += 1
            
            # Pequeno delay entre mensagens
            time.sleep(1)
        
        # Aguardar antes de começar novo ciclo
        print(f"[BOT] Aguardando 3 segundos antes do próximo ciclo...", flush=True)
        time.sleep(3)
        
    except Exception as e:
        print(f"[BOT] Erro no loop: {e}", flush=True)
        time.sleep(5)

