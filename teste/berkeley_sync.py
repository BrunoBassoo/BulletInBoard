import time
import threading
import zmq
import json
from logical_clock import LogicalClock

class BerkeleySynchronizer:
    def __init__(self, server_name, reference_port=5555):
        self.server_name = server_name
        self.clock = LogicalClock()
        self.physical_clock = time.time()
        self.coordinator = None
        self.is_coordinator = False
        self.servers = []
        self.message_count = 0
        self.sync_interval = 10  # sincroniza a cada 10 mensagens
        
        # Socket para comunicação com servidor de referência
        self.ref_context = zmq.Context()
        self.ref_socket = self.ref_context.socket(zmq.REQ)
        self.ref_socket.connect(f"tcp://reference_server:{reference_port}")
        
        # Socket para comunicação entre servidores
        self.server_context = zmq.Context()
        self.server_socket = self.server_context.socket(zmq.REP)
        self.server_socket.bind(f"tcp://*:5556")
        
        # Socket para pub/sub
        self.pub_context = zmq.Context()
        self.pub_socket = self.pub_context.socket(zmq.PUB)
        self.pub_socket.bind("tcp://*:5557")
        
        # Socket para sub
        self.sub_context = zmq.Context()
        self.sub_socket = self.sub_context.socket(zmq.SUB)
        self.sub_socket.connect("tcp://proxy:5558")
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, b"servers")
        
        # Threads
        self.server_thread = threading.Thread(target=self._handle_server_requests, daemon=True)
        self.sub_thread = threading.Thread(target=self._handle_subscriptions, daemon=True)
        self.heartbeat_thread = threading.Thread(target=self._send_heartbeat, daemon=True)
        
        self.server_thread.start()
        self.sub_thread.start()
        self.heartbeat_thread.start()
    
    def _send_heartbeat(self):
        """Envia heartbeat para o servidor de referência"""
        while True:
            try:
                time.sleep(5)  # Envia a cada 5 segundos
                self._request_rank()
            except Exception as e:
                print(f"Erro no heartbeat: {e}")
    
    def _request_rank(self):
        """Solicita rank do servidor de referência"""
        try:
            request = {
                "service": "heartbeat",
                "data": {
                    "user": self.server_name,
                    "timestamp": self.clock.get_timestamp(),
                    "clock": self.clock.increment()
                }
            }
            self.ref_socket.send_json(request)
            response = self.ref_socket.recv_json()
            self.clock.update(response.get("clock", 0))
        except Exception as e:
            print(f"Erro ao enviar heartbeat: {e}")
    
    def _get_server_list(self):
        """Obtém lista de servidores do servidor de referência"""
        try:
            request = {
                "service": "list",
                "data": {
                    "timestamp": self.clock.get_timestamp(),
                    "clock": self.clock.increment()
                }
            }
            self.ref_socket.send_json(request)
            response = self.ref_socket.recv_json()
            self.clock.update(response.get("clock", 0))
            
            if "list" in response:
                self.servers = response["list"]
                return True
            return False
        except Exception as e:
            print(f"Erro ao obter lista de servidores: {e}")
            return False
    
    def _handle_server_requests(self):
        """Processa requisições de outros servidores"""
        while True:
            try:
                message = self.server_socket.recv_json()
                self.clock.update(message.get("clock", 0))
                
                service = message.get("service")
                data = message.get("data", {})
                
                if service == "clock":
                    response = self._handle_clock_request(data)
                elif service == "election":
                    response = self._handle_election_request(data)
                else:
                    response = {"error": f"Serviço desconhecido: {service}"}
                
                response["timestamp"] = self.clock.get_timestamp()
                response["clock"] = self.clock.increment()
                self.server_socket.send_json(response)
                
            except Exception as e:
                print(f"Erro ao processar requisição de servidor: {e}")
    
    def _handle_clock_request(self, data):
        """Processa requisição de sincronização de relógio"""
        return {
            "time": self.physical_clock,
            "coordinator": self.coordinator
        }
    
    def _handle_election_request(self, data):
        """Processa requisição de eleição"""
        return {"election": "OK"}
    
    def _handle_subscriptions(self):
        """Processa mensagens do tópico servers"""
        while True:
            try:
                topic, message = self.sub_socket.recv_multipart()
                if topic == b"servers":
                    data = json.loads(message)
                    self.clock.update(data.get("clock", 0))
                    
                    if data.get("service") == "election":
                        new_coordinator = data.get("data", {}).get("coordinator")
                        if new_coordinator and new_coordinator != self.coordinator:
                            self.coordinator = new_coordinator
                            self.is_coordinator = (new_coordinator == self.server_name)
                            print(f"Novo coordenador: {self.coordinator}")
            except Exception as e:
                print(f"Erro ao processar subscription: {e}")
    
    def synchronize_clock(self):
        """Sincroniza relógio usando algoritmo de Berkeley"""
        if not self.is_coordinator:
            return
        
        if not self._get_server_list():
            return
        
        # Coleta tempos dos servidores
        server_times = []
        for server in self.servers:
            if server["name"] != self.server_name:
                try:
                    # Conecta ao servidor
                    context = zmq.Context()
                    socket = context.socket(zmq.REQ)
                    socket.connect(f"tcp://server_{server['name']}:5556")
                    socket.setsockopt(zmq.RCVTIMEO, 2000)  # 2 segundos timeout
                    
                    request = {
                        "service": "clock",
                        "data": {
                            "timestamp": self.clock.get_timestamp(),
                            "clock": self.clock.increment()
                        }
                    }
                    socket.send_json(request)
                    response = socket.recv_json()
                    self.clock.update(response.get("clock", 0))
                    
                    server_times.append({
                        "name": server["name"],
                        "time": response.get("time", 0)
                    })
                    
                    socket.close()
                    context.term()
                except Exception as e:
                    print(f"Erro ao sincronizar com {server['name']}: {e}")
        
        # Adiciona próprio tempo
        server_times.append({
            "name": self.server_name,
            "time": self.physical_clock
        })
        
        # Calcula tempo médio
        if server_times:
            avg_time = sum(s["time"] for s in server_times) / len(server_times)
            adjustment = avg_time - self.physical_clock
            
            # Ajusta relógio físico
            self.physical_clock += adjustment
            print(f"Ajuste de relógio: {adjustment:.3f}s")
    
    def start_election(self):
        """Inicia processo de eleição"""
        if not self._get_server_list():
            return
        
        # Envia requisições de eleição para servidores com rank maior
        current_rank = next((s["rank"] for s in self.servers if s["name"] == self.server_name), 0)
        
        for server in self.servers:
            if server["rank"] > current_rank:
                try:
                    context = zmq.Context()
                    socket = context.socket(zmq.REQ)
                    socket.connect(f"tcp://server_{server['name']}:5556")
                    socket.setsockopt(zmq.RCVTIMEO, 2000)
                    
                    request = {
                        "service": "election",
                        "data": {
                            "timestamp": self.clock.get_timestamp(),
                            "clock": self.clock.increment()
                        }
                    }
                    socket.send_json(request)
                    response = socket.recv_json()
                    self.clock.update(response.get("clock", 0))
                    
                    socket.close()
                    context.term()
                    
                    # Se recebeu resposta, não é coordenador
                    return
                except Exception as e:
                    print(f"Erro na eleição com {server['name']}: {e}")
        
        # Se chegou aqui, é o coordenador
        self.is_coordinator = True
        self.coordinator = self.server_name
        
        # Anuncia como coordenador
        message = {
            "service": "election",
            "data": {
                "coordinator": self.server_name,
                "timestamp": self.clock.get_timestamp(),
                "clock": self.clock.increment()
            }
        }
        self.pub_socket.send_multipart([b"servers", json.dumps(message).encode()])
        print(f"Eleito como coordenador: {self.server_name}")
    
    def check_coordinator(self):
        """Verifica se o coordenador está ativo"""
        if not self.coordinator:
            return False
        
        try:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect(f"tcp://server_{self.coordinator}:5556")
            socket.setsockopt(zmq.RCVTIMEO, 2000)
            
            request = {
                "service": "clock",
                "data": {
                    "timestamp": self.clock.get_timestamp(),
                    "clock": self.clock.increment()
                }
            }
            socket.send_json(request)
            response = socket.recv_json()
            self.clock.update(response.get("clock", 0))
            
            socket.close()
            context.term()
            return True
        except Exception as e:
            print(f"Coordenador {self.coordinator} não está ativo: {e}")
            return False
    
    def process_message(self):
        """Processa uma mensagem e verifica se precisa sincronizar"""
        self.message_count += 1
        
        # Sincroniza a cada sync_interval mensagens
        if self.message_count % self.sync_interval == 0:
            if not self.check_coordinator():
                self.start_election()
            else:
                self.synchronize_clock()
    
    def get_physical_time(self):
        """Retorna tempo físico atual"""
        return self.physical_clock
