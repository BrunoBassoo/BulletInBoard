#!/bin/bash

echo "Sistema Distribuído com Relógios - Inicialização"
echo "================================================="

# Verifica se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "Erro: Docker não está instalado"
    exit 1
fi

# Verifica se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "Erro: Docker Compose não está instalado"
    exit 1
fi

echo "1. Parando containers existentes..."
docker-compose down

echo "2. Construindo e iniciando containers..."
docker-compose up --build -d

echo "3. Aguardando sistema inicializar..."
sleep 10

echo "4. Verificando status dos containers..."
docker-compose ps

echo "5. Mostrando logs recentes..."
docker-compose logs --tail=20

echo ""
echo "Sistema iniciado com sucesso!"
echo "Para ver logs em tempo real: docker-compose logs -f"
echo "Para parar o sistema: docker-compose down"
echo "Para testar componentes: python test_system.py"
echo "Para demonstração: python demo.py"
