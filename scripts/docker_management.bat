@echo off
:menu
cls
echo ========================================
echo     GESTION DE CONTENEDORES DOCKER
echo ========================================
echo.
echo 1. Desplegar en PRODUCCION (con Nginx)
echo 2. Desplegar en DESARROLLO
echo 3. Ver estado de contenedores
echo 4. Ver logs en tiempo real
echo 5. Reiniciar contenedores
echo 6. Detener contenedores
echo 7. Limpiar contenedores e imagenes
echo 8. Backup de base de datos
echo 9. Salir
echo.
set /p choice="Selecciona una opcion (1-9): "

if "%choice%"=="1" goto production
if "%choice%"=="2" goto development
if "%choice%"=="3" goto status
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto restart
if "%choice%"=="6" goto stop
if "%choice%"=="7" goto cleanup
if "%choice%"=="8" goto backup
if "%choice%"=="9" goto exit
goto menu

:production
echo.
echo Desplegando en PRODUCCION...
call deploy_production.bat
goto menu

:development
echo.
echo Desplegando en DESARROLLO...
call deploy_development.bat
goto menu

:status
echo.
echo Estado de contenedores:
docker-compose ps
echo.
echo Imagenes disponibles:
docker images | findstr inventario
echo.
pause
goto menu

:logs
echo.
echo Mostrando logs en tiempo real (Ctrl+C para salir)...
docker-compose logs -f
goto menu

:restart
echo.
echo Reiniciando contenedores...
docker-compose restart
docker-compose ps
echo.
pause
goto menu

:stop
echo.
echo Deteniendo contenedores...
docker-compose down
echo Contenedores detenidos.
echo.
pause
goto menu

:cleanup
echo.
echo ADVERTENCIA: Esto eliminara contenedores e imagenes no utilizadas
set /p confirm="Estas seguro? (s/N): "
if /i "%confirm%"=="s" (
    echo Limpiando contenedores detenidos...
    docker container prune -f
    echo Limpiando imagenes no utilizadas...
    docker image prune -f
    echo Limpieza completada.
) else (
    echo Operacion cancelada.
)
echo.
pause
goto menu

:backup
echo.
echo Creando backup de base de datos...
docker-compose exec inventario-app cp /app/inventario.db /app/backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%.db
echo Backup creado en el contenedor.
echo Para descargarlo usa: docker cp inventario-ppg:/app/backup_*.db .
echo.
pause
goto menu

:exit
echo.
echo Saliendo...
exit /b 0