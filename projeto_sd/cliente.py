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

print("BulletInBoard", flush=True)
print("[1] Login", flush=True)
print("[2] Listar usuarios", flush=True)
print("[3] Cadastrar canal", flush=True)
print("[4] Listar canais", flush=True)
print("[5] Publicar em canal", flush=True)
print("[6] Mensagem privada", flush=True)
print("[0] Sair", flush=True)


while True:
    try:
        opcao = input("\nOpcao: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        break
    
    if opcao == "0":
        break
        
    try:
        match opcao:

            case "1":
                user = input("Usuario: ")
                
                request = {
                    "service": "login",
                    "data": {
                        "user": user,
                        "timestamp": datetime.now().timestamp(),
                        "clock": relogio.tick()
                    }
                }
                
                socket.send(msgpack.packb(request))
                reply_data = socket.recv()
                reply = msgpack.unpackb(reply_data, raw=False)
                
                if "data" in reply and "clock" in reply["data"]:
                    relogio.update(reply["data"]["clock"])
                
                status = reply.get('data', {}).get('status')
                if status == 'erro':
                    print(f"Erro: {reply.get('data', {}).get('description')}", flush=True)
                else:
                    print(f"Login OK", flush=True)

            case "2":
                request = {
                    "service": "users",
                    "data": {
                        "timestamp": datetime.now().timestamp(),
                        "clock": relogio.tick()
                    }
                }
                socket.send(msgpack.packb(request))
                reply_data = socket.recv()
                reply = msgpack.unpackb(reply_data, raw=False)
                
                if "data" in reply and "clock" in reply["data"]:
                    relogio.update(reply["data"]["clock"])
                
                users = reply.get('data', {}).get('users', [])
                print(f"Usuarios ({len(users)}):", flush=True)
                for user in users:
                    print(f"  {user}", flush=True)

            case "3":
                canal = input("Canal: ")
                
                request = {
                    "service": "channel",
                    "data": {
                        "channel": canal,
                        "timestamp": datetime.now().timestamp(),
                        "clock": relogio.tick()
                    }
                }
                socket.send(msgpack.packb(request))
                reply_data = socket.recv()
                reply = msgpack.unpackb(reply_data, raw=False)
                
                if "data" in reply and "clock" in reply["data"]:
                    relogio.update(reply["data"]["clock"])
                
                status = reply.get('data', {}).get('status')
                if status == 'erro':
                    print(f"Erro: {reply.get('data', {}).get('description')}", flush=True)
                else:
                    print(f"Canal cadastrado", flush=True)

            case "4":
                request = {
                    "service": "channels",
                    "data": {
                        "timestamp": datetime.now().timestamp(),
                        "clock": relogio.tick()
                    }
                }
                socket.send(msgpack.packb(request))
                reply_data = socket.recv()
                reply = msgpack.unpackb(reply_data, raw=False)
                
                if "data" in reply and "clock" in reply["data"]:
                    relogio.update(reply["data"]["clock"])
                
                channels = reply.get('data', {}).get('channels', [])
                print(f"Canais ({len(channels)}):", flush=True)
                for channel in channels:
                    print(f"  {channel}", flush=True)

            case "5":
                usuario = input("Usuario: ")
                canal = input("Canal: ")
                mensagem = input("Mensagem: ")

                request = {
                    "service": "publish",
                    "data": {
                        "user": usuario,
                        "channel": canal,
                        "message": mensagem,
                        "timestamp": datetime.now().timestamp(),
                        "clock": relogio.tick()
                    }
                }
                socket.send(msgpack.packb(request))
                reply_data = socket.recv()
                reply = msgpack.unpackb(reply_data, raw=False)
                
                if "data" in reply and "clock" in reply["data"]:
                    relogio.update(reply["data"]["clock"])
                
                status = reply.get('data', {}).get('status')
                if status == 'erro':
                    print(f"Erro: {reply.get('data', {}).get('message')}", flush=True)
                else:
                    print(f"Publicado", flush=True)

            case "6":
                src = input("De (usuario): ")
                dst = input("Para (usuario): ")
                mensagem = input("Mensagem: ")

                request = {
                    "service": "message",
                    "data": {
                        "src": src,
                        "dst": dst,
                        "message": mensagem,
                        "timestamp": datetime.now().timestamp(),
                        "clock": relogio.tick()
                    }
                }
                socket.send(msgpack.packb(request))
                reply_data = socket.recv()
                reply = msgpack.unpackb(reply_data, raw=False)
                
                if "data" in reply and "clock" in reply["data"]:
                    relogio.update(reply["data"]["clock"])
                
                status = reply.get('data', {}).get('status')
                if status == 'erro':
                    print(f"Erro: {reply.get('data', {}).get('message')}", flush=True)
                else:
                    print(f"Enviado", flush=True)
            
            case _:
                print(f"Opcao invalida", flush=True)
    
    except:
        pass

socket.close()
context.term()
