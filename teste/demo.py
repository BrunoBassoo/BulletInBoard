#!/usr/bin/env python3
"""
Script de demonstração do sistema distribuído com relógios
"""

import zmq
import json
import time
import threading
from logical_clock import LogicalClock

class SystemDemo:
    def __init__(self):
        self.clock = LogicalClock()
        print("Demonstração do Sistema Distribuído com Relógios")
        print("="*60)
    
    def demo_logical_clock(self):
        """Demonstra o funcionamento do relógio lógico"""
        print("\n1. DEMONSTRAÇÃO DO RELÓGIO LÓGICO")
        print("-" * 40)
        
        clock = LogicalClock()
        
        print("Simulando envio de mensagem...")
        clock.increment()
        print(f"Relógio após envio: {clock.get_clock()}")
        
        print("Simulando recebimento de mensagem com relógio 5...")
        clock.update(5)
        print(f"Relógio após recebimento: {clock.get_clock()}")
        
        print("Simulando recebimento de mensagem com relógio 3...")
        clock.update(3)
        print(f"Relógio após recebimento: {clock.get_clock()}")
        
        print("Simulando envio de nova mensagem...")
        clock.increment()
        print(f"Relógio após novo envio: {clock.get_clock()}")
    
    def demo_berkeley_sync(self):
        """Demonstra o algoritmo de Berkeley"""
        print("\n2. DEMONSTRAÇÃO DO ALGORITMO DE BERKELEY")
        print("-" * 40)
        
        print("Simulando sincronização de relógios:")
        print("- Coordenador coleta tempos dos servidores")
        print("- Calcula tempo médio")
        print("- Ajusta relógios para o tempo médio")
        print("- Sincronização ocorre a cada 10 mensagens")
    
    def demo_election(self):
        """Demonstra a eleição de coordenador"""
        print("\n3. DEMONSTRAÇÃO DA ELEIÇÃO DE COORDENADOR")
        print("-" * 40)
        
        print("Processo de eleição:")
        print("1. Servidor detecta que coordenador está inativo")
        print("2. Inicia processo de eleição")
        print("3. Envia requisições para servidores com rank maior")
        print("4. Se não recebe resposta, se torna coordenador")
        print("5. Anuncia novo coordenador via pub/sub")
    
    def demo_services(self):
        """Demonstra os serviços do servidor de referência"""
        print("\n4. DEMONSTRAÇÃO DOS SERVIÇOS")
        print("-" * 40)
        
        print("Servidor de Referência oferece:")
        print("- rank: Atribui rank aos servidores")
        print("- list: Retorna lista de servidores ativos")
        print("- heartbeat: Monitora servidores ativos")
        
        print("\nExemplo de requisição rank:")
        print(json.dumps({
            "service": "rank",
            "data": {
                "user": "server1",
                "timestamp": 1234567890,
                "clock": 1
            }
        }, indent=2))
        
        print("\nExemplo de resposta rank:")
        print(json.dumps({
            "service": "rank",
            "data": {
                "rank": 1,
                "timestamp": 1234567891,
                "clock": 2
            }
        }, indent=2))
    
    def demo_architecture(self):
        """Demonstra a arquitetura do sistema"""
        print("\n5. ARQUITETURA DO SISTEMA")
        print("-" * 40)
        
        print("Componentes:")
        print("┌─────────────────┐    ┌─────────────────┐")
        print("│ Servidor Ref.   │◄──►│ Servidores      │")
        print("│ (rank, list)    │    │ (3 réplicas)    │")
        print("└─────────────────┘    └─────────────────┘")
        print("                              │")
        print("                              ▼")
        print("┌─────────────────┐    ┌─────────────────┐")
        print("│ Broker           │◄──►│ Servidores      │")
        print("│ (req/rep)        │    │ (processamento) │")
        print("└─────────────────┘    └─────────────────┘")
        print("         │                       │")
        print("         ▼                       ▼")
        print("┌─────────────────┐    ┌─────────────────┐")
        print("│ Cliente/Bots     │    │ Proxy           │")
        print("│ (req/rep)        │    │ (pub/sub)       │")
        print("└─────────────────┘    └─────────────────┘")
    
    def demo_message_flow(self):
        """Demonstra o fluxo de mensagens"""
        print("\n6. FLUXO DE MENSAGENS")
        print("-" * 40)
        
        print("1. Cliente envia mensagem para Broker")
        print("2. Broker seleciona servidor aleatoriamente")
        print("3. Servidor processa mensagem")
        print("4. Servidor publica resultado no Proxy")
        print("5. Proxy distribui para todos os clientes/bots")
        print("6. Relógios lógicos são atualizados em cada passo")
    
    def run_demo(self):
        """Executa demonstração completa"""
        self.demo_logical_clock()
        self.demo_berkeley_sync()
        self.demo_election()
        self.demo_services()
        self.demo_architecture()
        self.demo_message_flow()
        
        print("\n" + "="*60)
        print("DEMONSTRAÇÃO CONCLUÍDA")
        print("="*60)
        print("\nPara executar o sistema:")
        print("1. docker-compose up --build")
        print("2. Aguarde todos os containers iniciarem")
        print("3. Observe os logs para ver o funcionamento")
        print("4. Para parar: docker-compose down")

if __name__ == "__main__":
    demo = SystemDemo()
    demo.run_demo()
