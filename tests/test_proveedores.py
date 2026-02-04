#!/usr/bin/env python3
"""
Test script para el sistema de proveedores
"""

import sqlite3
import sys
import os

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_proveedores_system():
    """Probar el sistema completo de proveedores"""
    print("🧪 PRUEBAS DEL SISTEMA DE PROVEEDORES")
    print("=" * 50)
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('inventario.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("1. Verificando estructura de la tabla proveedores...")
        
        # Verificar que existe la tabla
        table_exists = cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='proveedores'
        """).fetchone()
        
        if not table_exists:
            print("❌ ERROR: Tabla 'proveedores' no existe")
            return False
        
        print("✅ Tabla 'proveedores' existe")
        
        # Verificar estructura de la tabla
        columns = cursor.execute("PRAGMA table_info(proveedores)").fetchall()
        expected_columns = ['id', 'nombre', 'contacto', 'telefono', 'email', 'pagina_web', 'direccion', 'notas']
        
        column_names = [col['name'] for col in columns]
        for expected_col in expected_columns:
            if expected_col in column_names:
                print(f"✅ Columna '{expected_col}' existe")
            else:
                print(f"❌ ERROR: Columna '{expected_col}' falta")
                return False
        
        print("\n2. Verificando relación con productos...")
        
        # Verificar que productos tiene proveedor_id
        productos_columns = cursor.execute("PRAGMA table_info(productos)").fetchall()
        productos_column_names = [col['name'] for col in productos_columns]
        
        if 'proveedor_id' in productos_column_names:
            print("✅ Columna 'proveedor_id' existe en productos")
        else:
            print("❌ ERROR: Columna 'proveedor_id' falta en productos")
            return False
        
        print("\n3. Probando operaciones CRUD...")
        
        # Crear proveedor de prueba
        test_proveedor_data = (
            'Proveedor Test',
            'Juan Test',
            '555-TEST',
            'test@proveedor.com',
            'www.test.com',
            'Dirección Test',
            'Proveedor para pruebas'
        )
        
        cursor.execute('''
            INSERT INTO proveedores (nombre, contacto, telefono, email, pagina_web, direccion, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', test_proveedor_data)
        
        test_proveedor_id = cursor.lastrowid
        print(f"✅ Proveedor creado con ID: {test_proveedor_id}")
        
        # Leer proveedor
        proveedor = cursor.execute('SELECT * FROM proveedores WHERE id = ?', (test_proveedor_id,)).fetchone()
        if proveedor and proveedor['nombre'] == 'Proveedor Test':
            print("✅ Proveedor leído correctamente")
        else:
            print("❌ ERROR: No se pudo leer el proveedor")
            return False
        
        # Actualizar proveedor
        cursor.execute('''
            UPDATE proveedores SET contacto = ? WHERE id = ?
        ''', ('Juan Test Actualizado', test_proveedor_id))
        
        proveedor_actualizado = cursor.execute('SELECT * FROM proveedores WHERE id = ?', (test_proveedor_id,)).fetchone()
        if proveedor_actualizado['contacto'] == 'Juan Test Actualizado':
            print("✅ Proveedor actualizado correctamente")
        else:
            print("❌ ERROR: No se pudo actualizar el proveedor")
            return False
        
        print("\n4. Probando relación con productos...")
        
        # Buscar un producto existente
        producto_existente = cursor.execute('SELECT id FROM productos LIMIT 1').fetchone()
        
        if producto_existente:
            producto_id = producto_existente['id']
            
            # Asignar proveedor al producto
            cursor.execute('UPDATE productos SET proveedor_id = ? WHERE id = ?', 
                          (test_proveedor_id, producto_id))
            
            # Verificar la relación
            producto_con_proveedor = cursor.execute('''
                SELECT p.descripcion, pr.nombre as proveedor_nombre
                FROM productos p
                JOIN proveedores pr ON p.proveedor_id = pr.id
                WHERE p.id = ?
            ''', (producto_id,)).fetchone()
            
            if producto_con_proveedor and producto_con_proveedor['proveedor_nombre'] == 'Proveedor Test':
                print("✅ Relación producto-proveedor funciona correctamente")
            else:
                print("❌ ERROR: Relación producto-proveedor no funciona")
                return False
            
            # Limpiar la relación
            cursor.execute('UPDATE productos SET proveedor_id = NULL WHERE id = ?', (producto_id,))
        else:
            print("⚠️  No hay productos para probar la relación")
        
        print("\n5. Probando consultas complejas...")
        
        # Consulta de proveedores con conteo de productos
        proveedores_con_productos = cursor.execute('''
            SELECT p.id, p.nombre, COUNT(DISTINCT pr.id) as productos_count
            FROM proveedores p
            LEFT JOIN productos pr ON p.id = pr.proveedor_id
            WHERE p.id = ?
            GROUP BY p.id
        ''', (test_proveedor_id,)).fetchone()
        
        if proveedores_con_productos:
            print(f"✅ Consulta compleja funciona: {proveedores_con_productos['nombre']} tiene {proveedores_con_productos['productos_count']} productos")
        else:
            print("❌ ERROR: Consulta compleja falló")
            return False
        
        print("\n6. Probando restricciones...")
        
        # Intentar crear proveedor con nombre duplicado
        try:
            cursor.execute('''
                INSERT INTO proveedores (nombre) VALUES (?)
            ''', ('Proveedor Test',))
            print("❌ ERROR: Se permitió nombre duplicado")
            return False
        except sqlite3.IntegrityError:
            print("✅ Restricción de nombre único funciona")
        
        print("\n7. Limpiando datos de prueba...")
        
        # Eliminar proveedor de prueba
        cursor.execute('DELETE FROM proveedores WHERE id = ?', (test_proveedor_id,))
        
        # Verificar que se eliminó
        proveedor_eliminado = cursor.execute('SELECT * FROM proveedores WHERE id = ?', (test_proveedor_id,)).fetchone()
        if not proveedor_eliminado:
            print("✅ Proveedor de prueba eliminado correctamente")
        else:
            print("❌ ERROR: No se pudo eliminar el proveedor de prueba")
            return False
        
        # Commit de todos los cambios
        conn.commit()
        conn.close()
        
        print("\n🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("✅ El sistema de proveedores está funcionando correctamente")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN PRUEBAS: {e}")
        return False

def test_data_integrity():
    """Probar integridad de datos existentes"""
    print("\n🔍 VERIFICANDO INTEGRIDAD DE DATOS")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect('inventario.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Contar proveedores
        proveedores_count = cursor.execute('SELECT COUNT(*) as count FROM proveedores').fetchone()['count']
        print(f"📊 Total de proveedores: {proveedores_count}")
        
        # Contar productos con proveedor
        productos_con_proveedor = cursor.execute('''
            SELECT COUNT(*) as count FROM productos WHERE proveedor_id IS NOT NULL
        ''').fetchone()['count']
        print(f"📦 Productos con proveedor asignado: {productos_con_proveedor}")
        
        # Verificar referencias huérfanas
        referencias_huerfanas = cursor.execute('''
            SELECT COUNT(*) as count 
            FROM productos p 
            WHERE p.proveedor_id IS NOT NULL 
            AND p.proveedor_id NOT IN (SELECT id FROM proveedores)
        ''').fetchone()['count']
        
        if referencias_huerfanas == 0:
            print("✅ No hay referencias huérfanas")
        else:
            print(f"⚠️  {referencias_huerfanas} productos con proveedor_id inválido")
        
        # Mostrar algunos proveedores de ejemplo
        proveedores_ejemplo = cursor.execute('''
            SELECT p.nombre, COUNT(DISTINCT pr.id) as productos_count
            FROM proveedores p
            LEFT JOIN productos pr ON p.id = pr.proveedor_id
            GROUP BY p.id
            ORDER BY productos_count DESC, p.nombre
            LIMIT 5
        ''').fetchall()
        
        if proveedores_ejemplo:
            print("\n📋 Proveedores principales:")
            for proveedor in proveedores_ejemplo:
                print(f"   • {proveedor['nombre']}: {proveedor['productos_count']} productos")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verificando integridad: {e}")
        return False

def main():
    """Función principal"""
    print("🏢 SISTEMA DE PROVEEDORES - PRUEBAS COMPLETAS")
    print("=" * 60)
    
    if not os.path.exists('inventario.db'):
        print("❌ No se encontró inventario.db")
        print("💡 Ejecuta primero el script de migración: python migrar_proveedores.py")
        return
    
    # Ejecutar pruebas
    if test_proveedores_system():
        test_data_integrity()
        print("\n🎉 TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("✅ El sistema de proveedores está listo para usar")
    else:
        print("\n❌ ALGUNAS PRUEBAS FALLARON")
        print("🔧 Revisa la configuración del sistema")

if __name__ == "__main__":
    main()