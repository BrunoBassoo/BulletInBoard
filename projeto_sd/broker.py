import zmq

print("[BROKER] Iniciando broker...", flush=True)

context = zmq.Context()

client_socket = context.socket(zmq.ROUTER)
client_socket.bind("tcp://*:5555")
print("[BROKER] ✅ Socket ROUTER bound na porta 5555 (clientes)", flush=True)

server_socket = context.socket(zmq.DEALER)
server_socket.bind("tcp://*:5556")
print("[BROKER] ✅ Socket DEALER bound na porta 5556 (servidores)", flush=True)

print("[BROKER] 🚀 Broker pronto! Iniciando proxy...", flush=True)

try:
    zmq.proxy(client_socket, server_socket)
except KeyboardInterrupt:
    print("\n[BROKER] Encerrando broker...", flush=True)
except Exception as e:
    print(f"[BROKER] Erro: {e}", flush=True)
finally:
    client_socket.close()
    server_socket.close()
    context.term()
    print("[BROKER] Broker encerrado.", flush=True)
