import zmq
from time import sleep

context = zmq.Context()

# SUB para receber do servidor
sub_servidor = context.socket(zmq.SUB)
sub_servidor.connect("tcp://servidor:5559")  # Porta definida no servidor
sub_servidor.setsockopt_string(zmq.SUBSCRIBE, "")

# PUB para enviar ao proxy
pub_proxy = context.socket(zmq.PUB)
pub_proxy.connect("tcp://proxy:5557")  # Proxy XSUB

while True:
    try:
        mensagem = sub_servidor.recv_string()
        print(f"[PUBLISHER] Recebido do servidor: {mensagem}", flush=True)
        pub_proxy.send_string(mensagem)
        print(f"[PUBLISHER] Enviado ao proxy: {mensagem}", flush=True)
    except Exception as e:
        print(f"[PUBLISHER] Erro: {e}", flush=True)
    sleep(0.5)

pub_proxy.close()
sub_servidor.close()
context.close()