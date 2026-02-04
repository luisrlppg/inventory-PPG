import os

class Config:
    """Configuración de la aplicación Flask"""
    
    # Configuración básica
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu-clave-secreta-muy-segura-aqui'
    
    # Base de datos
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inventario.db')
    
    # Configuración de archivos
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imagenes')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Configuración de la empresa
    EMPRESA_NOMBRE = "Plásticos Plasa (PPG)"
    EMPRESA_UBICACION = "Oficinas - Planta Alta"
    SISTEMA_NOMBRE = "Sistema de Inventario de Refacciones"
    SISTEMA_VERSION = "1.0.0"
    
    # Configuración de paginación
    PRODUCTOS_POR_PAGINA = 50
    INVENTARIO_POR_PAGINA = 100
    
    # Configuración de alertas
    STOCK_MINIMO_ALERTA = 1  # Alertar cuando el stock sea menor o igual a este valor
    
    # Configuración de imágenes
    IMAGEN_EXTENSIONES_PERMITIDAS = {'jpg', 'jpeg', 'png', 'gif'}
    IMAGEN_TAMAÑO_MAXIMO = (800, 800)  # Redimensionar imágenes grandes
    
    # Configuración de respaldos
    RESPALDO_AUTOMATICO = True
    RESPALDO_DIAS = 7  # Mantener respaldos por 7 días
    
    @staticmethod
    def init_app(app):
        """Inicializar configuración de la aplicación"""
        # Crear carpetas necesarias
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # Configurar logging
        if not app.debug:
            import logging
            from logging.handlers import RotatingFileHandler
            
            if not os.path.exists('logs'):
                os.mkdir('logs')
            
            file_handler = RotatingFileHandler('logs/inventario.log', maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Sistema de inventario iniciado')

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False

# Configuración por defecto
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}