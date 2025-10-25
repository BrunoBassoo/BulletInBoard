import zmq
import json
import time
import threading
import random
from logical_clock import LogicalClock

class Broker:
    def __init__(self, port=5559):
        self.clock = LogicalClock()
        self.context = zmq.Context()
        
        # Socket para receber mensagens de clientes
        self.client_socket = self.context.socket(zmq.REP)
        self.client_socket.bind(f"tcp://*:{port}")
        
        # Sockets para comunicação com servidores
        self.server_sockets = {}
        self.server_ports = {
            "server1": 5561,
            "server2": 5562, 
            "server3": 5563
        }
        
        # Conecta aos servidores
        for server_name, port in self.server_ports.items():
            socket = self.context.socket(zmq.REQ)
            socket.connect(f"tcp://{server_name}:{port}")
            self.server_sockets[server_name] = socket
        
        # Thread para processar mensagens
        self.thread = threading.Thread(target=self._handle_messages, daemon=True)
        self.thread.start()
        
        print("Broker iniciado")
    
    def _handle_messages(self):
        """Processa mensagens de clientes"""
        while True:
            try:
                # Recebe mensagem do cliente
                message = self.client_socket.recv_json()
                self.clock.update(message.get("clock", 0))
                
                # Seleciona servidor aleatoriamente
                server_name = random.choice(list(self.server_sockets.keys()))
                server_socket = self.server_sockets[server_name]
                
                # Envia mensagem para o servidor
                message["timestamp"] = self.clock.get_timestamp()
                message["clock"] = self.clock.increment()
                server_socket.send_json(message)
                
                # Recebe resposta do servidor
                response = server_socket.recv_json()
                self.clock.update(response.get("clock", 0))
                
                # Envia resposta para o cliente
                response["timestamp"] = self.clock.get_timestamp()
                response["clock"] = self.clock.increment()
                self.client_socket.send_json(response)
                
            except Exception as e:
                print(f"Erro no broker: {e}")
                # Envia erro para o cliente
                error_response = {
                    "status": "error",
                    "message": str(e),
                    "timestamp": self.clock.get_timestamp(),
                    "clock": self.clock.increment()
                }
                self.client_socket.send_json(error_response)
    
    def run(self):
        """Loop principal do broker"""
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Broker encerrado")
            self.cleanup()
    
    def cleanup(self):
        """Limpa recursos"""
        for socket in self.server_sockets.values():
            socket.close()
        self.client_socket.close()
        self.context.term()

if __name__ == "__main__":
    broker = Broker()
    broker.run()
