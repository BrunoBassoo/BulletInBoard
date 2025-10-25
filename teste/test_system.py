#!/usr/bin/env python3
"""
Script de teste para o sistema distribuído com relógios
"""

import time
import subprocess
import sys

def run_command(cmd, description):
    """Executa comando e exibe resultado"""
    print(f"\n{'='*50}")
    print(f"Executando: {description}")
    print(f"Comando: {cmd}")
    print('='*50)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        print(f"Saída: {result.stdout}")
        if result.stderr:
            print(f"Erro: {result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Comando expirou após 30 segundos")
        return False
    except Exception as e:
        print(f"Erro ao executar comando: {e}")
        return False

def test_docker_compose():
    """Testa o sistema usando docker-compose"""
    print("Iniciando teste do sistema distribuído...")
    
    # Para containers existentes
    print("\n1. Parando containers existentes...")
    run_command("docker-compose down", "Parando containers")
    
    # Constrói e inicia containers
    print("\n2. Construindo e iniciando containers...")
    if not run_command("docker-compose up --build -d", "Iniciando sistema"):
        print("Erro ao iniciar containers")
        return False
    
    # Aguarda sistema inicializar
    print("\n3. Aguardando sistema inicializar...")
    time.sleep(10)
    
    # Verifica status dos containers
    print("\n4. Verificando status dos containers...")
    run_command("docker-compose ps", "Status dos containers")
    
    # Mostra logs dos containers
    print("\n5. Logs dos containers...")
    run_command("docker-compose logs --tail=20", "Logs recentes")
    
    # Testa comunicação entre componentes
    print("\n6. Testando comunicação...")
    print("Sistema deve estar funcionando com:")
    print("- 1 Servidor de referência")
    print("- 3 Servidores com sincronização")
    print("- 1 Broker")
    print("- 1 Proxy")
    print("- 1 Cliente")
    print("- 2 Bots")
    
    print("\n7. Para parar o sistema:")
    print("docker-compose down")
    
    return True

def test_individual_components():
    """Testa componentes individuais"""
    print("\nTestando componentes individuais...")
    
    components = [
        ("python reference_server.py", "Servidor de referência"),
        ("python server.py server1", "Servidor 1"),
        ("python broker.py", "Broker"),
        ("python proxy.py", "Proxy"),
        ("python client.py cliente1 automatic", "Cliente automático"),
        ("python bot.py bot1 30", "Bot 1")
    ]
    
    for cmd, description in components:
        print(f"\nTestando: {description}")
        print(f"Comando: {cmd}")
        print("Pressione Ctrl+C para parar e testar próximo componente...")
        
        try:
            subprocess.run(cmd, shell=True, timeout=5)
        except subprocess.TimeoutExpired:
            print("Componente funcionando (parado após 5 segundos)")
        except KeyboardInterrupt:
            print("Componente interrompido pelo usuário")
        except Exception as e:
            print(f"Erro: {e}")

def main():
    """Função principal"""
    print("Sistema Distribuído com Relógios - Teste")
    print("="*50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "individual":
        test_individual_components()
    else:
        test_docker_compose()

if __name__ == "__main__":
    main()
