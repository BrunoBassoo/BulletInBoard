"""
Configurações do sistema distribuído
"""

# Portas dos serviços
PORTS = {
    'reference_server': 5555,
    'server_communication': 5556,
    'server_pub': 5557,
    'proxy_sub': 5557,
    'proxy_pub': 5558,
    'broker': 5559,
    'server1_broker': 5561,
    'server2_broker': 5562,
    'server3_broker': 5563,
    'server1_pub': 5564,
    'server2_pub': 5565,
    'server3_pub': 5566
}

# Configurações de sincronização
SYNC_CONFIG = {
    'message_interval': 10,  # Sincroniza a cada 10 mensagens
    'heartbeat_interval': 5,  # Heartbeat a cada 5 segundos
    'heartbeat_timeout': 30,  # Timeout de 30 segundos
    'election_timeout': 2,  # Timeout de eleição 2 segundos
}

# Configurações dos bots
BOT_CONFIG = {
    'message_interval_min': 2,  # Intervalo mínimo entre mensagens
    'message_interval_max': 5,  # Intervalo máximo entre mensagens
    'default_duration': 120,  # Duração padrão em segundos
}

# Configurações do cliente
CLIENT_CONFIG = {
    'auto_message_count': 10,  # Número de mensagens no modo automático
    'auto_message_interval': 2,  # Intervalo entre mensagens automáticas
}

# Templates de mensagens para bots
BOT_MESSAGES = [
    "Olá, sou o bot {bot_name}",
    "Mensagem automática do {bot_name}",
    "Teste de sincronização - {bot_name}",
    "Relógio lógico: {clock} - {bot_name}",
    "Sistema distribuído funcionando - {bot_name}",
    "Heartbeat ativo - {bot_name}",
    "Processando mensagem - {bot_name}",
    "Sincronização em andamento - {bot_name}"
]

# Configurações de logging
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'show_clock': True,  # Mostra relógio lógico nos logs
    'show_timestamp': True,  # Mostra timestamp físico nos logs
}
