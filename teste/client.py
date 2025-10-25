import zmq
import json
import time
import threading
import sys
from logical_clock import LogicalClock

class Client:
    def __init__(self, client_name, broker_port=5559, proxy_port=5558):
        self.client_name = client_name
        self.clock = LogicalClock()
        
        # Socket para comunicação com broker
        self.broker_context = zmq.Context()
        self.broker_socket = self.broker_context.socket(zmq.REQ)
        self.broker_socket.connect(f"tcp://broker:{broker_port}")
        
        # Socket para receber mensagens do proxy
        self.proxy_context = zmq.Context()
        self.proxy_socket = self.proxy_context.socket(zmq.SUB)
        self.proxy_socket.connect(f"tcp://proxy:{proxy_port}")
        self.proxy_socket.setsockopt(zmq.SUBSCRIBE, b"messages")
        
        # Thread para receber mensagens
        self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
        self.receive_thread.start()
        
        print(f"Cliente {client_name} iniciado")
    
    def _receive_messages(self):
        """Recebe mensagens do proxy"""
        while True:
            try:
                # Recebe mensagem do proxy
                topic, message = self.proxy_socket.recv_multipart()
                if topic == b"messages":
                    data = json.loads(message)
                    self.clock.update(data.get("clock", 0))
                    
                    # Exibe mensagem recebida
                    print(f"[{self.client_name}] Mensagem recebida:")
                    print(f"  Servidor: {data.get('server', 'unknown')}")
                    print(f"  Conteúdo: {data.get('response', {}).get('content', 'N/A')}")
                    print(f"  Relógio lógico: {data.get('clock', 0)}")
                    print(f"  Timestamp: {data.get('timestamp', 0)}")
                    print()
                    
            except Exception as e:
                print(f"Erro ao receber mensagem: {e}")
    
    def send_message(self, content):
        """Envia mensagem para o broker"""
        try:
            message = {
                "user": self.client_name,
                "content": content,
                "timestamp": self.clock.get_timestamp(),
                "clock": self.clock.increment()
            }
            
            # Envia mensagem
            self.broker_socket.send_json(message)
            
            # Recebe resposta
            response = self.broker_socket.recv_json()
            self.clock.update(response.get("clock", 0))
            
            print(f"[{self.client_name}] Mensagem enviada:")
            print(f"  Conteúdo: {content}")
            print(f"  Status: {response.get('status', 'unknown')}")
            print(f"  Servidor: {response.get('server', 'unknown')}")
            print(f"  Relógio lógico: {response.get('clock', 0)}")
            print()
            
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
    
    def run_interactive(self):
        """Modo interativo do cliente"""
        print(f"Cliente {self.client_name} pronto. Digite mensagens (ou 'quit' para sair):")
        
        while True:
            try:
                content = input(f"[{self.client_name}]> ")
                if content.lower() == 'quit':
                    break
                if content.strip():
                    self.send_message(content)
            except KeyboardInterrupt:
                break
        
        print(f"Cliente {self.client_name} encerrado")
        self.cleanup()
    
    def run_automatic(self, message_count=10, interval=2):
        """Modo automático do cliente"""
        print(f"Cliente {self.client_name} enviando {message_count} mensagens automaticamente...")
        
        for i in range(message_count):
            content = f"Mensagem automática {i+1} de {self.client_name}"
            self.send_message(content)
            time.sleep(interval)
        
        print(f"Cliente {self.client_name} finalizou envio automático")
        self.cleanup()
    
    def cleanup(self):
        """Limpa recursos"""
        self.broker_socket.close()
        self.proxy_socket.close()
        self.broker_context.term()
        self.proxy_context.term()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python client.py <nome_do_cliente> [modo]")
        print("Modos: interactive (padrão) ou automatic")
        sys.exit(1)
    
    client_name = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "interactive"
    
    client = Client(client_name)
    
    if mode == "automatic":
        client.run_automatic()
    else:
        client.run_interactive()
