import zmq
import json
import time
import threading
from logical_clock import LogicalClock

class Proxy:
    def __init__(self, sub_port=5557, pub_port=5558):
        self.clock = LogicalClock()
        self.context = zmq.Context()
        
        # Socket para receber mensagens dos servidores
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.bind(f"tcp://*:{sub_port}")
        
        # Socket para enviar mensagens para clientes
        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.bind(f"tcp://*:{pub_port}")
        
        # Conecta aos servidores
        server_ports = [5564, 5565, 5566]  # Portas pub dos servidores
        for port in server_ports:
            self.sub_socket.connect(f"tcp://server1:{port}")
            self.sub_socket.connect(f"tcp://server2:{port}")
            self.sub_socket.connect(f"tcp://server3:{port}")
        
        # Thread para processar mensagens
        self.thread = threading.Thread(target=self._handle_messages, daemon=True)
        self.thread.start()
        
        print("Proxy iniciado")
    
    def _handle_messages(self):
        """Processa mensagens dos servidores e repassa para clientes"""
        while True:
            try:
                # Recebe mensagem dos servidores
                message = self.sub_socket.recv_json()
                self.clock.update(message.get("clock", 0))
                
                # Repassa mensagem para clientes
                message["proxy_timestamp"] = self.clock.get_timestamp()
                message["proxy_clock"] = self.clock.increment()
                
                # Publica para tópico "messages"
                self.pub_socket.send_multipart([b"messages", json.dumps(message).encode()])
                
            except Exception as e:
                print(f"Erro no proxy: {e}")
    
    def run(self):
        """Loop principal do proxy"""
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Proxy encerrado")
            self.cleanup()
    
    def cleanup(self):
        """Limpa recursos"""
        self.sub_socket.close()
        self.pub_socket.close()
        self.context.term()

if __name__ == "__main__":
    proxy = Proxy()
    proxy.run()
