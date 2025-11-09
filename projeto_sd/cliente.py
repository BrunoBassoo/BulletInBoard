import zmq
from datetime import datetime
import sys
import msgpack

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

socket.setsockopt(zmq.RCVTIMEO, 10000)
socket.setsockopt(zmq.SNDTIMEO, 10000)

print("="*50, flush=True)
print("Bem-vindo ao BulletInBoard!", flush=True)
print("="*50, flush=True)
print("Opções disponíveis:", flush=True)
print("[1] - Login", flush=True)
print("[2] - Listar usuários", flush=True)
print("[3] - Cadastrar canal", flush=True)
print("[4] - Listar canais", flush=True)
print("[5] - Publicar mensagem em um canal", flush=True)
print("[6] - Enviar mensagem para usuário", flush=True)
print("[0] - Sair do programa", flush=True)
print("="*50, flush=True)


while True:
    try:
        opcao = input("\nEntre com a opção: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n\nEncerrando o programa...", flush=True)
        break
    
    if opcao == "0":
        print("Encerrando o programa...", flush=True)
        break
        
    try:
        match opcao:

            case "1":
                print("\n------ Login ------", flush=True)
                user = input("Entre com o seu usuário: ")
                timestamp = datetime.now().timestamp()

                request = {
                    "service": "login",
                    "data": {
                        "user": user,
                        "timestamp": timestamp,
                        "clock": relogio.tick()
                    }
                }
                
                socket.send(msgpack.packb(request))
                reply_data = socket.recv()
                reply = msgpack.unpackb(reply_data, raw=False)
                
                # Atualiza relógio lógico ao receber
                if "data" in reply and "clock" in reply["data"]:
                    relogio.update(reply["data"]["clock"])
                
                print(f"\n✅ Resposta recebida:", flush=True)
                print(f"   Status: {reply.get('data', {}).get('status', 'N/A')}", flush=True)
                if reply.get('data', {}).get('status') == 'erro':
                    print(f"   Erro: {reply.get('data', {}).get('description', 'N/A')}", flush=True)
                else:
                    print(f"   Login realizado com sucesso!", flush=True)
                print(f"   Clock: {reply.get('data', {}).get('clock', 'N/A')}", flush=True)

            

            # FEITO
            case "2":
                print("\n------ Listar usuários ------", flush=True)
                timestamp = datetime.now().timestamp()
                request = {
                    "service": "users",
                    "data": {
                        "timestamp": timestamp,
                        "clock": relogio.tick()
                    }
                }
                socket.send(msgpack.packb(request))
                reply_data = socket.recv()
                reply = msgpack.unpackb(reply_data, raw=False)
                if "data" in reply and "clock" in reply["data"]:
                    relogio.update(reply["data"]["clock"])
                
                print(f"\n📋 Usuários cadastrados:", flush=True)
                users = reply.get('data', {}).get('users', [])
                print(f"Total de usuários: {len(users)}", flush=True)
                if users:
                    for i, user in enumerate(users, 1):
                        print(f"   {i}. {user}", flush=True)
                else:
                    print(f"   Nenhum usuário cadastrado ainda.", flush=True)
                    print(f"   Dica: Use a opção 1 para fazer login primeiro!", flush=True)
            
            

            # FEITO
            case "3":
                print("\n------ Cadastrar canal ------", flush=True)
                canal = input("Entre com o canal: ")
                timestamp = datetime.now().timestamp()

                request = {
                    "service": "channel",
                    "data": {
                        "channel": canal,
                        "timestamp": timestamp,
                        "clock": relogio.tick()
                    }
                }
                socket.send(msgpack.packb(request))
                reply_data = socket.recv()
                reply = msgpack.unpackb(reply_data, raw=False)
                if "data" in reply and "clock" in reply["data"]:
                    relogio.update(reply["data"]["clock"])
                
                print(f"\n✅ Status: {reply.get('data', {}).get('status', 'N/A')}", flush=True)
                if reply.get('data', {}).get('status') == 'erro':
                    print(f"   Erro: {reply.get('data', {}).get('description', 'N/A')}", flush=True)
                else:
                    print(f"   Canal '{canal}' cadastrado com sucesso!", flush=True)

            

            # FEITO
            case "4":
                print("\n------ Listar canais ------", flush=True)
                timestamp = datetime.now().timestamp()
                request = {
                    "service": "channels",
                    "data": {
                        "timestamp": timestamp,
                        "clock": relogio.tick()
                    }
                }
                socket.send(msgpack.packb(request))
                reply_data = socket.recv()
                reply = msgpack.unpackb(reply_data, raw=False)
                if "data" in reply and "clock" in reply["data"]:
                    relogio.update(reply["data"]["clock"])
                
                print(f"\n📢 Canais disponíveis:", flush=True)
                channels = reply.get('data', {}).get('channels', [])
                print(f"Total de canais: {len(channels)}", flush=True)
                if channels:
                    for i, channel in enumerate(channels, 1):
                        print(f"   {i}. #{channel}", flush=True)
                else:
                    print(f"   Nenhum canal cadastrado ainda.", flush=True)
                    print(f"   Dica: Use a opção 3 para cadastrar um canal!", flush=True)
        
            
        
            # FEITO
            case "5":
                print("\n------ Publicar canal ------", flush=True)
                nome_do_usuário = input("Entre com o seu usuário: ")
                nome_do_canal = input("Entre com o nome do canal: ")
                mensagem = input("Entre com a mensagem a ser publicada: ")
                timestamp = datetime.now().timestamp()

                request = {
                    "service": "publish",
                    "data": {
                        "user": nome_do_usuário,
                        "channel": nome_do_canal,
                        "message": mensagem,
                        "timestamp": timestamp,
                        "clock": relogio.tick()
                    }
                }
                socket.send(msgpack.packb(request))
                reply_data = socket.recv()
                reply = msgpack.unpackb(reply_data, raw=False)
                if "data" in reply and "clock" in reply["data"]:
                    relogio.update(reply["data"]["clock"])
                
                print(f"\n✅ Status: {reply.get('data', {}).get('status', 'N/A')}", flush=True)
                if reply.get('data', {}).get('status') == 'erro':
                    print(f"   Erro: {reply.get('data', {}).get('message', 'N/A')}", flush=True)
                else:
                    print(f"   Mensagem publicada no canal #{nome_do_canal}!", flush=True)
            
            
            
            # FEITO
            case "6":
                print("\n------ Enviando mensagem privada ------", flush=True)
                nome_do_remetente = input("Entre com o seu usuário (origem): ")
                nome_do_destinatario = input("Entre com o nome do destinatário: ")
                mensagem = input("Entre com a mensagem a ser enviada: ")
                timestamp = datetime.now().timestamp()

                request = {
                    "service": "message",
                    "data": {
                        "src": nome_do_remetente,
                        "dst": nome_do_destinatario,
                        "message": mensagem,
                        "timestamp": timestamp,
                        "clock": relogio.tick()
                    }
                }
                socket.send(msgpack.packb(request))
                reply_data = socket.recv()
                reply = msgpack.unpackb(reply_data, raw=False)
                if "data" in reply and "clock" in reply["data"]:
                    relogio.update(reply["data"]["clock"])
                
                print(f"\n✅ Status: {reply.get('data', {}).get('status', 'N/A')}", flush=True)
                if reply.get('data', {}).get('status') == 'erro':
                    print(f"   Erro: {reply.get('data', {}).get('message', 'N/A')}", flush=True)
                else:
                    print(f"   Mensagem enviada para {nome_do_destinatario}!", flush=True)
            
            case _:
                print(f"\n❌ Opção '{opcao}' inválida! Por favor, escolha uma opção válida (0-6).", flush=True)
    
    except zmq.Again:
        # Recriar socket
        socket.close()
        socket = context.socket(zmq.REQ)
        socket.connect("tcp://broker:5555")
        socket.setsockopt(zmq.RCVTIMEO, 10000)
        socket.setsockopt(zmq.SNDTIMEO, 10000)
    except zmq.ZMQError:
        try:
            socket.close()
            socket = context.socket(zmq.REQ)
            socket.connect("tcp://broker:5555")
            socket.setsockopt(zmq.RCVTIMEO, 10000)
            socket.setsockopt(zmq.SNDTIMEO, 10000)
        except:
            break
    except Exception as e:
        print(f"\n❌ Erro: {e}", flush=True)

print("\n" + "="*50, flush=True)
print("Obrigado por usar o BulletInBoard!", flush=True)
print("="*50, flush=True)

# Limpar recursos
try:
    socket.close()
    context.term()
except:
    pass
