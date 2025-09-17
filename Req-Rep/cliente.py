import zmq
from datetime import datetime

#exemplo timestamap = datetime.now().timestamp()

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
                "opcao": "canal",
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
                "opcao": "listar",
                "dados": ""
            }

            socket.send_json(request)
            reply = socket.recv_string()

            if reply.split(":")[0] == "ERRO":
                print(reply, flush=True)

        case _:
            print("Opção não encontrada")

    opcao = input("Entre com a opção: ")
