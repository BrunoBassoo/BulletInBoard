import time
import threading

class LogicalClock:
    def __init__(self):
        self.clock = 0
        self.lock = threading.Lock()
    
    def increment(self):
        """Incrementa o relógio lógico antes do envio de mensagem"""
        with self.lock:
            self.clock += 1
            return self.clock
    
    def update(self, received_clock):
        """Atualiza o relógio lógico ao receber uma mensagem"""
        with self.lock:
            self.clock = max(self.clock, received_clock) + 1
            return self.clock
    
    def get_clock(self):
        """Retorna o valor atual do relógio"""
        with self.lock:
            return self.clock
    
    def get_timestamp(self):
        """Retorna timestamp físico atual"""
        return int(time.time() * 1000)  # milissegundos
