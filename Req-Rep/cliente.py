import zmq
from datetime import datetime

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://broker:5555")

opcao = input("Entre com a opção: ")
while True:
    match opcao:

        # FEITO
        case "login":
        print("------ Login ------")
            user = input("Entre com o seu usuário: ")
            time = datetime.now().timestamp()

            request = {
                "opcao": "login",
                "dados": {
                    "user": user,
                    "time": time
                }
            }

            socket.send_json(request)
            reply = socket.recv_string()
            if reply.split(":")[0] == "ERRO":
                print(reply, flush=True)

        # FEITO
        case "listar":
            print("------ Listar usuários ------")
            request = {
                "opcao": "listar",
                "dados": ""
            }

            socket.send_json(request)
            reply = socket.recv_string()

            if reply.split(":")[0] == "ERRO":
                print(reply, flush=True)

        # FEITO
        case "cadastrarCanal":
            print("------ Cadastrar canal ------")
            canal = input("Entre com o canal: ")
            time = datetime.now().timestamp()

            request = {
                "opcao": "cadastrarCanal",
                "dados": {
                    "canal": canal,
                    "time": time
                }
            }

            socket.send_json(request)
            reply = socket.recv_string()
            if reply.split(":")[0] == "ERRO":
                print(reply, flush=True)

        # FEITO
        case "listarCanal":
            print("------ Listar canais ------")
            request = {
                "opcao": "listarCanal",
                "dados": ""
            }

            socket.send_json(request)
            reply = socket.recv_string()

            if reply.split(":")[0] == "ERRO":
                print(reply, flush=True)
        
        # FEITO
        case "publish":
            print("------ Publicar canal ------")
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
                    "timestamp": timestamp
                }
                
            }

            socket.send_json(request)
            reply = socket.recv_string()

            if reply.split(":")[0] == "ERRO":
                print(reply, flush=True)
        
        # EM ANDAMENTO
        case "message":
        
            print("------ enviando mensagem privada ------")
            nome_do_usuário = input("Entre com o seu usuário: ")
            nome_do_receptor = input("Entre com o nome do canal: ")
            mensagem = input("Entre com a mensagem a ser enviada: ")
            timestamp = datetime.now().timestamp()


            request = {
                "opcao": "message",
                "dados": {
                    "user": nome_do_usuário,
                    "receptor": nome_do_receptor,
                    "message": mensagem,
                    "timestamp": timestamp
                }
                
            }

            socket.send_json(request)
            reply = socket.recv_string()

            if reply.split(":")[0] == "ERRO":
                print(reply, flush=True)

        case _:
            print("Opção não encontrada")

    opcao = input("Entre com a opção: ")
