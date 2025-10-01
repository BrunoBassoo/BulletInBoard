import zmq
from time import sleep

context = zmq.Context()
sub = context.socket(zmq.SUB)
sub.setsockopt_string(zmq.SUBSCRIBE, "")

# Conecta ao proxy XPUB
sub.connect("tcp://proxy:5558")

while True:
    mensagem = sub.recv_string()
    print(f"[SUBSCRIBER] Mensagem recebida do proxy: {mensagem}", flush=True)
    sleep(0.5)

sub.close()
context.close()
