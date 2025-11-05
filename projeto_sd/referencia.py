import zmq
import msgpack
import time
import threading

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

class ServidorReferencia:
    def __init__(self):
        self.relogio = RelogioLogico()
        self.servidores = {}  # {nome: {"rank": rank, "last_heartbeat": timestamp}}
        self.proximo_rank = 1
        self.lock = threading.Lock()
        
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:5560")
        
        print("[REFERÊNCIA] Servidor de referência iniciado na porta 5560", flush=True)
        
        # Thread para limpar servidores inativos
        self.cleanup_thread = threading.Thread(target=self.cleanup_servidores_inativos, daemon=True)
        self.cleanup_thread.start()
    
    def cleanup_servidores_inativos(self):
        """Remove servidores que não enviaram heartbeat há mais de 30 segundos"""
        while True:
            time.sleep(10)  # Verifica a cada 10 segundos
            current_time = time.time()
            with self.lock:
                inativos = []
                for nome, dados in self.servidores.items():
                    if current_time - dados["last_heartbeat"] > 30:
                        inativos.append(nome)
                
                for nome in inativos:
                    print(f"[REFERÊNCIA] Removendo servidor inativo: {nome}", flush=True)
                    del self.servidores[nome]
    
    def processar_rank(self, data):
        """Processa requisição de rank de um servidor"""
        user = data.get("user")
        
        with self.lock:
            if user not in self.servidores:
                # Novo servidor - atribui rank
                rank = self.proximo_rank
                self.proximo_rank += 1
                self.servidores[user] = {
                    "rank": rank,
                    "last_heartbeat": time.time()
                }
                print(f"[REFERÊNCIA] Novo servidor cadastrado: {user} com rank {rank}", flush=True)
            else:
                # Servidor já existe - retorna rank existente
                rank = self.servidores[user]["rank"]
                self.servidores[user]["last_heartbeat"] = time.time()
        
        return {
            "service": "rank",
            "data": {
                "rank": rank,
                "timestamp": time.time(),
                "clock": self.relogio.tick()
            }
        }
    
    def processar_list(self):
        """Retorna lista de todos os servidores ativos"""
        with self.lock:
            lista = [
                {"name": nome, "rank": dados["rank"]} 
                for nome, dados in self.servidores.items()
            ]
        
        return {
            "service": "list",
            "data": {
                "list": lista,
                "timestamp": time.time(),
                "clock": self.relogio.tick()
            }
        }
    
    def processar_heartbeat(self, data):
        """Processa heartbeat de um servidor"""
        user = data.get("user")
        
        with self.lock:
            if user in self.servidores:
                self.servidores[user]["last_heartbeat"] = time.time()
                print(f"[REFERÊNCIA] Heartbeat recebido de: {user}", flush=True)
            else:
                print(f"[REFERÊNCIA] Heartbeat de servidor desconhecido: {user}", flush=True)
        
        return {
            "service": "heartbeat",
            "data": {
                "timestamp": time.time(),
                "clock": self.relogio.tick()
            }
        }
    
    def run(self):
        """Loop principal do servidor de referência"""
        while True:
            try:
                # Recebe requisição
                request_data = self.socket.recv()
                request = msgpack.unpackb(request_data, raw=False)
                
                service = request.get("service")
                data = request.get("data", {})
                
                # Atualiza relógio lógico
                if "clock" in data:
                    self.relogio.update(data["clock"])
                
                print(f"[REFERÊNCIA] Requisição recebida: {service}", flush=True)
                
                # Processa serviço
                if service == "rank":
                    reply = self.processar_rank(data)
                elif service == "list":
                    reply = self.processar_list()
                elif service == "heartbeat":
                    reply = self.processar_heartbeat(data)
                else:
                    reply = {
                        "service": "error",
                        "data": {
                            "msg": "Serviço não encontrado",
                            "timestamp": time.time(),
                            "clock": self.relogio.tick()
                        }
                    }
                
                # Envia resposta
                self.socket.send(msgpack.packb(reply))
                
            except Exception as e:
                print(f"[REFERÊNCIA] Erro: {e}", flush=True)
                # Envia resposta de erro
                error_reply = {
                    "service": "error",
                    "data": {
                        "msg": str(e),
                        "timestamp": time.time(),
                        "clock": self.relogio.tick()
                    }
                }
                self.socket.send(msgpack.packb(error_reply))

if __name__ == "__main__":
    servidor = ServidorReferencia()
    servidor.run()

