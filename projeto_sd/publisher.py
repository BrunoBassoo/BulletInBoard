
import zmq
from time import sleep
import msgpack

context = zmq.Context()

# SUB para receber do servidor
servidor_sub = context.socket(zmq.SUB)
servidor_sub.connect("tcp://servidor:5559")  # Porta correta do servidor
servidor_sub.setsockopt_string(zmq.SUBSCRIBE, "")  # Assina todos os tópicos

# PUB para enviar ao proxy
proxy_pub = context.socket(zmq.PUB)
proxy_pub.connect("tcp://proxy:5557")  # Proxy XSUB

print("[PUBLISHER] Iniciando publisher...", flush=True)

while True:
    try:
        # Recebe mensagem serializada com MessagePack
        mensagem_data = servidor_sub.recv()
        mensagem = msgpack.unpackb(mensagem_data, raw=False)
        print(f"[PUBLISHER] Recebido do servidor: {mensagem}", flush=True)
        
        # Extrair o tópico da mensagem
        topic = mensagem.get("topic", "")
        
        if topic:
            # Enviar mensagem com tópico (multipart)
            # Formato: [tópico, mensagem]
            proxy_pub.send_string(topic, zmq.SNDMORE)
            proxy_pub.send(msgpack.packb(mensagem))
            print(f"[PUBLISHER] Enviado ao proxy no tópico '{topic}': {mensagem}", flush=True)
        else:
            # Enviar sem tópico (fallback)
            proxy_pub.send(msgpack.packb(mensagem))
            print(f"[PUBLISHER] Enviado ao proxy sem tópico: {mensagem}", flush=True)
        
    except Exception as e:
        print(f"[PUBLISHER] Erro: {e}", flush=True)
    sleep(0.1)

proxy_pub.close()
servidor_sub.close()
context.close()
