import zmq
import json
import time
import threading
from logical_clock import LogicalClock

class ReferenceServer:
    def __init__(self, port=5555):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://*:{port}")
        
        self.clock = LogicalClock()
        self.servers = {}  # {nome: rank}
        self.server_heartbeats = {}  # {nome: timestamp}
        self.heartbeat_timeout = 30  # segundos
        
        # Thread para limpeza de servidores inativos
        self.cleanup_thread = threading.Thread(target=self._cleanup_inactive_servers, daemon=True)
        self.cleanup_thread.start()
    
    def _cleanup_inactive_servers(self):
        """Remove servidores que não enviaram heartbeat"""
        while True:
            time.sleep(10)  # Verifica a cada 10 segundos
            current_time = time.time()
            inactive_servers = []
            
            for server_name, last_heartbeat in self.server_heartbeats.items():
                if current_time - last_heartbeat > self.heartbeat_timeout:
                    inactive_servers.append(server_name)
            
            for server_name in inactive_servers:
                if server_name in self.servers:
                    del self.servers[server_name]
                if server_name in self.server_heartbeats:
                    del self.server_heartbeats[server_name]
                print(f"Servidor {server_name} removido por inatividade")
    
    def _create_response(self, data):
        """Cria resposta com timestamp e relógio lógico"""
        return {
            "timestamp": self.clock.get_timestamp(),
            "clock": self.clock.get_clock(),
            **data
        }
    
    def handle_rank_request(self, data):
        """Processa requisição de rank"""
        server_name = data.get("user")
        if not server_name:
            return {"error": "Nome do servidor não fornecido"}
        
        # Atribui rank baseado na ordem de chegada
        if server_name not in self.servers:
            self.servers[server_name] = len(self.servers) + 1
            print(f"Servidor {server_name} recebeu rank {self.servers[server_name]}")
        
        return self._create_response({
            "rank": self.servers[server_name]
        })
    
    def handle_list_request(self, data):
        """Processa requisição de lista de servidores"""
        server_list = [{"name": name, "rank": rank} for name, rank in self.servers.items()]
        return self._create_response({
            "list": server_list
        })
    
    def handle_heartbeat(self, data):
        """Processa heartbeat de servidor"""
        server_name = data.get("user")
        if not server_name:
            return {"error": "Nome do servidor não fornecido"}
        
        # Atualiza timestamp do heartbeat
        self.server_heartbeats[server_name] = time.time()
        
        return self._create_response({})
    
    def run(self):
        """Loop principal do servidor de referência"""
        print("Servidor de referência iniciado na porta 5555")
        
        while True:
            try:
                # Recebe mensagem
                message = self.socket.recv_json()
                self.clock.update(message.get("clock", 0))
                
                service = message.get("service")
                data = message.get("data", {})
                
                # Processa requisição baseada no serviço
                if service == "rank":
                    response = self.handle_rank_request(data)
                elif service == "list":
                    response = self.handle_list_request(data)
                elif service == "heartbeat":
                    response = self.handle_heartbeat(data)
                else:
                    response = {"error": f"Serviço desconhecido: {service}"}
                
                # Envia resposta
                self.socket.send_json(response)
                
            except Exception as e:
                print(f"Erro no servidor de referência: {e}")

if __name__ == "__main__":
    server = ReferenceServer()
    server.run()
