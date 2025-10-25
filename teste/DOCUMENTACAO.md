# Sistema Distribuído com Relógios - Documentação

## Visão Geral

Este projeto implementa um sistema distribuído completo com relógios lógicos e sincronização de relógios físicos usando o algoritmo de Berkeley. O sistema é composto por múltiplos processos que se comunicam via ZeroMQ e são orquestrados usando Docker.

## Arquitetura

### Componentes Principais

1. **Servidor de Referência** (`reference_server.py`)
   - Gerencia ranks dos servidores
   - Mantém lista de servidores ativos
   - Monitora heartbeat dos servidores
   - Porta: 5555

2. **Servidores** (`server.py`) - 3 réplicas
   - Processam mensagens dos clientes
   - Implementam sincronização de relógios
   - Participam de eleições de coordenador
   - Portas: 5561-5563 (broker), 5564-5566 (pub), 5556 (comunicação), 5557 (pub)

3. **Broker** (`broker.py`)
   - Intermediário entre clientes e servidores
   - Distribui mensagens aleatoriamente
   - Porta: 5559

4. **Proxy** (`proxy.py`)
   - Distribui mensagens processadas via pub/sub
   - Portas: 5557 (sub), 5558 (pub)

5. **Cliente** (`client.py`)
   - Envia mensagens para o sistema
   - Recebe respostas via proxy
   - Modo interativo ou automático

6. **Bots** (`bot.py`) - 2 réplicas
   - Simulam usuários automáticos
   - Enviam mensagens periodicamente

## Funcionalidades Implementadas

### Relógio Lógico

- **Incremento**: Antes do envio de cada mensagem
- **Atualização**: Ao receber mensagem, usa máximo entre relógio local e recebido
- **Thread-safe**: Protegido por locks para acesso concorrente

### Algoritmo de Berkeley

- **Coordenador**: Eleito automaticamente entre servidores
- **Coleta de tempos**: Coordenador coleta tempos de todos os servidores
- **Cálculo de média**: Calcula tempo médio de todos os servidores
- **Ajuste**: Ajusta relógios físicos para o tempo médio
- **Frequência**: Sincronização a cada 10 mensagens processadas

### Eleição de Coordenador

- **Detecção de falha**: Servidores verificam se coordenador está ativo
- **Processo de eleição**: Servidor com maior rank se torna coordenador
- **Anúncio**: Novo coordenador é anunciado via pub/sub
- **Timeout**: Eleições têm timeout de 2 segundos

### Serviços do Servidor de Referência

#### 1. Rank (`rank`)
```json
// Requisição
{
  "service": "rank",
  "data": {
    "user": "server1",
    "timestamp": 1234567890,
    "clock": 1
  }
}

// Resposta
{
  "service": "rank",
  "data": {
    "rank": 1,
    "timestamp": 1234567891,
    "clock": 2
  }
}
```

#### 2. Lista (`list`)
```json
// Requisição
{
  "service": "list",
  "data": {
    "timestamp": 1234567890,
    "clock": 1
  }
}

// Resposta
{
  "service": "list",
  "data": {
    "list": [
      {"name": "server1", "rank": 1},
      {"name": "server2", "rank": 2}
    ],
    "timestamp": 1234567891,
    "clock": 2
  }
}
```

#### 3. Heartbeat (`heartbeat`)
```json
// Requisição
{
  "service": "heartbeat",
  "data": {
    "user": "server1",
    "timestamp": 1234567890,
    "clock": 1
  }
}

// Resposta
{
  "service": "heartbeat",
  "data": {
    "timestamp": 1234567891,
    "clock": 2
  }
}
```

## Como Executar

### Pré-requisitos

- Docker
- Docker Compose
- Python 3.9+ (para execução local)

### Execução com Docker

```bash
# Iniciar sistema completo
docker-compose up --build

# Ver logs em tempo real
docker-compose logs -f

# Parar sistema
docker-compose down
```

### Execução Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar componentes individualmente
python reference_server.py
python server.py server1
python broker.py
python proxy.py
python client.py cliente1
python bot.py bot1
```

## Estrutura de Arquivos

```
teste/
├── README.md                 # Documentação principal
├── DOCUMENTACAO.md          # Documentação detalhada
├── requirements.txt         # Dependências Python
├── Dockerfile              # Imagem Docker
├── docker-compose.yml      # Orquestração de containers
├── start.sh               # Script de inicialização (Linux/Mac)
├── start.ps1              # Script de inicialização (Windows)
├── logical_clock.py       # Implementação do relógio lógico
├── berkeley_sync.py       # Algoritmo de Berkeley e eleição
├── reference_server.py    # Servidor de referência
├── server.py             # Servidores de processamento
├── broker.py             # Broker de mensagens
├── proxy.py              # Proxy pub/sub
├── client.py             # Cliente
├── bot.py                # Bots automáticos
├── config.py             # Configurações do sistema
├── demo.py               # Script de demonstração
└── test_system.py        # Script de teste
```

## Fluxo de Mensagens

1. **Cliente → Broker**: Cliente envia mensagem
2. **Broker → Servidor**: Broker seleciona servidor aleatoriamente
3. **Servidor → Processamento**: Servidor processa mensagem
4. **Servidor → Proxy**: Servidor publica resultado
5. **Proxy → Clientes**: Proxy distribui para todos os clientes/bots

## Monitoramento

### Logs dos Containers

```bash
# Todos os containers
docker-compose logs

# Container específico
docker-compose logs reference_server
docker-compose logs server1
docker-compose logs broker
docker-compose logs proxy
docker-compose logs client
docker-compose logs bot1
```

### Status dos Containers

```bash
# Status geral
docker-compose ps

# Informações detalhadas
docker-compose ps -a
```

## Testes

### Teste Automático

```bash
# Executar demonstração
python demo.py

# Testar sistema
python test_system.py

# Testar componentes individuais
python test_system.py individual
```

### Teste Manual

1. Inicie o sistema com `docker-compose up --build`
2. Observe os logs para verificar funcionamento
3. Verifique sincronização de relógios
4. Teste eleição de coordenador
5. Monitore heartbeat dos servidores

## Configurações

### Portas

- **5555**: Servidor de referência
- **5556**: Comunicação entre servidores
- **5557**: Pub dos servidores / Sub do proxy
- **5558**: Pub do proxy
- **5559**: Broker
- **5561-5563**: Servidores para broker
- **5564-5566**: Pub dos servidores

### Parâmetros de Sincronização

- **Intervalo de mensagens**: 10 mensagens
- **Heartbeat**: 5 segundos
- **Timeout de heartbeat**: 30 segundos
- **Timeout de eleição**: 2 segundos

## Troubleshooting

### Problemas Comuns

1. **Containers não iniciam**
   - Verifique se Docker está rodando
   - Verifique se as portas estão disponíveis
   - Execute `docker-compose down` e tente novamente

2. **Erro de conexão**
   - Verifique se todos os containers estão rodando
   - Verifique os logs para erros específicos
   - Aguarde alguns segundos para inicialização completa

3. **Sincronização não funciona**
   - Verifique se o servidor de referência está ativo
   - Verifique se os servidores estão se comunicando
   - Observe os logs de sincronização

### Logs Importantes

- **Relógio lógico**: Incrementos e atualizações
- **Sincronização**: Tempos coletados e ajustes
- **Eleição**: Processo de eleição de coordenador
- **Heartbeat**: Monitoramento de servidores ativos

## Desenvolvimento

### Adicionando Novos Componentes

1. Crie o arquivo Python do componente
2. Adicione ao `docker-compose.yml`
3. Configure as portas em `config.py`
4. Teste com `test_system.py`

### Modificando Configurações

1. Edite `config.py` para alterar parâmetros
2. Reinicie os containers com `docker-compose restart`
3. Verifique se as mudanças foram aplicadas

## Conclusão

Este sistema demonstra implementação completa de:
- Relógios lógicos em sistemas distribuídos
- Algoritmo de Berkeley para sincronização
- Eleição de coordenador
- Comunicação via ZeroMQ
- Orquestração com Docker

O sistema está pronto para uso e pode ser estendido com funcionalidades adicionais conforme necessário.
