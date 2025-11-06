import zmq
from time import sleep
import msgpack

context = zmq.Context()
sub = context.socket(zmq.SUB)
sub.setsockopt_string(zmq.SUBSCRIBE, "")

# Conecta ao proxy XPUB
sub.connect("tcp://proxy:5558")

print("[SUBSCRIBER] Iniciando subscriber...", flush=True)

while True:
    try:
        # Recebe mensagem serializada com MessagePack
        mensagem_data = sub.recv()
        mensagem = msgpack.unpackb(mensagem_data, raw=False)
        print(f"[SUBSCRIBER] Mensagem recebida do proxy: {mensagem}", flush=True)
        
    except Exception as e:
        print(f"[SUBSCRIBER] Erro: {e}", flush=True)
    sleep(0.5)

sub.close()
context.close()
