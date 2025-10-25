import zmq
import json
import time
import threading
import random
import sys
from logical_clock import LogicalClock

class Bot:
    def __init__(self, bot_name, broker_port=5559, proxy_port=5558):
        self.bot_name = bot_name
        self.clock = LogicalClock()
        self.running = True
        
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
        
        # Thread para enviar mensagens automaticamente
        self.send_thread = threading.Thread(target=self._send_messages, daemon=True)
        self.send_thread.start()
        
        print(f"Bot {bot_name} iniciado")
    
    def _receive_messages(self):
        """Recebe mensagens do proxy"""
        while self.running:
            try:
                # Recebe mensagem do proxy
                topic, message = self.proxy_socket.recv_multipart()
                if topic == b"messages":
                    data = json.loads(message)
                    self.clock.update(data.get("clock", 0))
                    
                    # Bot processa mensagem recebida
                    print(f"[{self.bot_name}] Mensagem recebida:")
                    print(f"  Servidor: {data.get('server', 'unknown')}")
                    print(f"  Conteúdo: {data.get('response', {}).get('content', 'N/A')}")
                    print(f"  Relógio lógico: {data.get('clock', 0)}")
                    print()
                    
            except Exception as e:
                if self.running:
                    print(f"Erro ao receber mensagem: {e}")
    
    def _send_messages(self):
        """Envia mensagens automaticamente"""
        message_templates = [
            "Olá, sou o bot {bot_name}",
            "Mensagem automática do {bot_name}",
            "Teste de sincronização - {bot_name}",
            "Relógio lógico: {clock} - {bot_name}",
            "Sistema distribuído funcionando - {bot_name}"
        ]
        
        message_count = 0
        while self.running:
            try:
                # Seleciona template aleatório
                template = random.choice(message_templates)
                content = template.format(
                    bot_name=self.bot_name,
                    clock=self.clock.get_clock()
                )
                
                # Envia mensagem
                self._send_message(content)
                message_count += 1
                
                # Intervalo aleatório entre 2 e 5 segundos
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                print(f"Erro ao enviar mensagem automática: {e}")
                time.sleep(1)
    
    def _send_message(self, content):
        """Envia uma mensagem para o broker"""
        try:
            message = {
                "user": self.bot_name,
                "content": content,
                "timestamp": self.clock.get_timestamp(),
                "clock": self.clock.increment()
            }
            
            # Envia mensagem
            self.broker_socket.send_json(message)
            
            # Recebe resposta
            response = self.broker_socket.recv_json()
            self.clock.update(response.get("clock", 0))
            
            print(f"[{self.bot_name}] Mensagem enviada:")
            print(f"  Conteúdo: {content}")
            print(f"  Status: {response.get('status', 'unknown')}")
            print(f"  Servidor: {response.get('server', 'unknown')}")
            print(f"  Relógio lógico: {response.get('clock', 0)}")
            print()
            
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
    
    def stop(self):
        """Para o bot"""
        self.running = False
        print(f"Bot {self.bot_name} parado")
        self.cleanup()
    
    def run(self, duration=60):
        """Executa o bot por um tempo determinado"""
        print(f"Bot {self.bot_name} executando por {duration} segundos...")
        
        try:
            time.sleep(duration)
        except KeyboardInterrupt:
            pass
        
        self.stop()
    
    def cleanup(self):
        """Limpa recursos"""
        self.broker_socket.close()
        self.proxy_socket.close()
        self.broker_context.term()
        self.proxy_context.term()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python bot.py <nome_do_bot> [duração_em_segundos]")
        sys.exit(1)
    
    bot_name = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    
    bot = Bot(bot_name)
    bot.run(duration)
