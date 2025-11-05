import zmq
from datetime import datetime
import sys
import msgpack
import threading
import time

# Classe do relógio lógico
class RelogioLogico:
    def __init__(self):
        self.clock = 0
        self.lock = threading.Lock()
    
    def tick(self):
        with self.lock:
            self.clock += 1
            return self.clock
    
    def update(self, clock_recebido):
        with self.lock:
            self.clock = max(self.clock, clock_recebido)
            return self.clock
    
    def get(self):
        with self.lock:
            return self.clock

class Cliente:
    def __init__(self):
        self.relogio = RelogioLogico()
        self.nome_usuario = None
        self.canais_inscritos = []
        
        # Socket REQ para comunicação com broker
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://broker:5555")
        
        # Socket SUB para receber mensagens do proxy
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect("tcp://proxy:5558")
        
        # Thread para receber mensagens
        self.running = True
        self.receiver_thread = threading.Thread(target=self.receber_mensagens, daemon=True)
        self.receiver_thread.start()
        
        print("[CLIENTE] Subscriber iniciado em thread separada", flush=True)
    
    def inscrever_topico(self, topico):
        """Inscreve em um tópico específico"""
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, topico)
        print(f"[CLIENTE] Inscrito no tópico: {topico}", flush=True)
    
    def receber_mensagens(self):
        """Thread que recebe mensagens do proxy via subscriber"""
        print("[CLIENTE] Aguardando mensagens...", flush=True)
        
        while self.running:
            try:
                # Recebe mensagem com tópico
                topic, mensagem_data = self.sub_socket.recv_multipart()
                topic_str = topic.decode('utf-8')
                mensagem = msgpack.unpackb(mensagem_data, raw=False)
                
                # Atualiza relógio lógico
                if "clock" in mensagem:
                    self.relogio.update(mensagem["clock"])
                
                if "channel" in mensagem:
                    print(f"\n[{mensagem['channel']}] {mensagem['user']}: {mensagem['message']}", flush=True)
                    print(f"   [Clock: {mensagem.get('clock', 'N/A')} | {datetime.fromtimestamp(mensagem.get('timestamp', 0)).strftime('%H:%M:%S')}]", flush=True)
                elif "dst" in mensagem:
                    print(f"\nMensagem privada de {mensagem['src']}: {mensagem['message']}", flush=True)
                    print(f"   [Clock: {mensagem.get('clock', 'N/A')} | {datetime.fromtimestamp(mensagem.get('timestamp', 0)).strftime('%H:%M:%S')}]", flush=True)
                elif "coordinator" in mensagem.get("data", {}):
                    print(f"\nNovo coordenador eleito: {mensagem['data']['coordinator']}", flush=True)
                
            except Exception as e:
                if self.running:
                    print(f"\n[CLIENTE] Erro ao receber mensagem: {e}", flush=True)
                time.sleep(0.5)
    
    def enviar_request(self, service, data):
        """Envia requisição e recebe resposta"""
        try:
            # Incrementa relógio antes de enviar
            data["clock"] = self.relogio.tick()
            
            request = {
                "service": service,
                "data": data
            }
            
            self.socket.send(msgpack.packb(request))
            reply_data = self.socket.recv()
            reply = msgpack.unpackb(reply_data, raw=False)
            
            # Atualiza relógio lógico ao receber
            if "data" in reply and "clock" in reply["data"]:
                self.relogio.update(reply["data"]["clock"])
            
            return reply
        except Exception as e:
            print(f"Erro ao enviar requisição: {e}", flush=True)
            return None
    
    def menu(self):
        """Exibe o menu principal"""
        print("\n" + "="*50)
        print("Bem-vindo ao BulletInBoard!")
        print("="*50)
        print("Opções disponíveis:")
        print("[1] - Login")
        print("[2] - Listar usuários")
        print("[3] - Cadastrar canal")
        print("[4] - Listar canais")
        print("[5] - Inscrever em canal")
        print("[6] - Publicar mensagem em um canal")
        print("[7] - Enviar mensagem privada para usuário")
        print("[0] - Sair do programa")
        print("-" * 50)
    
    def executar(self):
        """Loop principal do cliente"""
        self.menu()
        
        while True:
            try:
                opcao = input("\nEntre com a opção: ").strip()
                
                # FEITO
                if opcao == "0":
                    print("Encerrando o programa...")
                    self.running = False
                    break
                    
                # FEITO
                if opcao == "1":
                    print("\n------ Login ------")
                    user = input("Entre com o seu usuário: ")
                    
                    data = {
                        "user": user,
                        "timestamp": datetime.now().timestamp()
                    }
                    
                    reply = self.enviar_request("login", data)
                    if reply and reply.get("data", {}).get("status") == "OK":
                        self.nome_usuario = user
                        # Inscreve no tópico do próprio nome para receber mensagens privadas
                        self.inscrever_topico(user)
                        print(f"Login realizado com sucesso! [Clock: {reply['data'].get('clock')}]")
                    else:
                        print(f"Erro no login: {reply.get('data', {}).get('message', 'Erro desconhecido')}")

                # FEITO
                elif opcao == "2":
                    print("\n------ Listar usuários ------")
                    data = {"timestamp": datetime.now().timestamp()}
                    
                    reply = self.enviar_request("listar", data)
                    if reply and reply.get("data", {}).get("status") == "OK":
                        users = reply["data"].get("users", [])
                        print(f"Usuários cadastrados: {', '.join(users) if users else 'Nenhum'}")
                        print(f"   [Clock: {reply['data'].get('clock')}]")
                    else:
                        print(f"Erro ao listar: {reply.get('data', {}).get('message', 'Erro desconhecido')}")

                # FEITO
                elif opcao == "3":
                    print("\n------ Cadastrar canal ------")
                    canal = input("Entre com o nome do canal: ")
                    
                    data = {
                        "canal": canal,
                        "timestamp": datetime.now().timestamp()
                    }
                    
                    reply = self.enviar_request("cadastrarCanal", data)
                    if reply and reply.get("data", {}).get("status") == "OK":
                        print(f"Canal '{canal}' cadastrado com sucesso! [Clock: {reply['data'].get('clock')}]")
                    else:
                        print(f" Erro ao cadastrar canal: {reply.get('data', {}).get('message', 'Erro desconhecido')}")

                # FEITO
                elif opcao == "4":
                    print("\n------ Listar canais ------")
                    data = {"timestamp": datetime.now().timestamp()}
                    
                    reply = self.enviar_request("listarCanal", data)
                    if reply and reply.get("data", {}).get("status") == "OK":
                        channels = reply["data"].get("channels", [])
                        print(f"Canais disponíveis: {', '.join(channels) if channels else 'Nenhum'}")
                        print(f"   [Clock: {reply['data'].get('clock')}]")
                    else:
                        print(f"Erro ao listar canais: {reply.get('data', {}).get('message', 'Erro desconhecido')}")

                # FEITO
                elif opcao == "5":
                    print("\n------ Inscrever em canal ------")
                    canal = input("Entre com o nome do canal: ")
                    self.inscrever_topico(canal)
                    self.canais_inscritos.append(canal)
                    print(f"Inscrito no canal '{canal}' com sucesso!")

                # FEITO
                elif opcao == "6":
                    print("\n------ Publicar mensagem em canal ------")
                    
                    if not self.nome_usuario:
                        print("Você precisa fazer login primeiro!")
                        continue
                    
                    nome_do_canal = input("Entre com o nome do canal: ")
                    mensagem = input("Entre com a mensagem: ")
                    
                    data = {
                        "user": self.nome_usuario,
                        "channel": nome_do_canal,
                        "message": mensagem,
                        "timestamp": datetime.now().timestamp()
                    }
                    
                    reply = self.enviar_request("publish", data)
                    if reply and reply.get("data", {}).get("status") == "OK":
                        print(f"Mensagem publicada no canal '{nome_do_canal}'! [Clock: {reply['data'].get('clock')}]")
                    else:
                        print(f"Erro: {reply.get('data', {}).get('message', 'Erro desconhecido')}")

                # FEITO
                elif opcao == "7":
                    print("\n------ Enviar mensagem privada ------")
                    
                    if not self.nome_usuario:
                        print("Você precisa fazer login primeiro!")
                        continue
                    
                    nome_do_receptor = input("Entre com o nome do receptor: ")
                    mensagem = input("Entre com a mensagem: ")
                    
                    data = {
                        "src": self.nome_usuario,
                        "dst": nome_do_receptor,
                        "message": mensagem,
                        "timestamp": datetime.now().timestamp()
                    }
                    
                    reply = self.enviar_request("message", data)
                    if reply and reply.get("data", {}).get("status") == "OK":
                        print(f"Mensagem enviada para '{nome_do_receptor}'! [Clock: {reply['data'].get('clock')}]")
                    else:
                        print(f" Erro: {reply.get('data', {}).get('message', 'Erro desconhecido')}")
                
                else:
                    print("Opção inválida! Tente novamente.")
                    
            except KeyboardInterrupt:
                print("\n\nEncerrando o programa...")
                self.running = False
                break
            except Exception as e:
                print(f"Erro: {e}", flush=True)
        
        # Cleanup
        self.sub_socket.close()
        self.socket.close()
        self.context.term()

if __name__ == "__main__":
    cliente = Cliente()
    cliente.executar()
