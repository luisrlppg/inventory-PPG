#!/usr/bin/env powershell
# Script de despliegue en producción con Docker

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   DESPLIEGUE EN PRODUCCION - Docker" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    Write-Host "[1/5] Deteniendo contenedores actuales..." -ForegroundColor Yellow
    docker-compose down
    if ($LASTEXITCODE -ne 0) { throw "Error deteniendo contenedores" }

    Write-Host ""
    Write-Host "[2/5] Construyendo nueva imagen..." -ForegroundColor Yellow
    docker-compose build --no-cache
    if ($LASTEXITCODE -ne 0) { throw "Error construyendo imagen" }

    Write-Host ""
    Write-Host "[3/5] Iniciando contenedores en modo producción..." -ForegroundColor Yellow
    docker-compose --profile production up -d
    if ($LASTEXITCODE -ne 0) { throw "Error iniciando contenedores" }

    Write-Host ""
    Write-Host "[4/5] Verificando estado de contenedores..." -ForegroundColor Yellow
    docker-compose ps

    Write-Host ""
    Write-Host "[5/5] Mostrando logs recientes..." -ForegroundColor Yellow
    docker-compose logs --tail=20

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "   DESPLIEGUE COMPLETADO" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Aplicación disponible en:" -ForegroundColor White
    Write-Host "- Con Nginx: http://localhost" -ForegroundColor Cyan
    Write-Host "- Directo: http://localhost:5000" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Comandos útiles:" -ForegroundColor White
    Write-Host "- Ver logs: docker-compose logs -f" -ForegroundColor Gray
    Write-Host "- Detener: docker-compose down" -ForegroundColor Gray
    Write-Host "- Estado: docker-compose ps" -ForegroundColor Gray

} catch {
    Write-Host ""
    Write-Host "❌ ERROR EN DESPLIEGUE: $_" -ForegroundColor Red
    Write-Host "Revisa los logs arriba para más detalles." -ForegroundColor Red
    exit 1
}

Write-Host ""
Read-Host "Presiona Enter para continuar"