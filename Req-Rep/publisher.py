
import zmq
from time import sleep

context = zmq.Context()

# SUB para receber do servidor
servidor_sub = context.socket(zmq.SUB)
servidor_sub.connect("tcp://servidor:5558")  # Porta definida no servidor
servidor_sub.setsockopt_string(zmq.SUBSCRIBE, "")  # Assina todos os tópicos

# PUB para enviar ao proxy
proxy_pub = context.socket(zmq.PUB)
proxy_pub.connect("tcp://proxy:5557")  # Proxy XSUB

while True:
    try:
        mensagem = servidor_sub.recv_string()
        print(f"[PUBLISHER] Recebido do servidor: {mensagem}", flush=True)
        proxy_pub.send_string(mensagem)
        print(f"[PUBLISHER] Enviado ao proxy: {mensagem}", flush=True)
    except Exception as e:
        print(f"[PUBLISHER] Erro: {e}", flush=True)
    sleep(0.5)

proxy_pub.close()
servidor_sub.close()
context.close()