@echo off
echo ========================================
echo   DESPLIEGUE EN DESARROLLO - Docker
echo ========================================
echo.

echo [1/4] Deteniendo contenedores actuales...
docker-compose down

echo.
echo [2/4] Construyendo nueva imagen...
docker-compose build

echo.
echo [3/4] Iniciando contenedores en modo desarrollo...
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

echo.
echo [4/4] Verificando estado de contenedores...
docker-compose ps

echo.
echo ========================================
echo   DESPLIEGUE COMPLETADO
echo ========================================
echo.
echo Aplicacion disponible en:
echo - http://localhost:5000
echo.
echo Modo desarrollo activo:
echo - Auto-reload habilitado
echo - Debug mode activo
echo - Codigo montado como volumen
echo.
echo Para ver logs en tiempo real:
echo   docker-compose logs -f
echo.
pause