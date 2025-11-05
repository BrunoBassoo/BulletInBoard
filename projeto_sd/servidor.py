import threading
import zmq
import msgpack
import time
import os
import socket as sock

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

# Função para salvar mensagens no arquivo de log
def salvar_log(mensagem):
    try:
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(f"{mensagem}\n")
    except Exception as e:
        print(f"Erro ao salvar no log: {e}", flush=True)

class Servidor:
    def __init__(self):
        # Nome único do servidor baseado no hostname
        self.nome = sock.gethostname()
        self.rank = None
        self.coordenador = None
        self.lista_servidores = []
        self.relogio = RelogioLogico()
        self.mensagens_processadas = 0
        
        # Dados locais
        self.usuarios = dict()
        self.canais = dict()
        self.cont = 0
        
        # Contexto ZMQ
        self.context = zmq.Context()
        
        # Socket REP para broker (recebe requisições de clientes)
        self.socket = self.context.socket(zmq.REP)
        self.socket.connect("tcp://broker:5556")
        
        # Socket PUB para publicar mensagens (envia para publisher intermediário)
        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.connect("tcp://publisher:5559")
        
        # Socket REQ para comunicação com servidor de referência
        self.ref_socket = self.context.socket(zmq.REQ)
        self.ref_socket.connect("tcp://referencia:5560")
        
        # Socket REP para comunicação entre servidores
        self.server_socket = self.context.socket(zmq.REP)
        self.server_socket.bind("tcp://*:5561")
        
        print(f"[{self.nome}] Servidor iniciado!", flush=True)
        
        # Registra no servidor de referência e obtém rank
        self.obter_rank()
        
        # Inicia threads auxiliares
        self.running = True
        self.heartbeat_thread = threading.Thread(target=self.enviar_heartbeat, daemon=True)
        self.heartbeat_thread.start()
        
        self.server_comm_thread = threading.Thread(target=self.handle_server_communication, daemon=True)
        self.server_comm_thread.start()
        
        # Atualiza lista de servidores
        self.atualizar_lista_servidores()
        
        # Define coordenador inicial como o de menor rank
        if self.lista_servidores:
            self.coordenador = min(self.lista_servidores, key=lambda x: x["rank"])["name"]
            print(f"[{self.nome}] Coordenador inicial: {self.coordenador}", flush=True)
    
    def obter_rank(self):
        """Obtém rank do servidor de referência"""
        try:
            request = {
                "service": "rank",
                "data": {
                    "user": self.nome,
                    "timestamp": time.time(),
                    "clock": self.relogio.tick()
                }
            }
            
            self.ref_socket.send(msgpack.packb(request))
            reply_data = self.ref_socket.recv()
            reply = msgpack.unpackb(reply_data, raw=False)
            
            if "clock" in reply.get("data", {}):
                self.relogio.update(reply["data"]["clock"])
            
            self.rank = reply["data"]["rank"]
            print(f"[{self.nome}] Rank obtido: {self.rank}", flush=True)
            
        except Exception as e:
            print(f"[{self.nome}] Erro ao obter rank: {e}", flush=True)
            self.rank = 999  # Rank padrão em caso de erro
    
    def enviar_heartbeat(self):
        """Envia heartbeat periodicamente ao servidor de referência"""
        time.sleep(5)  # Aguarda inicialização
        
        while self.running:
            try:
                request = {
                    "service": "heartbeat",
                    "data": {
                        "user": self.nome,
                        "timestamp": time.time(),
                        "clock": self.relogio.tick()
                    }
                }
                
                # Cria socket temporário para heartbeat (evita conflito)
                temp_socket = self.context.socket(zmq.REQ)
                temp_socket.connect("tcp://referencia:5560")
                temp_socket.send(msgpack.packb(request))
                temp_socket.recv()  # Recebe confirmação
                temp_socket.close()
                
            except Exception as e:
                print(f"[{self.nome}] Erro ao enviar heartbeat: {e}", flush=True)
            
            time.sleep(15)  # Envia a cada 15 segundos
    
    def atualizar_lista_servidores(self):
        """Obtém lista de servidores ativos do servidor de referência"""
        try:
            request = {
                "service": "list",
                "data": {
                    "timestamp": time.time(),
                    "clock": self.relogio.tick()
                }
            }
            
            # Cria socket temporário
            temp_socket = self.context.socket(zmq.REQ)
            temp_socket.connect("tcp://referencia:5560")
            temp_socket.send(msgpack.packb(request))
            reply_data = temp_socket.recv()
            temp_socket.close()
            
            reply = msgpack.unpackb(reply_data, raw=False)
            
            if "clock" in reply.get("data", {}):
                self.relogio.update(reply["data"]["clock"])
            
            self.lista_servidores = reply["data"]["list"]
            print(f"[{self.nome}] Lista de servidores atualizada: {self.lista_servidores}", flush=True)
            
        except Exception as e:
            print(f"[{self.nome}] Erro ao atualizar lista de servidores: {e}", flush=True)
    
    def sincronizar_relogio(self):
        """Sincroniza relógio com o coordenador usando algoritmo de Berkeley"""
        if not self.coordenador or self.coordenador == self.nome:
            # Se sou o coordenador, não preciso sincronizar
            return
        
        try:
            # Solicita horário do coordenador
            request = {
                "service": "clock",
                "data": {
                    "timestamp": time.time(),
                    "clock": self.relogio.tick()
                }
            }
            
            # Cria socket temporário para comunicação com outro servidor
            temp_socket = self.context.socket(zmq.REQ)
            temp_socket.setsockopt(zmq.RCVTIMEO, 5000)  # Timeout de 5 segundos
            temp_socket.connect(f"tcp://{self.coordenador}:5561")
            
            tempo_envio = time.time()
            temp_socket.send(msgpack.packb(request))
            reply_data = temp_socket.recv()
            tempo_recebimento = time.time()
            temp_socket.close()
            
            reply = msgpack.unpackb(reply_data, raw=False)
            
            if "clock" in reply.get("data", {}):
                self.relogio.update(reply["data"]["clock"])
            
            # Calcula ajuste de tempo (Berkeley simplificado)
            tempo_coordenador = reply["data"]["time"]
            rtt = tempo_recebimento - tempo_envio
            tempo_estimado_coordenador = tempo_coordenador + (rtt / 2)
            
            # Aplica ajuste (simplificado - apenas log)
            diferenca = tempo_estimado_coordenador - time.time()
            print(f"[{self.nome}] Sincronização: diferença de {diferenca:.3f}s com coordenador", flush=True)
            
        except zmq.error.Again:
            print(f"[{self.nome}] Timeout ao sincronizar com coordenador - iniciando eleição", flush=True)
            self.iniciar_eleicao()
        except Exception as e:
            print(f"[{self.nome}] Erro ao sincronizar relógio: {e}", flush=True)
    
    def iniciar_eleicao(self):
        """Inicia processo de eleição de novo coordenador"""
        print(f"[{self.nome}] Iniciando eleição...", flush=True)
        
        # Atualiza lista de servidores
        self.atualizar_lista_servidores()
        
        # Encontra servidores com rank maior
        servidores_maiores = [s for s in self.lista_servidores if s["rank"] > self.rank]
        
        recebeu_ok = False
        for servidor in servidores_maiores:
            try:
                request = {
                    "service": "election",
                    "data": {
                        "timestamp": time.time(),
                        "clock": self.relogio.tick()
                    }
                }
                
                temp_socket = self.context.socket(zmq.REQ)
                temp_socket.setsockopt(zmq.RCVTIMEO, 3000)
                temp_socket.connect(f"tcp://{servidor['name']}:5561")
                temp_socket.send(msgpack.packb(request))
                reply_data = temp_socket.recv()
                temp_socket.close()
                
                reply = msgpack.unpackb(reply_data, raw=False)
                if reply["data"].get("election") == "OK":
                    recebeu_ok = True
                    print(f"[{self.nome}] Servidor {servidor['name']} respondeu OK à eleição", flush=True)
                    
            except Exception as e:
                print(f"[{self.nome}] Servidor {servidor['name']} não respondeu: {e}", flush=True)
        
        # Se não recebeu OK de ninguém maior, torna-se coordenador
        if not recebeu_ok:
            self.tornar_coordenador()
    
    def tornar_coordenador(self):
        """Torna-se o coordenador e avisa outros servidores"""
        self.coordenador = self.nome
        print(f"[{self.nome}] ⭐ Eleito como COORDENADOR!", flush=True)
        
        # Publica no tópico servers
        msg = {
            "service": "election",
            "data": {
                "coordinator": self.nome,
                "timestamp": time.time(),
                "clock": self.relogio.tick()
            }
        }
        
        self.pub_socket.send(msgpack.packb(msg))
        print(f"[{self.nome}] Anúncio de coordenador publicado", flush=True)
    
    def handle_server_communication(self):
        """Thread para lidar com comunicação entre servidores"""
        while self.running:
            try:
                request_data = self.server_socket.recv()
                request = msgpack.unpackb(request_data, raw=False)
                
                service = request.get("service")
                data = request.get("data", {})
                
                # Atualiza relógio lógico
                if "clock" in data:
                    self.relogio.update(data["clock"])
                
                if service == "clock":
                    # Responde com horário atual
                    reply = {
                        "service": "clock",
                        "data": {
                            "time": time.time(),
                            "timestamp": time.time(),
                            "clock": self.relogio.tick()
                        }
                    }
                    self.server_socket.send(msgpack.packb(reply))
                    
                elif service == "election":
                    # Responde OK e inicia própria eleição
                    reply = {
                        "service": "election",
                        "data": {
                            "election": "OK",
                            "timestamp": time.time(),
                            "clock": self.relogio.tick()
                        }
                    }
                    self.server_socket.send(msgpack.packb(reply))
                    
                    # Inicia própria eleição
                    threading.Thread(target=self.iniciar_eleicao, daemon=True).start()
                
                else:
                    # Serviço desconhecido
                    reply = {
                        "service": "error",
                        "data": {
                            "msg": "Serviço desconhecido",
                            "timestamp": time.time(),
                            "clock": self.relogio.tick()
                        }
                    }
                    self.server_socket.send(msgpack.packb(reply))
                    
            except Exception as e:
                print(f"[{self.nome}] Erro na comunicação entre servidores: {e}", flush=True)
    
    def processar_cliente(self):
        """Loop principal para processar requisições de clientes"""
        while self.running:
            try:
                # Recebe mensagem serializada com MessagePack
                request_data = self.socket.recv()
                request = msgpack.unpackb(request_data, raw=False)
                opcao = request.get("opcao")
                dados = request.get("dados")
                
                # Salva a mensagem recebida no log
                salvar_log(f"[{time.time()}] Opcao: {opcao} | Dados: {dados}")
                
                # Atualiza relógio lógico ao receber
                if dados and "clock" in dados:
                    self.relogio.update(dados["clock"])
                
                # Processa opção
                reply = self.processar_opcao(opcao, dados)
                
                # Envia resposta usando MessagePack
                self.socket.send(msgpack.packb(reply))
                
                # Incrementa contador de mensagens
                self.mensagens_processadas += 1
                
                # Sincroniza relógio a cada 10 mensagens
                if self.mensagens_processadas % 10 == 0:
                    print(f"[{self.nome}] Sincronizando relógio (10 mensagens processadas)...", flush=True)
                    threading.Thread(target=self.sincronizar_relogio, daemon=True).start()
                
            except Exception as e:
                print(f"[{self.nome}] Erro ao processar cliente: {e}", flush=True)
    
    def canal_existe(self, nome_canal):
        """Verifica se um canal existe"""
        for canal_data in self.canais.values():
            if canal_data.get('canal') == nome_canal:
                return True
        return False
    
    def usuario_existe(self, nome_usuario):
        """Verifica se um usuário existe"""
        for user_data in self.usuarios.values():
            if user_data.get('user') == nome_usuario:
                return True
        return False
    
    def processar_opcao(self, opcao, dados):
        """Processa uma opção de requisição"""
        if opcao == "login":
            self.usuarios[self.cont] = dados
            self.cont += 1
            reply = {
                "msg": "OK",
                "clock": self.relogio.tick(),
                "timestamp": time.time()
            }
            print(f"[{self.nome}] Login do {dados.get('user')} feito!", flush=True)
            
        elif opcao == "listar":
            for i in self.usuarios:
                print(f"Usuario {i}: {self.usuarios[i].get('user')} | time: {self.usuarios[i].get('time')}")
            reply = {
                "msg": "usuarios listados com sucesso",
                "clock": self.relogio.tick(),
                "timestamp": time.time()
            }
            print(f"[{self.nome}] Usuarios listados com sucesso!", flush=True)
            
        elif opcao == "cadastrarCanal":
            self.canais[self.cont] = dados
            self.cont += 1
            reply = {
                "msg": "cadastro de canal OK",
                "clock": self.relogio.tick(),
                "timestamp": time.time()
            }
            print(f"[{self.nome}] Cadastro do canal {dados.get('canal')} feito!", flush=True)
            
        elif opcao == "listarCanal":
            for i in self.canais:
                print(f"Canal {i}: {self.canais[i].get('canal')}")
            reply = {
                "msg": "lista de canais OK",
                "clock": self.relogio.tick(),
                "timestamp": time.time()
            }
            print(f"[{self.nome}] Canais listados com sucesso!", flush=True)
            
        elif opcao == "publish":
            try:
                user = dados.get("user")
                channel = dados.get("channel")
                message = dados.get("message")
                timestamp = dados.get("timestamp")
                
                # Publica no tópico do canal
                topic = channel.encode('utf-8')
                pub_msg = {
                    "user": user,
                    "channel": channel,
                    "message": message,
                    "timestamp": timestamp,
                    "clock": self.relogio.get()
                }
                # Envia com tópico
                self.pub_socket.send_multipart([topic, msgpack.packb(pub_msg)])
                
                # Salva no log
                salvar_log(f"[PUBLISH] Canal: {channel} | User: {user} | Msg: {message}")
                
                reply = {
                    "msg": f"Mensagem publicada para o canal: {channel}",
                    "clock": self.relogio.tick(),
                    "timestamp": time.time()
                }
                print(f"[{self.nome}] Mensagem publicada no canal '{channel}': {user}: {message}", flush=True)
                    
            except Exception as e:
                reply = {
                    "msg": f"ERRO: {e}",
                    "clock": self.relogio.tick(),
                    "timestamp": time.time()
                }
                print(f"[{self.nome}] Falha ao publicar mensagem: {e}", flush=True)
                
        elif opcao == "message":
            try:
                user = dados.get("user")
                receptor = dados.get("receptor")
                message = dados.get("message")
                timestamp = dados.get("timestamp")
                
                # Publica no tópico do usuário destino (receptor)
                topic = receptor.encode('utf-8')
                pub_msg = {
                    "user": user,
                    "receptor": receptor,
                    "message": message,
                    "timestamp": timestamp,
                    "clock": self.relogio.get()
                }
                # Envia com tópico
                self.pub_socket.send_multipart([topic, msgpack.packb(pub_msg)])
                
                # Salva no log
                salvar_log(f"[MESSAGE] From: {user} | To: {receptor} | Msg: {message}")
                
                reply = {
                    "msg": f"Mensagem privada enviada para o usuário: {receptor}",
                    "clock": self.relogio.tick(),
                    "timestamp": time.time()
                }
                print(f"[{self.nome}] Mensagem privada de '{user}' para '{receptor}': {message}", flush=True)
                    
            except Exception as e:
                reply = {
                    "msg": f"ERRO: {e}",
                    "clock": self.relogio.tick(),
                    "timestamp": time.time()
                }
                print(f"[{self.nome}] Falha ao enviar mensagem privada: {e}", flush=True)
                
        else:
            reply = {
                "msg": "ERRO: função não encontrada",
                "clock": self.relogio.tick(),
                "timestamp": time.time()
            }
        
        return reply

if __name__ == "__main__":
    servidor = Servidor()
    servidor.processar_cliente()
