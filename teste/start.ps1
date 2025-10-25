# Sistema Distribuído com Relógios - Inicialização
Write-Host "Sistema Distribuído com Relógios - Inicialização" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Verifica se Docker está instalado
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Erro: Docker não está instalado" -ForegroundColor Red
    exit 1
}

# Verifica se Docker Compose está instalado
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "Erro: Docker Compose não está instalado" -ForegroundColor Red
    exit 1
}

Write-Host "1. Parando containers existentes..." -ForegroundColor Yellow
docker-compose down

Write-Host "2. Construindo e iniciando containers..." -ForegroundColor Yellow
docker-compose up --build -d

Write-Host "3. Aguardando sistema inicializar..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "4. Verificando status dos containers..." -ForegroundColor Yellow
docker-compose ps

Write-Host "5. Mostrando logs recentes..." -ForegroundColor Yellow
docker-compose logs --tail=20

Write-Host ""
Write-Host "Sistema iniciado com sucesso!" -ForegroundColor Green
Write-Host "Para ver logs em tempo real: docker-compose logs -f" -ForegroundColor Cyan
Write-Host "Para parar o sistema: docker-compose down" -ForegroundColor Cyan
Write-Host "Para testar componentes: python test_system.py" -ForegroundColor Cyan
Write-Host "Para demonstração: python demo.py" -ForegroundColor Cyan
