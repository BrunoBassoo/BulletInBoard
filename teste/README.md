# Projeto Teste - Sistema Distribuído com Relógios

Este projeto implementa um sistema distribuído com relógios lógicos e sincronização de relógios físicos usando o algoritmo de Berkeley.

## Componentes

- **Servidor de Referência**: Gerencia ranks e lista de servidores
- **Servidores**: Processam mensagens e sincronizam relógios
- **Cliente**: Envia mensagens para o sistema
- **Bots**: Simulam usuários automáticos
- **Broker**: Intermediário entre clientes e servidores
- **Proxy**: Distribui mensagens via pub/sub

## Funcionalidades

- Relógio lógico em todos os processos
- Sincronização de relógios físicos (algoritmo de Berkeley)
- Eleição de coordenador
- Heartbeat para monitoramento de servidores
- Sistema de ranks para servidores

## Como executar

```bash
docker-compose up --build
```
