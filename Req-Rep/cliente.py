import zmq
from datetime import datetime
import sys

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://broker:5555")

print("Bem-vindo ao BulletInBoard!")
print("Opções disponíveis:")
print("login - Fazer login no sistema")
print("listar - Listar usuários")
print("cadastrarCanal - Cadastrar novo canal")
print("listarCanal - Listar canais disponíveis")
print("publish - Publicar mensagem em um canal")
print("message - Enviar mensagem privada")
print("sair - Sair do programa")
print("-" * 40)

while True:
    try:
        opcao = input("\nEntre com a opção: ").strip().lower()
        
        if opcao == "sair":
            print("Encerrando o programa...")
            socket.close()
            context.term()
            sys.exit(0)
            
        match opcao:

            case "login":
                print("\n------ Login ------")
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
                print(f"Resposta: {reply}")

                

            # FEITO
            case "listar":
                print("\n------ Listar usuários ------")
                request = {
                    "opcao": "listar",
                    "dados": ""
                }

                socket.send_json(request)
                reply = socket.recv_string()
                print(f"Resposta: {reply}")
                
                

            # FEITO
            case "cadastrarCanal":
                print("\n------ Cadastrar canal ------")
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
                print(f"Resposta: {reply}")

                

            # FEITO
            case "listarCanal":
                print("\n------ Listar canais ------")
                request = {
                    "opcao": "listarCanal",
                    "dados": ""
                }

                socket.send_json(request)
                reply = socket.recv_string()
                print(f"Resposta: {reply}")
            
                
            
            # FEITO
            case "publish":
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
                        "timestamp": timestamp
                    }
                }

                socket.send_json(request)
                reply = socket.recv_string()
                print(f"Resposta: {reply}")
                
                
            
            # EM ANDAMENTO
            case "message":
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
                        "timestamp": timestamp
                    }
                }

                socket.send_json(request)
                reply = socket.recv_string()
                print(f"Resposta: {reply}")


    except KeyboardInterrupt:
        print("\nEncerrando o programa...")
        socket.close()
        context.term()
        sys.exit(0)
    except Exception as e:
        print(f"\nErro: {str(e)}")
        print("Tentando continuar...")
    
