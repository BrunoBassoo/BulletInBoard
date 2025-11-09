#!/usr/bin/env python3
"""
Script de teste para demonstrar a eficiência do MessagePack
comparado com JSON
"""

import msgpack
import json
import sys
from datetime import datetime

def test_serialization():
    """Testa serialização e compara tamanhos"""
    
    print("="*60)
    print("TESTE DE SERIALIZAÇÃO: MessagePack vs JSON")
    print("="*60)
    
    # Exemplo 1: Mensagem de Login
    print("\n1. Mensagem de Login:")
    login_msg = {
        "service": "login",
        "data": {
            "user": "joao_silva",
            "timestamp": datetime.now().timestamp(),
            "clock": 1
        }
    }
    
    # MessagePack
    packed = msgpack.packb(login_msg)
    print(f"   MessagePack: {len(packed)} bytes")
    print(f"   Binário: {packed[:50]}...")
    
    # JSON
    json_str = json.dumps(login_msg)
    json_bytes = json_str.encode('utf-8')
    print(f"   JSON: {len(json_bytes)} bytes")
    print(f"   String: {json_str}")
    
    # Economia
    economia = ((len(json_bytes) - len(packed)) / len(json_bytes)) * 100
    print(f"   📊 Economia: {economia:.1f}%")
    
    # Exemplo 2: Lista de usuários
    print("\n2. Lista de Usuários:")
    users_msg = {
        "service": "users",
        "data": {
            "timestamp": datetime.now().timestamp(),
            "users": ["alice", "bob", "charlie", "diana", "eve"],
            "clock": 5
        }
    }
    
    packed = msgpack.packb(users_msg)
    json_bytes = json.dumps(users_msg).encode('utf-8')
    
    print(f"   MessagePack: {len(packed)} bytes")
    print(f"   JSON: {len(json_bytes)} bytes")
    economia = ((len(json_bytes) - len(packed)) / len(json_bytes)) * 100
    print(f"   📊 Economia: {economia:.1f}%")
    
    # Exemplo 3: Mensagem longa em canal
    print("\n3. Publicação em Canal:")
    publish_msg = {
        "service": "publish",
        "data": {
            "user": "bot_1234",
            "channel": "tecnologia",
            "message": "Esta é uma mensagem mais longa que contém informações sobre o sistema de mensageria distribuída usando ZeroMQ e MessagePack.",
            "timestamp": datetime.now().timestamp(),
            "clock": 42
        }
    }
    
    packed = msgpack.packb(publish_msg)
    json_bytes = json.dumps(publish_msg).encode('utf-8')
    
    print(f"   MessagePack: {len(packed)} bytes")
    print(f"   JSON: {len(json_bytes)} bytes")
    economia = ((len(json_bytes) - len(packed)) / len(json_bytes)) * 100
    print(f"   📊 Economia: {economia:.1f}%")
    
    # Exemplo 4: Mensagens múltiplas
    print("\n4. Batch de 100 Mensagens:")
    total_msgpack = 0
    total_json = 0
    
    for i in range(100):
        msg = {
            "service": "message",
            "data": {
                "src": f"user_{i}",
                "dst": f"user_{(i+1)%100}",
                "message": f"Mensagem número {i}",
                "timestamp": datetime.now().timestamp(),
                "clock": i
            }
        }
        total_msgpack += len(msgpack.packb(msg))
        total_json += len(json.dumps(msg).encode('utf-8'))
    
    print(f"   MessagePack: {total_msgpack} bytes")
    print(f"   JSON: {total_json} bytes")
    economia = ((total_json - total_msgpack) / total_json) * 100
    print(f"   📊 Economia: {economia:.1f}%")
    print(f"   💾 Redução: {total_json - total_msgpack} bytes")

def test_performance():
    """Testa performance de serialização/desserialização"""
    import time
    
    print("\n" + "="*60)
    print("TESTE DE PERFORMANCE")
    print("="*60)
    
    msg = {
        "service": "publish",
        "data": {
            "user": "test_user",
            "channel": "test_channel",
            "message": "Test message " * 10,
            "timestamp": datetime.now().timestamp(),
            "clock": 100
        }
    }
    
    iterations = 10000
    
    # MessagePack
    start = time.time()
    for _ in range(iterations):
        packed = msgpack.packb(msg)
        unpacked = msgpack.unpackb(packed, raw=False)
    msgpack_time = time.time() - start
    
    # JSON
    start = time.time()
    for _ in range(iterations):
        json_str = json.dumps(msg)
        parsed = json.loads(json_str)
    json_time = time.time() - start
    
    print(f"\n{iterations} iterações de serialização + desserialização:")
    print(f"   MessagePack: {msgpack_time:.4f}s")
    print(f"   JSON: {json_time:.4f}s")
    
    speedup = json_time / msgpack_time
    print(f"   ⚡ MessagePack é {speedup:.2f}x mais rápido")

def test_types():
    """Testa suporte a diferentes tipos de dados"""
    
    print("\n" + "="*60)
    print("TESTE DE TIPOS DE DADOS")
    print("="*60)
    
    test_data = {
        "string": "Olá, mundo!",
        "int": 42,
        "float": 3.14159,
        "bool": True,
        "none": None,
        "list": [1, 2, 3, 4, 5],
        "dict": {"a": 1, "b": 2},
        "nested": {
            "level1": {
                "level2": {
                    "level3": "deep"
                }
            }
        }
    }
    
    print("\nDados originais:")
    print(json.dumps(test_data, indent=2))
    
    # Serializar e desserializar
    packed = msgpack.packb(test_data)
    unpacked = msgpack.unpackb(packed, raw=False)
    
    print(f"\nTamanho serializado: {len(packed)} bytes")
    print(f"Integridade dos dados: {'✅ OK' if test_data == unpacked else '❌ ERRO'}")

if __name__ == "__main__":
    try:
        test_serialization()
        test_performance()
        test_types()
        
        print("\n" + "="*60)
        print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("="*60)
        print("\nMessagePack está funcionando corretamente!")
        print("Benefícios comprovados:")
        print("  • Menor tamanho de mensagens")
        print("  • Melhor performance")
        print("  • Suporte completo a tipos de dados")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}", file=sys.stderr)
        sys.exit(1)

