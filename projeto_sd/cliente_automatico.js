const zmq = require('zeromq');
const msgpack = require('msgpack5')();

class RelogioLogico {
    constructor() {
        this.clock = 0;
    }
    
    tick() {
        this.clock++;
        return this.clock;
    }
    
    update(clockRecebido) {
        if (clockRecebido > this.clock) {
            this.clock = clockRecebido;
        }
    }
    
    get() {
        return this.clock;
    }
}

async function main() {
    const sock = new zmq.Request();
    sock.connect("tcp://broker:5555");
    sock.sendTimeout = 10000;
    sock.receiveTimeout = 10000;
    
    const relogio = new RelogioLogico();
    
    const usuario = process.env.CLIENT_NAME || `bot_${Math.floor(Math.random() * 9000) + 1000}`;
    console.log(`[BOT ${usuario}] Iniciado`);
    
    // Login
    let request = {
        service: "login",
        data: {
            user: usuario,
            timestamp: Date.now() / 1000,
            clock: relogio.tick()
        }
    };
    
    await sock.send(msgpack.encode(request));
    let reply = msgpack.decode(await sock.receive());
    
    if (reply.data && reply.data.clock) {
        relogio.update(reply.data.clock);
    }
    
    console.log(`[BOT ${usuario}] Login realizado`);
    
    const mensagensDisponiveis = [
        "Ola a todos!",
        "Mensagem automatica.",
        "Testando o canal.",
        "Mensagem de exemplo.",
        "Pub/Sub funcionando.",
        "Mais uma mensagem.",
        "JavaScript e legal.",
        "Distribuido e melhor.",
        "ZeroMQ test.",
        "Fim das mensagens."
    ];
    
    const canaisPossiveis = ["geral", "noticias", "tecnologia", "esportes", "games"];
    const mensagensPrivadas = [
        "Oi!",
        "Tudo bem?",
        "Mensagem privada teste.",
        "Olá amigo!",
        "Falou!",
        "E ai?",
        "Beleza?",
        "Mensagem direta."
    ];
    
    let ciclo = 0;
    
    // Loop infinito
    while (true) {
        try {
            ciclo++;
            
            // A cada 5 ciclos, faz operações variadas
            const operacao = ciclo % 5;
            
            switch (operacao) {
                case 0:
                    // Listar usuários
                    request = {
                        service: "users",
                        data: {
                            timestamp: Date.now() / 1000,
                            clock: relogio.tick()
                        }
                    };
                    
                    await sock.send(msgpack.encode(request));
                    reply = msgpack.decode(await sock.receive());
                    
                    if (reply.data && reply.data.clock) {
                        relogio.update(reply.data.clock);
                    }
                    
                    const usuarios = reply.data?.users || [];
                    console.log(`[BOT ${usuario}] Listou usuarios: ${usuarios.length} encontrados`);
                    break;
                
                case 1:
                    // Cadastrar canal
                    const novoCanal = canaisPossiveis[Math.floor(Math.random() * canaisPossiveis.length)];
                    
                    request = {
                        service: "channel",
                        data: {
                            channel: novoCanal,
                            timestamp: Date.now() / 1000,
                            clock: relogio.tick()
                        }
                    };
                    
                    await sock.send(msgpack.encode(request));
                    reply = msgpack.decode(await sock.receive());
                    
                    if (reply.data && reply.data.clock) {
                        relogio.update(reply.data.clock);
                    }
                    
                    if (reply.data?.status === "sucesso") {
                        console.log(`[BOT ${usuario}] Canal cadastrado: ${novoCanal}`);
                    } else {
                        console.log(`[BOT ${usuario}] Tentou cadastrar canal: ${novoCanal} (ja existe)`);
                    }
                    break;
                
                case 2:
                    // Listar canais
                    request = {
                        service: "channels",
                        data: {
                            timestamp: Date.now() / 1000,
                            clock: relogio.tick()
                        }
                    };
                    
                    await sock.send(msgpack.encode(request));
                    reply = msgpack.decode(await sock.receive());
                    
                    if (reply.data && reply.data.clock) {
                        relogio.update(reply.data.clock);
                    }
                    
                    const canais = reply.data?.channels || [];
                    console.log(`[BOT ${usuario}] Listou canais: ${canais.length} encontrados`);
                    break;
                
                case 3:
                    // Publicar em canal
                    request = {
                        service: "channels",
                        data: {
                            timestamp: Date.now() / 1000,
                            clock: relogio.tick()
                        }
                    };
                    
                    await sock.send(msgpack.encode(request));
                    reply = msgpack.decode(await sock.receive());
                    
                    if (reply.data && reply.data.clock) {
                        relogio.update(reply.data.clock);
                    }
                    
                    let canaisDisponiveis = reply.data?.channels || [];
                    if (canaisDisponiveis.length === 0) {
                        canaisDisponiveis = ["geral"];
                    }
                    
                    const canalEscolhido = canaisDisponiveis[Math.floor(Math.random() * canaisDisponiveis.length)];
                    const mensagemCanal = mensagensDisponiveis[Math.floor(Math.random() * mensagensDisponiveis.length)];
                    
                    request = {
                        service: "publish",
                        data: {
                            user: usuario,
                            channel: canalEscolhido,
                            message: mensagemCanal,
                            timestamp: Date.now() / 1000,
                            clock: relogio.tick()
                        }
                    };
                    
                    await sock.send(msgpack.encode(request));
                    reply = msgpack.decode(await sock.receive());
                    
                    if (reply.data && reply.data.clock) {
                        relogio.update(reply.data.clock);
                    }
                    
                    console.log(`[BOT ${usuario}] Publicou em #${canalEscolhido}: ${mensagemCanal}`);
                    break;
                
                case 4:
                    // Enviar mensagem privada
                    request = {
                        service: "users",
                        data: {
                            timestamp: Date.now() / 1000,
                            clock: relogio.tick()
                        }
                    };
                    
                    await sock.send(msgpack.encode(request));
                    reply = msgpack.decode(await sock.receive());
                    
                    if (reply.data && reply.data.clock) {
                        relogio.update(reply.data.clock);
                    }
                    
                    const usuariosDisponiveis = reply.data?.users || [];
                    const outrosUsuarios = usuariosDisponiveis.filter(u => u !== usuario);
                    
                    if (outrosUsuarios.length > 0) {
                        const destinatario = outrosUsuarios[Math.floor(Math.random() * outrosUsuarios.length)];
                        const mensagemPrivada = mensagensPrivadas[Math.floor(Math.random() * mensagensPrivadas.length)];
                        
                        request = {
                            service: "message",
                            data: {
                                src: usuario,
                                dst: destinatario,
                                message: mensagemPrivada,
                                timestamp: Date.now() / 1000,
                                clock: relogio.tick()
                            }
                        };
                        
                        await sock.send(msgpack.encode(request));
                        reply = msgpack.decode(await sock.receive());
                        
                        if (reply.data && reply.data.clock) {
                            relogio.update(reply.data.clock);
                        }
                        
                        console.log(`[BOT ${usuario}] Enviou mensagem para @${destinatario}: ${mensagemPrivada}`);
                    } else {
                        console.log(`[BOT ${usuario}] Nenhum outro usuario disponivel para mensagem privada`);
                    }
                    break;
            }
            
            await new Promise(resolve => setTimeout(resolve, 3000));
            
        } catch (error) {
            console.error(`[BOT ${usuario}] Erro: ${error.message}`);
            await new Promise(resolve => setTimeout(resolve, 5000));
        }
    }
}

main().catch(console.error);

