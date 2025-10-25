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

print("Bem-vindo ao BulletInBoard!")
print("Opções disponíveis:")
print("[1] - login")
print("[2] - listar]")
print("[3] - Cadastrar canal")
print("[4] - Listar canal")
print("[5] - Publicar mensagem em um canal")
print("[6] - Enviar mensagem para usuario")
print("[0] - Sair do programa")
print("-" * 40)


while True:
    
    opcao = input("\nEntre com a opção: ").strip().lower()    
    if opcao == "0":
        print("Encerrando o programa...")
        break
        
    match opcao:

        case "1":
            print("\n------ Login ------")
            user = input("Entre com o seu usuário: ")
            time = datetime.now().timestamp()

            request = {
                "opcao": "login",
                "dados": {
                    "user": user,
                    "time": time,
                    "clock": relogio.tick()
                }
            }
            socket.send(msgpack.packb(request))
            reply_data = socket.recv()
            reply = msgpack.unpackb(reply_data, raw=False)
            # Atualiza relógio lógico ao receber
            if "clock" in reply.get("dados", {}):
                relogio.update(reply["dados"]["clock"])
            print(f"Resposta: {reply}")

            

        # FEITO
        case "2":
            print("\n------ Listar usuários ------")
            request = {
                "opcao": "listar",
                "dados": {
                    "clock": relogio.tick()
                }
            }
            socket.send(msgpack.packb(request))
            reply_data = socket.recv()
            reply = msgpack.unpackb(reply_data, raw=False)
            if "clock" in reply.get("dados", {}):
                relogio.update(reply["dados"]["clock"])
            print(f"Resposta: {reply}")
            
            

        # FEITO
        case "3":
            print("\n------ Cadastrar canal ------")
            canal = input("Entre com o canal: ")
            time = datetime.now().timestamp()

            request = {
                "opcao": "cadastrarCanal",
                "dados": {
                    "canal": canal,
                    "time": time,
                    "clock": relogio.tick()
                }
            }
            socket.send(msgpack.packb(request))
            reply_data = socket.recv()
            reply = msgpack.unpackb(reply_data, raw=False)
            if "clock" in reply.get("dados", {}):
                relogio.update(reply["dados"]["clock"])
            print(f"Resposta: {reply}")

            

        # FEITO
        case "4":
            print("\n------ Listar canais ------")
            request = {
                "opcao": "listarCanal",
                "dados": {
                    "clock": relogio.tick()
                }
            }
            socket.send(msgpack.packb(request))
            reply_data = socket.recv()
            reply = msgpack.unpackb(reply_data, raw=False)
            if "clock" in reply.get("dados", {}):
                relogio.update(reply["dados"]["clock"])
            print(f"Resposta: {reply}")
        
            
        
        # FEITO
        case "5":
            print("\n------ Publicar canal ------")
            nome_do_usuário = input("Entre com o seu usuário: ")
            nome_do_canal = input("Entre com o nome do canal: ")
            mensagem = input("Entre com a mensagem a ser publicada: ")
            timestamp = datetime.now().timestamp()

            request = {
                "opcao": "publish",
                "dados": {
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
            if "clock" in reply.get("dados", {}):
                relogio.update(reply["dados"]["clock"])
            print(f"Resposta: {reply}")
            
            
        
        # EM ANDAMENTO
        case "6":
            print("\n------ Enviando mensagem privada ------")
            nome_do_usuário = input("Entre com o seu usuário: ")
            nome_do_receptor = input("Entre com o nome do receptor: ")
            mensagem = input("Entre com a mensagem a ser enviada: ")
            timestamp = datetime.now().timestamp()

            request = {
                "opcao": "message",
                "dados": {
                    "user": nome_do_usuário,
                    "receptor": nome_do_receptor,
                    "message": mensagem,
                    "timestamp": timestamp,
                    "clock": relogio.tick()
                }
            }
            socket.send(msgpack.packb(request))
            reply_data = socket.recv()
            reply = msgpack.unpackb(reply_data, raw=False)
            if "clock" in reply.get("dados", {}):
                relogio.update(reply["dados"]["clock"])
            print(f"Resposta: {reply}")
    
