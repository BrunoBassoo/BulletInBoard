# Como Executar o Projeto

## 🚀 Inicialização

### 1. Build das imagens
```bash
docker-compose build
```

### 2. Subir os serviços
```bash
docker-compose up
```

**Ou em background:**
```bash
docker-compose up -d
```

## 🔍 Verificar Status dos Containers

```bash
docker-compose ps
```

## 📋 Ver Logs

### Ver todos os logs
```bash
docker-compose logs -f
```

### Ver log de um serviço específico
```bash
docker-compose logs -f broker
docker-compose logs -f servidor
docker-compose logs -f cliente
docker-compose logs -f referencia
```

## 🎮 Usar o Cliente Interativo

```bash
docker attach cliente
```

**Importante:** Para sair sem matar o container, use `Ctrl+P` seguido de `Ctrl+Q`

Para matar e sair use: `Ctrl+C`

## ⚙️ Ordem de Inicialização Esperada

1. **Referência** (porta 5560)
2. **Broker** (portas 5555, 5556)
3. **Proxy** (portas 5557, 5558)
4. **Servidor** (3 réplicas)
   - Tentará se registrar na referência
   - Se falhar, opera em modo standalone
5. **Publisher** (conecta ao servidor e proxy)
6. **Subscriber** (conecta ao proxy)
7. **Cliente** (conecta ao broker)
8. **Cliente Automático** (2 réplicas, conecta ao broker)

## 🐛 Troubleshooting

### Problema: Cliente não recebe resposta

1. **Verificar se o broker está rodando:**
```bash
docker-compose logs broker
```
Deve mostrar:
```
[BROKER] ✅ Socket ROUTER bound na porta 5555
[BROKER] ✅ Socket DEALER bound na porta 5556
[BROKER] 🚀 Broker pronto!
```

2. **Verificar se o servidor está pronto:**
```bash
docker-compose logs servidor
```
Deve mostrar:
```
[S] ✅ Servidor pronto para receber mensagens!
[S] Aguardando requisições...
```

3. **Verificar logs em tempo real:**
```bash
# Terminal 1
docker-compose logs -f servidor

# Terminal 2
docker attach cliente
```

### Problema: Servidor não inicia

1. **Verificar se a referência está rodando:**
```bash
docker-compose logs referencia
```

2. **Reiniciar os serviços:**
```bash
docker-compose restart
```

### Problema: Timeout ao registrar servidor

Isso é normal se a referência não estiver pronta ainda. O servidor continuará em modo standalone e funcionará normalmente para operações de cliente.

```
[S] ⚠️ Timeout ao registrar. Servidor de referência não disponível.
[S] Continuando sem registro (modo standalone)...
```

### Limpar tudo e recomeçar

```bash
# Parar todos os containers
docker-compose down

# Remover volumes (dados persistidos)
docker-compose down -v

# Rebuild e restart
docker-compose build
docker-compose up
```

## 📊 Testar Funcionalidades

### 1. Testar Login
```
Entre com a opção: 1
Entre com o seu usuário: teste123
```

### 2. Listar Usuários
```
Entre com a opção: 2
```

### 3. Criar Canal
```
Entre com a opção: 3
Entre com o canal: tecnologia
```

### 4. Listar Canais
```
Entre com a opção: 4
```

### 5. Publicar em Canal
```
Entre com a opção: 5
Entre com o seu usuário: teste123
Entre com o nome do canal: tecnologia
Entre com a mensagem a ser publicada: Olá pessoal!
```

### 6. Enviar Mensagem Privada
```
Entre com a opção: 6
Entre com o seu usuário (origem): teste123
Entre com o nome do destinatário: outro_usuario
Entre com a mensagem a ser enviada: Olá!
```

## 📈 Logs Esperados

### Cliente executando opção 1 (Login)

**Cliente:**
```
------ Login ------
Entre com o seu usuário: bruno
[DEBUG] Enviando requisição de login...
[DEBUG] Aguardando resposta...

✅ Resposta recebida:
   Status: sucesso
   Login realizado com sucesso!
   Clock: 2
```

**Servidor:**
```
[S] 📨 Mensagem recebida do cliente
[S] 🔍 Service: login | User: bruno
[S] - Login do bruno feito!
[S] 📤 Enviando resposta: login - Status: sucesso
[S] ✅ Resposta enviada com sucesso!
```

## 🔧 Comandos Úteis

### Ver containers rodando
```bash
docker ps
```

### Executar comando em um container
```bash
docker exec -it <container_name> sh
```

### Ver consumo de recursos
```bash
docker stats
```

### Reiniciar um serviço específico
```bash
docker-compose restart servidor
```

### Escalar servidores
```bash
docker-compose up --scale servidor=5
```

## 🎯 Fluxo Completo de Teste

1. Subir os serviços:
```bash
docker-compose up -d
```

2. Aguardar ~5 segundos para tudo inicializar

3. Ver logs do servidor:
```bash
docker-compose logs -f servidor
```

4. Em outro terminal, conectar ao cliente:
```bash
docker attach cliente
```

5. Fazer login e testar funcionalidades

6. Ver logs em tempo real de todos os serviços:
```bash
docker-compose logs -f
```

## 📝 Notas Importantes

- **REQ/REP é síncrono**: Cada requisição deve receber uma resposta antes da próxima
- **Flush é essencial**: Sem `flush=True`, logs podem não aparecer no Docker
- **Timeouts são importantes**: Evitam que o sistema trave indefinidamente
- **Modo standalone**: Servidor funciona sem referência, mas sem sincronização
- **Dados persistidos**: Arquivos JSON são salvos dentro dos containers

## 🆘 Em caso de problemas persistentes

1. Verificar logs completos:
```bash
docker-compose logs > logs_completos.txt
```

2. Verificar portas em uso:
```bash
netstat -an | grep "5555\|5556\|5557\|5558\|5559\|5560\|5561"
```

3. Remover tudo e recomeçar:
```bash
docker-compose down -v
docker system prune -a
docker-compose build --no-cache
docker-compose up
```

## ✅ Checklist de Verificação

- [ ] Docker e Docker Compose instalados
- [ ] Porta 5555-5561 disponíveis
- [ ] Build executado com sucesso
- [ ] Broker iniciou corretamente
- [ ] Servidor(es) pronto(s)
- [ ] Cliente conecta ao broker
- [ ] Logs aparecem com flush

🎉 **Boa sorte com o projeto!**

