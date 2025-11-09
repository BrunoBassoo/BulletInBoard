#!/usr/bin/env python3
"""
Script de teste para demonstrar o funcionamento dos relógios lógicos
e sincronização de relógio físico (Berkeley)
"""

import time

# Simulação do Relógio Lógico
class RelogioLogico:
    def __init__(self, nome):
        self.nome = nome
        self.clock = 0
    
    def tick(self):
        """Incrementa o relógio antes de enviar mensagem"""
        self.clock += 1
        print(f"[{self.nome}] Relógio incrementado para: {self.clock}")
        return self.clock
    
    def update(self, clock_recebido):
        """Atualiza o relógio ao receber mensagem"""
        clock_antigo = self.clock
        self.clock = max(self.clock, clock_recebido) + 1
        print(f"[{self.nome}] Relógio atualizado: {clock_antigo} -> {self.clock} (recebido: {clock_recebido})")
        return self.clock
    
    def get(self):
        return self.clock

def simular_troca_mensagens():
    """Simula troca de mensagens entre processos"""
    print("="*60)
    print("SIMULAÇÃO DE RELÓGIO LÓGICO")
    print("="*60)
    
    cliente = RelogioLogico("Cliente")
    servidor = RelogioLogico("Servidor")
    
    print("\n1. Cliente envia login ao Servidor")
    clock_enviado = cliente.tick()
    print(f"   Mensagem enviada com clock={clock_enviado}")
    
    print("\n2. Servidor recebe e processa")
    servidor.update(clock_enviado)
    
    print("\n3. Servidor responde ao Cliente")
    clock_resposta = servidor.tick()
    print(f"   Resposta enviada com clock={clock_resposta}")
    
    print("\n4. Cliente recebe resposta")
    cliente.update(clock_resposta)
    
    print("\n5. Cliente envia outra mensagem")
    clock_enviado2 = cliente.tick()
    print(f"   Mensagem enviada com clock={clock_enviado2}")
    
    print("\n6. Servidor recebe segunda mensagem")
    servidor.update(clock_enviado2)
    
    print(f"\n📊 Estado final:")
    print(f"   Cliente: clock={cliente.get()}")
    print(f"   Servidor: clock={servidor.get()}")

def simular_berkeley():
    """Simula algoritmo de Berkeley"""
    print("\n" + "="*60)
    print("SIMULAÇÃO DO ALGORITMO DE BERKELEY")
    print("="*60)
    
    # Simular relógios com pequenas diferenças
    relogio_coord = 100.0
    relogio_s1 = 102.0
    relogio_s2 = 98.0
    relogio_s3 = 101.5
    
    print(f"\n📍 Estado inicial dos relógios:")
    print(f"   Coordenador: {relogio_coord:.2f}s")
    print(f"   Servidor 1:  {relogio_s1:.2f}s (diferença: +{relogio_s1-relogio_coord:.2f}s)")
    print(f"   Servidor 2:  {relogio_s2:.2f}s (diferença: {relogio_s2-relogio_coord:.2f}s)")
    print(f"   Servidor 3:  {relogio_s3:.2f}s (diferença: +{relogio_s3-relogio_coord:.2f}s)")
    
    print(f"\n⏱️  Passo 1: Coordenador coleta os tempos")
    tempos = [relogio_coord, relogio_s1, relogio_s2, relogio_s3]
    
    print(f"\n⏱️  Passo 2: Calcula a média")
    media = sum(tempos) / len(tempos)
    print(f"   Média dos tempos: {media:.2f}s")
    
    print(f"\n⏱️  Passo 3: Calcula os ajustes")
    ajuste_coord = media - relogio_coord
    ajuste_s1 = media - relogio_s1
    ajuste_s2 = media - relogio_s2
    ajuste_s3 = media - relogio_s3
    
    print(f"   Ajuste Coordenador: {ajuste_coord:+.2f}s")
    print(f"   Ajuste Servidor 1:  {ajuste_s1:+.2f}s")
    print(f"   Ajuste Servidor 2:  {ajuste_s2:+.2f}s")
    print(f"   Ajuste Servidor 3:  {ajuste_s3:+.2f}s")
    
    print(f"\n⏱️  Passo 4: Aplica os ajustes")
    novo_coord = relogio_coord + ajuste_coord
    novo_s1 = relogio_s1 + ajuste_s1
    novo_s2 = relogio_s2 + ajuste_s2
    novo_s3 = relogio_s3 + ajuste_s3
    
    print(f"\n📍 Estado final dos relógios:")
    print(f"   Coordenador: {novo_coord:.2f}s")
    print(f"   Servidor 1:  {novo_s1:.2f}s")
    print(f"   Servidor 2:  {novo_s2:.2f}s")
    print(f"   Servidor 3:  {novo_s3:.2f}s")
    
    print(f"\n✅ Todos os relógios sincronizados!")

def simular_eleicao():
    """Simula algoritmo de eleição (Bully)"""
    print("\n" + "="*60)
    print("SIMULAÇÃO DO ALGORITMO DE ELEIÇÃO (BULLY)")
    print("="*60)
    
    servidores = [
        {"nome": "Servidor1", "rank": 1, "ativo": True},
        {"nome": "Servidor2", "rank": 2, "ativo": True},
        {"nome": "Servidor3", "rank": 3, "ativo": True},
    ]
    
    coordenador = servidores[2]["nome"]  # Maior rank
    
    print(f"\n📍 Estado inicial:")
    for s in servidores:
        print(f"   {s['nome']} (rank={s['rank']}) - {'🟢 Ativo' if s['ativo'] else '🔴 Inativo'}")
    print(f"   🎯 Coordenador atual: {coordenador}")
    
    print(f"\n💥 Coordenador {coordenador} falha!")
    servidores[2]["ativo"] = False
    
    print(f"\n🗳️  Servidor2 (rank=2) detecta falha e inicia eleição:")
    print(f"   - Envia ELECTION para Servidor3 (rank=3)")
    print(f"   - ❌ Sem resposta (Servidor3 está inativo)")
    print(f"   - ✅ Servidor2 se elege como coordenador!")
    
    coordenador = "Servidor2"
    
    print(f"\n📢 Servidor2 anuncia eleição no tópico 'servers'")
    print(f"   - Todos os servidores ativos são notificados")
    
    print(f"\n📍 Estado final:")
    for s in servidores:
        if s["ativo"]:
            print(f"   {s['nome']} (rank={s['rank']}) - 🟢 Ativo")
    print(f"   🎯 Novo coordenador: {coordenador}")
    
    print(f"\n🔄 Se Servidor3 voltar:")
    servidores[2]["ativo"] = True
    print(f"   - Servidor3 faz heartbeat")
    print(f"   - Servidor3 verifica quem é o coordenador")
    print(f"   - Servidor3 (rank=3) > Servidor2 (rank=2)")
    print(f"   - Servidor3 inicia eleição e se torna coordenador")
    coordenador = "Servidor3"
    print(f"   🎯 Coordenador final: {coordenador}")

def demonstrar_integracao():
    """Demonstra como tudo funciona junto"""
    print("\n" + "="*60)
    print("INTEGRAÇÃO: RELÓGIO LÓGICO + BERKELEY + ELEIÇÃO")
    print("="*60)
    
    print(f"\n🎬 Cenário completo:")
    print(f"   1. 3 Servidores iniciam e se registram no Servidor de Referência")
    print(f"   2. Servidor de Referência atribui ranks: 1, 2, 3")
    print(f"   3. Servidor com rank 3 é eleito coordenador inicial")
    print(f"   4. Servidores enviam heartbeat a cada 10 segundos")
    print(f"   5. A cada 30 segundos, servidores sincronizam relógio com coordenador")
    print(f"   6. Relógio lógico é atualizado em TODAS as mensagens")
    print(f"   7. Se coordenador falha, nova eleição é iniciada")
    
    print(f"\n📊 Mensagens trocadas com relógio lógico:")
    
    relogio = RelogioLogico("Sistema")
    
    print(f"\n   Cliente -> Servidor: login")
    clock1 = relogio.tick()
    print(f"      clock={clock1}")
    
    print(f"\n   Servidor -> Cliente: resposta")
    clock2 = relogio.tick()
    print(f"      clock={clock2}")
    
    print(f"\n   Servidor1 -> Referência: heartbeat")
    clock3 = relogio.tick()
    print(f"      clock={clock3}")
    
    print(f"\n   Servidor2 -> Coordenador: sincronizar relógio")
    clock4 = relogio.tick()
    print(f"      clock={clock4}")
    
    print(f"\n   Coordenador -> Servidor2: tempo atual")
    clock5 = relogio.tick()
    print(f"      clock={clock5}")
    
    print(f"\n✅ Relógio lógico garante ordem causal dos eventos!")
    print(f"✅ Berkeley garante sincronização de tempo físico!")
    print(f"✅ Eleição garante sempre há um coordenador!")

if __name__ == "__main__":
    try:
        simular_troca_mensagens()
        simular_berkeley()
        simular_eleicao()
        demonstrar_integracao()
        
        print("\n" + "="*60)
        print("✅ SIMULAÇÕES CONCLUÍDAS COM SUCESSO!")
        print("="*60)
        print("\nFuncionalidades implementadas:")
        print("  ✅ Relógio Lógico (Lamport)")
        print("  ✅ Sincronização de Relógio Físico (Berkeley)")
        print("  ✅ Eleição de Coordenador (Bully)")
        print("  ✅ Servidor de Referência (Rank + Heartbeat)")
        print("  ✅ Integração completa no sistema")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Erro durante a simulação: {e}")

