import zmq
from time import sleep
import msgpack
import sys
import os

# Obtém o nome do usuário das variáveis de ambiente ou usa um padrão
usuario = os.environ.get("SUBSCRIBER_USER", "subscriber_default")
canais_inscritos = os.environ.get("SUBSCRIBER_CHANNELS", "").split(",")
canais_inscritos = [c.strip() for c in canais_inscritos if c.strip()]

context = zmq.Context()
sub = context.socket(zmq.SUB)

# Conecta ao proxy XPUB
sub.connect("tcp://proxy:5558")

# Se inscrever no próprio nome de usuário para receber mensagens privadas
sub.setsockopt_string(zmq.SUBSCRIBE, usuario)
print(f"[SUBSCRIBER {usuario}] Inscrito no tópico de usuário: {usuario}", flush=True)

# Se inscrever nos canais especificados
for canal in canais_inscritos:
    sub.setsockopt_string(zmq.SUBSCRIBE, canal)
    print(f"[SUBSCRIBER {usuario}] Inscrito no canal: {canal}", flush=True)

print(f"[SUBSCRIBER {usuario}] Aguardando mensagens...", flush=True)

while True:
    try:
        # Recebe mensagem com tópico (multipart)
        # Formato: [tópico, mensagem]
        topic = sub.recv_string()
        mensagem_data = sub.recv()
        mensagem = msgpack.unpackb(mensagem_data, raw=False)
        
        msg_type = mensagem.get("type")
        if msg_type == "user":
            # Mensagem privada
            src = mensagem.get("src")
            message = mensagem.get("message")
            timestamp = mensagem.get("timestamp")
            print(f"[SUBSCRIBER {usuario}] 💌 Mensagem privada de {src}: {message}", flush=True)
        elif msg_type == "channel":
            # Mensagem de canal
            user = mensagem.get("user")
            channel = mensagem.get("channel")
            message = mensagem.get("message")
            timestamp = mensagem.get("timestamp")
            print(f"[SUBSCRIBER {usuario}] 📢 Canal #{channel} - {user}: {message}", flush=True)
        else:
            print(f"[SUBSCRIBER {usuario}] Mensagem recebida (tópico: {topic}): {mensagem}", flush=True)
        
    except Exception as e:
        print(f"[SUBSCRIBER {usuario}] Erro: {e}", flush=True)
    sleep(0.1)

sub.close()
context.close()
