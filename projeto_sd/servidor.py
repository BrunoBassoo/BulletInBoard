import threading
# Lista de endereços dos outros servidores (exemplo, ajuste conforme sua rede)
OUTROS_SERVIDORES = [
    "tcp://servidor2:5556",
    "tcp://servidor3:5556"
]

# Função para replicar mensagem para outros servidores
def replicar_para_outros_servidores(mensagem, lista_enderecos):
    def enviar(endereco):
        try:
            ctx = zmq.Context()
            sock = ctx.socket(zmq.REQ)
            sock.connect(endereco)
            sock.send(msgpack.packb(mensagem))
            sock.close()
            ctx.term()
        except Exception as e:
            print(f"Erro ao replicar para {endereco}: {e}")
    for endereco in lista_enderecos:
        threading.Thread(target=enviar, args=(endereco,)).start()
import zmq
import msgpack
import time

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

PUB_PORT = 5559  # Porta para publisher

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.connect("tcp://broker:5556")

usuarios = dict()
canais = dict()
cont = 0

while True:
    # Recebe mensagem serializada com MessagePack
    request_data = socket.recv()
    request = msgpack.unpackb(request_data, raw=False)
    opcao = request.get("opcao")
    dados = request.get("dados")
    # Atualiza relógio lógico ao receber
    if dados and "clock" in dados:
        relogio.update(dados["clock"])

    match opcao:

        # FEITO
        case "login":
            usuarios[cont] = dados
            cont += 1
            reply = {
                "msg": "OK",
                "clock": relogio.tick(),
                "timestamp": time.time()
            }
            print(f"[S] - Login do {dados.get('user')} feito!",flush=True)
            # Replicar para outros servidores
            replicar_para_outros_servidores({"opcao": "login", "dados": dados}, OUTROS_SERVIDORES)

        # FEITO
        case "listar":
            for i in usuarios:
                print(f"Usuario {i}: {usuarios[i].get('user')} | time: {usuarios[i].get('time')}")
            reply = {
                "msg": "usuarios listados com sucesso",
                "clock": relogio.tick(),
                "timestamp": time.time()
            }
            print(f"Usuarios listados com sucesso!", flush=True)
        
        # FEITO
        case "cadastrarCanal":
            canais[cont] = dados
            cont += 1
            reply = {
                "msg": "cadastro de canal OK",
                "clock": relogio.tick(),
                "timestamp": time.time()
            }
            print(f"[S] - Cadastro do canal {dados.get('user')} feito!",flush=True)
            # Replicar para outros servidores
            replicar_para_outros_servidores({"opcao": "cadastrarCanal", "dados": dados}, OUTROS_SERVIDORES)

        # FEITO
        case "listarCanal":
            for i in canais:
                print(f"Canal {i}: {canais[i].get('canal')}")
            reply = {
                "msg": "lista de canais OK",
                "clock": relogio.tick(),
                "timestamp": time.time()
            }
            print(f"Canais listados com sucesso!", flush=True)

        # FEITO
        case "publish":
            try:
                user = dados.get("user")
                channel = dados.get("channel")
                message = dados.get("message")
                timestamp = dados.get("timestamp")
                pub_msg = {
                    "user": user,
                    "channel": channel,
                    "message": message,
                    "timestamp": timestamp,
                    "clock": relogio.get()
                }
                pub_socket = context.socket(zmq.PUB)
                pub_socket.bind(f"tcp://*:{PUB_PORT}")
                pub_socket.send(msgpack.packb(pub_msg))
                reply = {
                    "msg": f"Mensagem publicada para o canal: {channel}",
                    "clock": relogio.tick(),
                    "timestamp": time.time()
                }
                print(f"[S] - Mensagem publicada para publisher: {pub_msg}", flush=True)
                pub_socket.close()
                # Replicar para outros servidores
                replicar_para_outros_servidores({"opcao": "publish", "dados": dados}, OUTROS_SERVIDORES)
            except Exception as e:
                reply = {
                    "msg": f"ERRO: {e}",
                    "clock": relogio.tick(),
                    "timestamp": time.time()
                }
                print(f"[S] - Falha ao publicar mensagem: {e}", flush=True)

        # FEITO
        case "message":
            try:
                user = dados.get("user")
                receptor = dados.get("receptor")
                message = dados.get("message")
                timestamp = dados.get("timestamp")
                pub_msg = {
                    "user": user,
                    "receptor": receptor,
                    "message": message,
                    "timestamp": timestamp,
                    "clock": relogio.get()
                }
                pub_socket = context.socket(zmq.PUB)
                pub_socket.bind(f"tcp://*:{PUB_PORT}")
                pub_socket.send(msgpack.packb(pub_msg))
                reply = {
                    "msg": f"Mensagem privada enviada para o usuário: {receptor}",
                    "clock": relogio.tick(),
                    "timestamp": time.time()
                }
                print(f"[P] - Mensagem publicada para publisher: {pub_msg}", flush=True)
                pub_socket.close()
                # Replicar para outros servidores
                replicar_para_outros_servidores({"opcao": "message", "dados": dados}, OUTROS_SERVIDORES)
            except Exception as e:
                reply = {
                    "msg": f"ERRO: {e}",
                    "clock": relogio.tick(),
                    "timestamp": time.time()
                }
                print(f"[P] - Falha ao publicar mensagem: {e}", flush=True)
    
        case _ :
            reply = {
                "msg": "ERRO: função não encontrada",
                "clock": relogio.tick(),
                "timestamp": time.time()
            }

    # Envia resposta usando MessagePack
    socket.send(msgpack.packb(reply))
