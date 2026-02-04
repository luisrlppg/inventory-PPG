#!/usr/bin/env python3
"""
Script para intercambiar bases de datos de forma segura
Reemplaza inventario.db con bkpinventario.db migrada
"""

import os
import shutil
from datetime import datetime

def intercambiar_bases_datos():
    """Intercambiar las bases de datos de forma segura"""
    print("🔄 INTERCAMBIO SEGURO DE BASES DE DATOS")
    print("=" * 50)
    
    # Verificar que existen ambas bases de datos
    if not os.path.exists('bkpinventario.db'):
        print("❌ No se encontró bkpinventario.db")
        print("💡 Ejecuta primero: python migrar_produccion_completa.py")
        return False
    
    if not os.path.exists('inventario.db'):
        print("❌ No se encontró inventario.db")
        return False
    
    print("📋 Estado actual:")
    print(f"   📊 bkpinventario.db: {os.path.getsize('bkpinventario.db'):,} bytes")
    print(f"   📊 inventario.db: {os.path.getsize('inventario.db'):,} bytes")
    
    # Confirmar intercambio
    print("\n⚠️  IMPORTANTE:")
    print("- inventario.db actual será respaldada como inventario_old_[timestamp].db")
    print("- bkpinventario.db se convertirá en la nueva inventario.db")
    print("- bkpinventario.db se mantendrá como backup")
    
    respuesta = input("\n¿Continuar con el intercambio? (s/N): ")
    if respuesta.lower() != 's':
        print("Intercambio cancelado")
        return False
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 1. Respaldar inventario.db actual
        backup_old = f'inventario_old_{timestamp}.db'
        shutil.copy2('inventario.db', backup_old)
        print(f"✅ Backup de inventario.db creado: {backup_old}")
        
        # 2. Copiar bkpinventario.db como nueva inventario.db
        shutil.copy2('bkpinventario.db', 'inventario.db')
        print("✅ bkpinventario.db copiada como nueva inventario.db")
        
        # 3. Verificar tamaños
        new_size = os.path.getsize('inventario.db')
        backup_size = os.path.getsize('bkpinventario.db')
        
        if new_size == backup_size:
            print("✅ Verificación de integridad: OK")
        else:
            print("⚠️  Advertencia: Los tamaños no coinciden exactamente")
        
        print("\n🎉 INTERCAMBIO COMPLETADO EXITOSAMENTE")
        print("=" * 40)
        print("📁 Archivos resultantes:")
        print(f"   📊 inventario.db (NUEVA): {os.path.getsize('inventario.db'):,} bytes")
        print(f"   📊 bkpinventario.db (backup): {os.path.getsize('bkpinventario.db'):,} bytes")
        print(f"   📊 {backup_old} (backup anterior): {os.path.getsize(backup_old):,} bytes")
        
        print("\n✅ La aplicación ahora usará los datos de producción con todas las nuevas funcionalidades")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el intercambio: {e}")
        return False

def verificar_aplicacion():
    """Verificar que la aplicación puede conectarse a la nueva base de datos"""
    print("\n🧪 VERIFICANDO CONEXIÓN DE LA APLICACIÓN")
    print("=" * 40)
    
    try:
        import sqlite3
        
        conn = sqlite3.connect('inventario.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verificar tablas principales
        tablas_criticas = ['productos', 'inventario', 'ubicaciones', 'proveedores', 'categorias', 'maquinas']
        
        for tabla in tablas_criticas:
            try:
                count = cursor.execute(f'SELECT COUNT(*) as count FROM {tabla}').fetchone()['count']
                print(f"✅ {tabla}: {count} registros")
            except Exception as e:
                print(f"❌ Error en tabla {tabla}: {e}")
                return False
        
        # Verificar que la aplicación puede hacer consultas complejas
        try:
            productos_con_info = cursor.execute('''
                SELECT p.id, p.descripcion, c.nombre as categoria, pr.nombre as proveedor,
                       COALESCE(SUM(i.cantidad), 0) as stock_total
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
                LEFT JOIN inventario i ON p.id = i.producto_id
                GROUP BY p.id
                LIMIT 5
            ''').fetchall()
            
            print(f"✅ Consulta compleja exitosa: {len(productos_con_info)} productos verificados")
            
        except Exception as e:
            print(f"⚠️  Advertencia en consulta compleja: {e}")
        
        conn.close()
        
        print("✅ Base de datos lista para la aplicación")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando aplicación: {e}")
        return False

def main():
    """Función principal"""
    print("🔄 INTERCAMBIO DE BASE DE DATOS DE PRODUCCIÓN")
    print("=" * 60)
    print("Este script intercambiará las bases de datos de forma segura:")
    print("1. Respaldará inventario.db actual")
    print("2. Copiará bkpinventario.db como nueva inventario.db")
    print("3. Verificará que la aplicación funcione correctamente")
    print()
    
    if intercambiar_bases_datos():
        if verificar_aplicacion():
            print("\n🎉 PROCESO COMPLETADO EXITOSAMENTE")
            print("✅ La aplicación está lista para usar con los datos de producción")
            print("\n📋 Próximos pasos recomendados:")
            print("1. Probar la aplicación web")
            print("2. Verificar que todos los datos se muestran correctamente")
            print("3. Probar las nuevas funcionalidades (proveedores, categorías, máquinas)")
            print("4. Si todo funciona bien, puedes eliminar los backups antiguos")
        else:
            print("\n⚠️  ADVERTENCIA: Hay problemas con la base de datos")
            print("🔧 Revisa los errores antes de usar la aplicación")
    else:
        print("\n❌ INTERCAMBIO FALLÓ")
        print("🔧 Revisa los errores y vuelve a intentar")

if __name__ == "__main__":
    main()