import zmq
import msgpack
import time

context = zmq.Context()

# SUB para receber do servidor na porta 5559
servidor_sub = context.socket(zmq.SUB)
servidor_sub.bind("tcp://*:5559")
servidor_sub.setsockopt_string(zmq.SUBSCRIBE, "")  # Assina todos os tópicos

# PUB para enviar ao proxy XSUB na porta 5557
proxy_pub = context.socket(zmq.PUB)
proxy_pub.connect("tcp://proxy:5557")

print("[PUBLISHER] Iniciando publisher intermediário...", flush=True)
print("[PUBLISHER] Recebendo de servidores (porta 5559)", flush=True)
print("[PUBLISHER] Enviando para proxy (porta 5557)", flush=True)

time.sleep(2)  # Aguarda conexões estabilizarem

while True:
    try:
        # Recebe mensagem do servidor (pode ter tópico ou não)
        parts = servidor_sub.recv_multipart()
        
        if len(parts) == 2:
            # Mensagem com tópico
            topic, data = parts
            mensagem = msgpack.unpackb(data, raw=False)
            print(f"[PUBLISHER] Recebido com tópico '{topic.decode('utf-8')}': {mensagem.get('message', mensagem)}", flush=True)
            # Repassa com tópico para o proxy
            proxy_pub.send_multipart([topic, data])
        else:
            # Mensagem sem tópico (formato antigo)
            data = parts[0]
            mensagem = msgpack.unpackb(data, raw=False)
            print(f"[PUBLISHER] Recebido sem tópico: {mensagem}", flush=True)
            # Repassa para o proxy
            proxy_pub.send(data)
        
    except Exception as e:
        print(f"[PUBLISHER] Erro: {e}", flush=True)
        time.sleep(0.5)

