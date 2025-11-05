import zmq
import msgpack
import time
from datetime import datetime

context = zmq.Context()

# SUB para receber do proxy XPUB na porta 5558
sub = context.socket(zmq.SUB)
sub.connect("tcp://proxy:5558")
sub.setsockopt_string(zmq.SUBSCRIBE, "")  # Assina todos os tópicos

print("[SUBSCRIBER] Iniciando subscriber para monitoramento...", flush=True)
print("[SUBSCRIBER] Conectado ao proxy (porta 5558)", flush=True)
print("[SUBSCRIBER] Mostrando todas as mensagens do sistema:", flush=True)
print("-" * 60, flush=True)

time.sleep(2)  # Aguarda conexões

while True:
    try:
        # Recebe mensagem do proxy (com tópico)
        parts = sub.recv_multipart()
        
        if len(parts) == 2:
            topic, data = parts
            topic_str = topic.decode('utf-8')
            mensagem = msgpack.unpackb(data, raw=False)
            
            timestamp = datetime.fromtimestamp(mensagem.get('timestamp', time.time())).strftime('%H:%M:%S')
            clock = mensagem.get('clock', 'N/A')
            
            # Verifica tipo de mensagem
            if "channel" in mensagem:
                # Mensagem de canal
                print(f"[{timestamp}] CANAL '{topic_str}' | {mensagem['user']}: {mensagem['message']} [Clock: {clock}]", flush=True)
            elif "dst" in mensagem:
                # Mensagem privada
                print(f"[{timestamp}] PRIVADA para '{topic_str}' | De: {mensagem['src']}: {mensagem['message']} [Clock: {clock}]", flush=True)
            elif "coordinator" in mensagem.get("data", {}):
                # Eleição
                print(f"[{timestamp}] ELEIÇÃO | Novo coordenador: {mensagem['data']['coordinator']} [Clock: {clock}]", flush=True)
            else:
                print(f"[{timestamp}] TÓPICO '{topic_str}' | {mensagem} [Clock: {clock}]", flush=True)
        else:
            # Mensagem sem tópico
            data = parts[0]
            mensagem = msgpack.unpackb(data, raw=False)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] SEM TÓPICO | {mensagem}", flush=True)
        
    except Exception as e:
        print(f"[SUBSCRIBER] Erro: {e}", flush=True)
        time.sleep(0.5)

