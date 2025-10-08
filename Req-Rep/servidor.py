import zmq
import json

PUB_PORT = 5559  # Porta para publisher

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.connect("tcp://broker:5556")

usuarios = dict()
canais = dict()
cont = 0

while True:
    request = socket.recv_json()
    opcao = request.get("opcao")
    dados = request.get("dados")
    reply = "ERRO: função não escolhida"
    print(dados)
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

        # FEITO
        case "publish":
            try:
                # Espera dict com user, channel, message, timestamp
                user = dados.get("user")
                channel = dados.get("channel")
                message = dados.get("message")
                timestamp = dados.get("timestamp")

                pub_msg = json.dumps({
                    "user": user,
                    "channel": channel,
                    "message": message,
                    "timestamp": timestamp
                })

                # Envia para o publisher
                pub_socket = context.socket(zmq.PUB)
                pub_socket.bind(f"tcp://*:{PUB_PORT}")
                pub_socket.send_string(pub_msg)
                reply = "OK: mensagem publicada"
                print(f"[S] - Mensagem publicada para publisher: {pub_msg}", flush=True)
                pub_socket.close()
            except Exception as e:
                reply = f"ERRO: {e}"
                print(f"[S] - Falha ao publicar mensagem: {e}", flush=True)

        # FEITO
        case "message":
            try:
                # Espera dict com user, receptor, message, timestamp
                user = dados.get("user")
                receptor = dados.get("receptor")
                message = dados.get("message")
                timestamp = dados.get("timestamp")

                pub_msg = json.dumps({
                    "user": user,
                    "receptor": receptor,
                    "message": message,
                    "timestamp": timestamp
                })

                # Envia para o publisher
                pub_socket = context.socket(zmq.PUB)
                pub_socket.bind(f"tcp://*:{PUB_PORT}")
                pub_socket.send_string(pub_msg)
                reply = "OK: mensagem publicada"
                print(f"[P] - Mensagem publicada para publisher: {pub_msg}", flush=True)
                pub_socket.close()
            except Exception as e:
                reply = f"ERRO: {e}"
                print(f"[P] - Falha ao publicar mensagem: {e}", flush=True)
    
        case _ :
            reply = "ERRO: função não encontrada"

    socket.send_string(reply)
