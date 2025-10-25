import zmq
import json
import time
import threading
import sys
from logical_clock import LogicalClock
from berkeley_sync import BerkeleySynchronizer

class Server:
    def __init__(self, server_name, broker_port=5559, proxy_port=5560):
        self.server_name = server_name
        self.clock = LogicalClock()
        self.synchronizer = BerkeleySynchronizer(server_name)
        
        # Socket para comunicação com broker
        self.broker_context = zmq.Context()
        self.broker_socket = self.broker_context.socket(zmq.REP)
        self.broker_socket.bind(f"tcp://*:{broker_port}")
        
        # Socket para pub (envio de mensagens para proxy)
        self.pub_context = zmq.Context()
        self.pub_socket = self.pub_context.socket(zmq.PUB)
        self.pub_socket.bind(f"tcp://*:{proxy_port}")
        
        # Thread para processar mensagens do broker
        self.broker_thread = threading.Thread(target=self._handle_broker_messages, daemon=True)
        self.broker_thread.start()
        
        print(f"Servidor {server_name} iniciado")
    
    def _handle_broker_messages(self):
        """Processa mensagens vindas do broker"""
        while True:
            try:
                # Recebe mensagem do broker
                message = self.broker_socket.recv_json()
                self.clock.update(message.get("clock", 0))
                
                # Processa a mensagem
                response = self._process_message(message)
                
                # Envia resposta para o broker
                response["timestamp"] = self.clock.get_timestamp()
                response["clock"] = self.clock.increment()
                self.broker_socket.send_json(response)
                
                # Publica mensagem para o proxy
                self._publish_message(message, response)
                
                # Verifica se precisa sincronizar relógio
                self.synchronizer.process_message()
                
            except Exception as e:
                print(f"Erro ao processar mensagem do broker: {e}")
    
    def _process_message(self, message):
        """Processa uma mensagem e retorna resposta"""
        user = message.get("user", "unknown")
        content = message.get("content", "")
        
        # Simula processamento
        time.sleep(0.1)
        
        # Retorna resposta processada
        return {
            "status": "processed",
            "server": self.server_name,
            "user": user,
            "content": f"Processado por {self.server_name}: {content}",
            "physical_time": self.synchronizer.get_physical_time()
        }
    
    def _publish_message(self, original_message, response):
        """Publica mensagem processada para o proxy"""
        try:
            pub_message = {
                "type": "message_processed",
                "original": original_message,
                "response": response,
                "server": self.server_name,
                "timestamp": self.clock.get_timestamp(),
                "clock": self.clock.get_clock()
            }
            
            self.pub_socket.send_json(pub_message)
        except Exception as e:
            print(f"Erro ao publicar mensagem: {e}")
    
    def run(self):
        """Loop principal do servidor"""
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"Servidor {self.server_name} encerrado")
            self.cleanup()
    
    def cleanup(self):
        """Limpa recursos"""
        self.broker_socket.close()
        self.pub_socket.close()
        self.broker_context.term()
        self.pub_context.term()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python server.py <nome_do_servidor>")
        sys.exit(1)
    
    server_name = sys.argv[1]
    server = Server(server_name)
    server.run()
