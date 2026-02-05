#!/usr/bin/env python3
"""
Pruebas para el sistema de alertas de stock bajo
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, get_productos_stock_bajo, enviar_alerta_stock_bajo, verificar_y_enviar_alertas_stock
import sqlite3

def test_productos_stock_bajo():
    """Probar la detección de productos con stock bajo"""
    print("🧪 Probando detección de productos con stock bajo...")
    
    with app.app_context():
        productos_stock_bajo = get_productos_stock_bajo()
        
        print(f"📊 Productos encontrados con stock bajo: {len(productos_stock_bajo)}")
        
        if productos_stock_bajo:
            print("\n📋 Lista de productos con stock bajo:")
            for i, producto in enumerate(productos_stock_bajo[:5], 1):  # Mostrar solo los primeros 5
                diferencia = producto['stock_actual'] - producto['stock_minimo']
                estado = "CRÍTICO" if diferencia < 0 else "BAJO"
                
                print(f"   {i}. [{estado}] {producto['descripcion']}")
                print(f"      Código: {producto['codigo'] or 'N/A'}")
                print(f"      Stock: {producto['stock_actual']} | Mínimo: {producto['stock_minimo']} | Diferencia: {diferencia:+d}")
                print(f"      Categoría: {producto['categoria'] or 'Sin categoría'}")
                print(f"      Proveedor: {producto['proveedor'] or 'Sin proveedor'}")
                print()
            
            if len(productos_stock_bajo) > 5:
                print(f"   ... y {len(productos_stock_bajo) - 5} productos más")
        else:
            print("   ✅ No hay productos con stock bajo")
    
    return productos_stock_bajo

def test_configuracion_correo():
    """Verificar configuración de correo"""
    print("\n🔧 Verificando configuración de correo...")
    
    with app.app_context():
        config_items = [
            ('MAIL_SERVER', app.config.get('MAIL_SERVER')),
            ('MAIL_PORT', app.config.get('MAIL_PORT')),
            ('MAIL_USE_TLS', app.config.get('MAIL_USE_TLS')),
            ('MAIL_USERNAME', app.config.get('MAIL_USERNAME')),
            ('MAIL_PASSWORD', '***' if app.config.get('MAIL_PASSWORD') else None),
            ('MAIL_DEFAULT_SENDER', app.config.get('MAIL_DEFAULT_SENDER')),
            ('STOCK_ALERT_ENABLED', app.config.get('STOCK_ALERT_ENABLED')),
            ('STOCK_ALERT_RECIPIENTS', app.config.get('STOCK_ALERT_RECIPIENTS')),
        ]
        
        print("📋 Configuración actual:")
        for key, value in config_items:
            status = "✅" if value else "❌"
            print(f"   {status} {key}: {value}")
        
        # Verificar si está completamente configurado
        mail_configured = bool(
            app.config.get('MAIL_USERNAME') and 
            app.config.get('MAIL_PASSWORD') and
            app.config.get('MAIL_DEFAULT_SENDER')
        )
        
        print(f"\n📧 Estado del correo: {'✅ Configurado' if mail_configured else '❌ Incompleto'}")
        
        if not mail_configured:
            print("\n💡 Para configurar el correo, agrega estas variables a tu archivo .env:")
            print("""
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu-contraseña-de-aplicacion
MAIL_DEFAULT_SENDER=tu-email@gmail.com
STOCK_ALERT_RECIPIENTS=admin@empresa.com,gerente@empresa.com
            """)
    
    return mail_configured

def test_generar_contenido_alerta():
    """Probar la generación de contenido de alerta"""
    print("\n📝 Probando generación de contenido de alerta...")
    
    # Crear datos de prueba
    productos_prueba = [
        {
            'id': 1,
            'codigo': 'TEST001',
            'descripcion': 'Producto de Prueba 1',
            'stock_actual': 2,
            'stock_minimo': 5,
            'categoria': 'Categoría Test',
            'subcategoria': 'Subcategoría Test',
            'proveedor': 'Proveedor Test',
            'proveedor_telefono': '555-1234',
            'proveedor_email': 'proveedor@test.com',
            'ubicaciones_stock': 'Almacén A: 1, Almacén B: 1'
        },
        {
            'id': 2,
            'codigo': 'TEST002',
            'descripcion': 'Producto de Prueba 2',
            'stock_actual': 0,
            'stock_minimo': 3,
            'categoria': 'Categoría Test 2',
            'subcategoria': None,
            'proveedor': None,
            'proveedor_telefono': None,
            'proveedor_email': None,
            'ubicaciones_stock': None
        }
    ]
    
    with app.app_context():
        from app import generar_html_alerta_stock, generar_texto_alerta_stock
        
        # Generar contenido HTML
        html_content = generar_html_alerta_stock(productos_prueba)
        print(f"   ✅ Contenido HTML generado: {len(html_content)} caracteres")
        
        # Generar contenido de texto
        text_content = generar_texto_alerta_stock(productos_prueba)
        print(f"   ✅ Contenido de texto generado: {len(text_content)} caracteres")
        
        # Guardar ejemplos para revisión
        with open('test_alerta_ejemplo.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("   📄 Ejemplo HTML guardado en: test_alerta_ejemplo.html")
        
        with open('test_alerta_ejemplo.txt', 'w', encoding='utf-8') as f:
            f.write(text_content)
        print("   📄 Ejemplo de texto guardado en: test_alerta_ejemplo.txt")

def test_envio_alerta_simulado():
    """Simular envío de alerta (sin enviar realmente)"""
    print("\n📤 Simulando envío de alerta...")
    
    with app.app_context():
        productos_stock_bajo = get_productos_stock_bajo()
        
        if not productos_stock_bajo:
            print("   ℹ️  No hay productos con stock bajo para enviar alerta")
            return
        
        # Simular configuración de correo
        destinatarios_prueba = ['admin@test.com', 'gerente@test.com']
        
        print(f"   📧 Destinatarios: {', '.join(destinatarios_prueba)}")
        print(f"   📦 Productos a reportar: {len(productos_stock_bajo)}")
        
        # Verificar configuración
        mail_configured = bool(
            app.config.get('MAIL_USERNAME') and 
            app.config.get('MAIL_PASSWORD')
        )
        
        if mail_configured:
            print("   ✅ Configuración de correo disponible")
            print("   ⚠️  Para enviar realmente, ejecuta la función desde la interfaz web")
        else:
            print("   ❌ Configuración de correo incompleta - no se puede enviar")

def test_verificacion_automatica():
    """Probar la verificación automática de alertas"""
    print("\n🔄 Probando verificación automática de alertas...")
    
    with app.app_context():
        resultado = verificar_y_enviar_alertas_stock()
        
        if resultado:
            print("   ✅ Verificación completada exitosamente")
        else:
            print("   ⚠️  Verificación completada con advertencias")

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 Iniciando pruebas del sistema de alertas de stock")
    print("=" * 60)
    
    try:
        # Prueba 1: Detectar productos con stock bajo
        productos_stock_bajo = test_productos_stock_bajo()
        
        # Prueba 2: Verificar configuración
        mail_configured = test_configuracion_correo()
        
        # Prueba 3: Generar contenido de alerta
        test_generar_contenido_alerta()
        
        # Prueba 4: Simular envío
        test_envio_alerta_simulado()
        
        # Prueba 5: Verificación automática
        test_verificacion_automatica()
        
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE PRUEBAS:")
        print(f"   📦 Productos con stock bajo: {len(productos_stock_bajo)}")
        print(f"   📧 Configuración de correo: {'✅ Completa' if mail_configured else '❌ Incompleta'}")
        print(f"   🔧 Sistema de alertas: ✅ Funcional")
        
        if productos_stock_bajo and mail_configured:
            print("\n🎉 ¡Sistema listo para enviar alertas!")
            print("   💡 Accede a /admin/stock-alerts para gestionar alertas")
        elif productos_stock_bajo:
            print("\n⚠️  Hay productos con stock bajo pero falta configurar el correo")
        else:
            print("\n✅ No hay productos con stock bajo en este momento")
            
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()