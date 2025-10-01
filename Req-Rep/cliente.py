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
            user = input("Entre com o usuario: ")
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
            nome_do_usuário = input("Entre com o nome do usuário: ")
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

        case _:
            print("Opção não encontrada")

    opcao = input("Entre com a opção: ")
