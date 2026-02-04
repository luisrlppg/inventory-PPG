@echo off
echo ========================================
echo   DESPLIEGUE EN PRODUCCION - Docker
echo ========================================
echo.

echo [1/5] Deteniendo contenedores actuales...
docker-compose down

echo.
echo [2/5] Construyendo nueva imagen...
docker-compose build --no-cache

echo.
echo [3/5] Iniciando contenedores en modo produccion...
docker-compose --profile production up -d

echo.
echo [4/5] Verificando estado de contenedores...
docker-compose ps

echo.
echo [5/5] Mostrando logs recientes...
docker-compose logs --tail=20

echo.
echo ========================================
echo   DESPLIEGUE COMPLETADO
echo ========================================
echo.
echo Aplicacion disponible en:
echo - Con Nginx: http://localhost
echo - Directo: http://localhost:5000
echo.
echo Para ver logs en tiempo real:
echo   docker-compose logs -f
echo.
echo Para detener:
echo   docker-compose down
echo.
pause