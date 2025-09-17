import zmq
import json

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.connect("tcp://broker:5556")

usuarios = dict()
canais = dict()
cont = 0

while True:
    request = socket.recv_json()
    opcao = request["opcao"]
    dados = request["dados"]
    reply = "ERRO: função não escolhida"

    match opcao:

        # FEITO
        case "login":
            usuarios[cont] = dados
            cont += 1
            reply = "OK"
            print(f"[S] - Login do {dados.get("user")} feito!",flush=True)

        # FEITO
        case "listar":

            for i in usuarios:
                print(f"Usuario {i}: {usuarios[i].get("user")}\n")
                reply = "OK"

            print(f"Usuarios listados com sucesso!", flush=True)
        
        # FEITO
        case "cadastrarCanal":
            canais[cont] = dados
            cont += 1
            reply = "OK"
            print(f"[S] - Cadastro do canal {dados.get("user")} feito!",flush=True)

        # FEITO
        case "listarCanal":

            for i in canais:
                print(f"Canal {i}: {canais[i].get("canal")}\n")
                reply = "OK"

            print(f"Canais listados com sucesso!", flush=True)
                
        case _ :
            reply = "ERRO: função não encontrada"

    socket.send_string(reply)
