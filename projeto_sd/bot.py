import zmq
import msgpack
import time
import threading
import random
import os

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

class Bot:
    def __init__(self, bot_id):
        self.bot_id = bot_id
        self.nome = f"Bot_{bot_id}"
        self.relogio = RelogioLogico()
        
        # Socket REQ para comunicação com broker
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://broker:5555")
        
        # Socket SUB para receber mensagens do proxy
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect("tcp://proxy:5558")
        
        self.canais_inscritos = []
        self.running = True
        
        print(f"[{self.nome}] Bot iniciado!", flush=True)
        
        # Thread para receber mensagens
        self.receiver_thread = threading.Thread(target=self.receber_mensagens, daemon=True)
        self.receiver_thread.start()
    
    def inscrever_topico(self, topico):
        """Inscreve em um tópico específico"""
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, topico)
        print(f"[{self.nome}] Inscrito no tópico: {topico}", flush=True)
    
    def enviar_request(self, opcao, dados):
        """Envia requisição e aguarda resposta"""
        try:
            # Incrementa relógio antes de enviar
            dados["clock"] = self.relogio.tick()
            
            request = {
                "opcao": opcao,
                "dados": dados
            }
            
            self.socket.send(msgpack.packb(request))
            reply_data = self.socket.recv()
            reply = msgpack.unpackb(reply_data, raw=False)
            
            # Atualiza relógio ao receber
            if "clock" in reply:
                self.relogio.update(reply["clock"])
            
            return reply
        except Exception as e:
            print(f"[{self.nome}] Erro ao enviar request: {e}", flush=True)
            return None
    
    def fazer_login(self):
        """Faz login no sistema"""
        dados = {
            "user": self.nome,
            "time": time.time()
        }
        
        reply = self.enviar_request("login", dados)
        if reply:
            # Inscreve no tópico do próprio nome para receber mensagens privadas
            self.inscrever_topico(self.nome)
            print(f"[{self.nome}] Login realizado com sucesso!", flush=True)
            return True
        else:
            print(f"[{self.nome}] Erro no login", flush=True)
            return False
    
    def cadastrar_canal(self, canal):
        """Cadastra um novo canal"""
        dados = {
            "canal": canal,
            "time": time.time()
        }
        
        reply = self.enviar_request("cadastrarCanal", dados)
        if reply:
            print(f"[{self.nome}] Canal '{canal}' cadastrado!", flush=True)
            # Inscreve no canal para receber mensagens
            self.inscrever_topico(canal)
            self.canais_inscritos.append(canal)
            return True
        else:
            print(f"[{self.nome}] Erro ao cadastrar canal", flush=True)
            return False
    
    def publicar_mensagem(self, canal, mensagem):
        """Publica mensagem em um canal"""
        dados = {
            "user": self.nome,
            "channel": canal,
            "message": mensagem,
            "timestamp": time.time()
        }
        
        reply = self.enviar_request("publish", dados)
        if reply:
            print(f"[{self.nome}] Publicado em '{canal}': {mensagem}", flush=True)
            return True
        else:
            print(f"[{self.nome}] Erro ao publicar", flush=True)
            return False
    
    def enviar_mensagem_privada(self, receptor, mensagem):
        """Envia mensagem privada para um usuário"""
        dados = {
            "user": self.nome,
            "receptor": receptor,
            "message": mensagem,
            "timestamp": time.time()
        }
        
        reply = self.enviar_request("message", dados)
        if reply:
            print(f"[{self.nome}] Mensagem privada enviada para '{receptor}'", flush=True)
            return True
        else:
            print(f"[{self.nome}] Erro ao enviar privada", flush=True)
            return False
    
    def receber_mensagens(self):
        """Thread que recebe mensagens do proxy via subscriber"""
        print(f"[{self.nome}] Subscriber iniciado, aguardando mensagens...", flush=True)
        
        while self.running:
            try:
                # Recebe mensagem com tópico
                topic, mensagem_data = self.sub_socket.recv_multipart()
                topic_str = topic.decode('utf-8')
                mensagem = msgpack.unpackb(mensagem_data, raw=False)
                
                # Atualiza relógio lógico
                if "clock" in mensagem:
                    self.relogio.update(mensagem["clock"])
                
                # Verifica se é mensagem de canal ou privada
                if "channel" in mensagem:
                    # Mensagem de canal
                    if mensagem.get("user") != self.nome:  # Não mostra próprias mensagens
                        print(f"\n[{self.nome}] [{mensagem['channel']}] {mensagem['user']}: {mensagem['message']}", flush=True)
                elif "receptor" in mensagem:
                    # Mensagem privada
                    if mensagem["receptor"] == self.nome:
                        print(f"\n[{self.nome}] Mensagem privada de {mensagem['user']}: {mensagem['message']}", flush=True)
                elif "coordinator" in mensagem.get("data", {}):
                    # Anúncio de novo coordenador
                    print(f"\n[{self.nome}] Novo coordenador: {mensagem['data']['coordinator']}", flush=True)
                
            except Exception as e:
                if self.running:
                    print(f"[{self.nome}] Erro ao receber mensagem: {e}", flush=True)
                time.sleep(0.5)
    
    def executar_comportamento(self):
        """Comportamento automatizado do bot"""
        # Aguarda servidores iniciarem
        time.sleep(3)
        
        # Faz login
        if not self.fazer_login():
            print(f"[{self.nome}] Falha no login. Encerrando...", flush=True)
            return
        
        time.sleep(1)
        
        # Cadastra canal
        canal = f"canal_{self.bot_id}"
        if not self.cadastrar_canal(canal):
            print(f"[{self.nome}] Falha ao cadastrar canal. Continuando...", flush=True)
        
        # Também se inscreve em canal geral se existir
        time.sleep(1)
        self.inscrever_topico("geral")
        
        time.sleep(2)
        
        # Lista de mensagens para enviar
        mensagens = [
            "Olá! Sou um bot automático",
            "Testando o sistema de mensagens",
            "Mensagem automática do bot",
            "Sistema funcionando perfeitamente!",
            "Relógio lógico sincronizado",
            "Enviando mensagem periódica",
            "Bot ativo e funcionando",
            "Teste de publicação no canal",
            "Mensagem de teste",
            "Sistema distribuído em ação!"
        ]
        
        contador = 0
        while self.running:
            try:
                # Escolhe canal aleatório entre os inscritos
                canal_escolhido = random.choice(self.canais_inscritos) if self.canais_inscritos else f"canal_{self.bot_id}"
                
                # Envia 10 mensagens
                for i in range(10):
                    msg = random.choice(mensagens)
                    self.publicar_mensagem(canal_escolhido, f"{msg} (#{contador}-{i})")
                    time.sleep(random.uniform(2, 4))  # Aguarda 2-4 segundos entre mensagens
                
                # Ocasionalmente envia mensagem privada para outro bot
                if contador % 3 == 0 and self.bot_id == 1:
                    self.enviar_mensagem_privada("Bot_2", f"Ping privado #{contador}")
                elif contador % 3 == 0 and self.bot_id == 2:
                    self.enviar_mensagem_privada("Bot_1", f"Pong privado #{contador}")
                
                contador += 1
                
                # Aguarda antes do próximo ciclo
                time.sleep(random.randint(5, 10))
                
            except Exception as e:
                print(f"[{self.nome}] Erro no comportamento: {e}", flush=True)
                time.sleep(5)
    
    def parar(self):
        """Para o bot"""
        self.running = False
        self.sub_socket.close()
        self.socket.close()
        self.context.term()

if __name__ == "__main__":
    # Pega ID do bot da variável de ambiente ou hostname
    try:
        import socket
        hostname = socket.gethostname()
        # Extrai número do hostname (ex: projeto_sd-bot-1 -> 1)
        if '-' in hostname:
            bot_id = int(hostname.split('-')[-1])
        else:
            bot_id = int(os.getenv("BOT_ID", "1"))
    except:
        bot_id = int(os.getenv("BOT_ID", "1"))
    
    bot = Bot(bot_id)
    
    try:
        bot.executar_comportamento()
    except KeyboardInterrupt:
        print(f"\n[Bot_{bot_id}] Encerrando...", flush=True)
        bot.parar()
