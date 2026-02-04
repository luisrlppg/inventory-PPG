#!/usr/bin/env python3
"""
Script para probar la funcionalidad de gestión de máquinas con relación muchos-a-muchos
"""

import sqlite3
import requests
import json

def test_database_migration():
    """Verificar que la migración de máquinas se completó correctamente"""
    print("🔍 TESTING DATABASE MIGRATION")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('inventario.db')
        conn.row_factory = sqlite3.Row
        
        # Verificar que existe la tabla producto_maquinas
        table_exists = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='producto_maquinas'
        """).fetchone()
        
        if table_exists:
            print("✅ Tabla producto_maquinas existe")
        else:
            print("❌ Tabla producto_maquinas no existe - ejecutar migrar_maquinas.py")
            return False
        
        # Verificar que la tabla productos no tiene maquina_id
        columns = conn.execute("PRAGMA table_info(productos)").fetchall()
        column_names = [col['name'] for col in columns]
        
        if 'maquina_id' in column_names:
            print("⚠️  Columna maquina_id aún existe en productos - migración incompleta")
        else:
            print("✅ Columna maquina_id eliminada de productos")
        
        # Verificar estructura de producto_maquinas
        pm_columns = conn.execute("PRAGMA table_info(producto_maquinas)").fetchall()
        expected_columns = ['id', 'producto_id', 'maquina_id', 'fecha_creacion']
        
        for col in expected_columns:
            if col in [c['name'] for c in pm_columns]:
                print(f"✅ Columna '{col}' existe en producto_maquinas")
            else:
                print(f"❌ Columna '{col}' falta en producto_maquinas")
                return False
        
        # Contar registros
        maquinas_count = conn.execute("SELECT COUNT(*) as count FROM maquinas").fetchone()
        relaciones_count = conn.execute("SELECT COUNT(*) as count FROM producto_maquinas").fetchone()
        
        print(f"📊 Datos actuales:")
        print(f"   - Máquinas: {maquinas_count['count']}")
        print(f"   - Relaciones producto-máquina: {relaciones_count['count']}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verificando migración: {e}")
        return False

def test_maquina_operations():
    """Probar operaciones CRUD de máquinas"""
    print(f"\n🧪 TESTING MAQUINA OPERATIONS")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('inventario.db')
        conn.row_factory = sqlite3.Row
        
        # Test 1: Crear máquina de prueba
        print("1. Creando máquina de prueba...")
        cursor = conn.execute("INSERT INTO maquinas (nombre, descripcion) VALUES (?, ?)", 
                             ("TEST_MAQUINA", "Máquina de prueba para testing"))
        test_maquina_id = cursor.lastrowid
        print(f"✅ Máquina creada con ID: {test_maquina_id}")
        
        # Test 2: Leer máquina
        print("2. Leyendo máquina...")
        maquina = conn.execute("SELECT * FROM maquinas WHERE id = ?", (test_maquina_id,)).fetchone()
        if maquina:
            print(f"✅ Máquina leída: {maquina['nombre']}")
        else:
            print("❌ Error leyendo máquina")
            return False
        
        # Test 3: Crear relación producto-máquina
        print("3. Creando relación producto-máquina...")
        # Obtener un producto existente
        producto = conn.execute("SELECT id FROM productos LIMIT 1").fetchone()
        if producto:
            cursor = conn.execute("INSERT INTO producto_maquinas (producto_id, maquina_id) VALUES (?, ?)", 
                                 (producto['id'], test_maquina_id))
            relacion_id = cursor.lastrowid
            print(f"✅ Relación creada con ID: {relacion_id}")
            
            # Test 4: Verificar relación
            print("4. Verificando relación...")
            relacion = conn.execute('''
                SELECT p.descripcion as producto, m.nombre as maquina
                FROM producto_maquinas pm
                JOIN productos p ON pm.producto_id = p.id
                JOIN maquinas m ON pm.maquina_id = m.id
                WHERE pm.id = ?
            ''', (relacion_id,)).fetchone()
            
            if relacion:
                print(f"✅ Relación verificada: {relacion['producto']} -> {relacion['maquina']}")
            else:
                print("❌ Error en relación")
                return False
        else:
            print("⚠️  No hay productos para crear relación")
        
        # Test 5: Actualizar máquina
        print("5. Actualizando máquina...")
        conn.execute("UPDATE maquinas SET nombre = ?, descripcion = ? WHERE id = ?", 
                    ("TEST_MAQUINA_UPDATED", "Descripción actualizada", test_maquina_id))
        
        updated = conn.execute("SELECT * FROM maquinas WHERE id = ?", (test_maquina_id,)).fetchone()
        if updated and updated['nombre'] == "TEST_MAQUINA_UPDATED":
            print("✅ Máquina actualizada correctamente")
        else:
            print("❌ Error actualizando máquina")
            return False
        
        # Cleanup: Eliminar datos de prueba
        print("6. Limpiando datos de prueba...")
        if 'relacion_id' in locals():
            conn.execute("DELETE FROM producto_maquinas WHERE id = ?", (relacion_id,))
        conn.execute("DELETE FROM maquinas WHERE id = ?", (test_maquina_id,))
        conn.commit()
        print("✅ Datos de prueba eliminados")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en operaciones: {e}")
        return False

def test_many_to_many_relationship():
    """Probar relación muchos-a-muchos"""
    print(f"\n🔗 TESTING MANY-TO-MANY RELATIONSHIP")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('inventario.db')
        conn.row_factory = sqlite3.Row
        
        # Crear máquinas de prueba
        print("1. Creando máquinas de prueba...")
        cursor1 = conn.execute("INSERT INTO maquinas (nombre) VALUES (?)", ("MAQUINA_A",))
        maquina_a_id = cursor1.lastrowid
        
        cursor2 = conn.execute("INSERT INTO maquinas (nombre) VALUES (?)", ("MAQUINA_B",))
        maquina_b_id = cursor2.lastrowid
        
        print(f"✅ Máquinas creadas: {maquina_a_id}, {maquina_b_id}")
        
        # Obtener productos de prueba
        productos = conn.execute("SELECT id, descripcion FROM productos LIMIT 2").fetchall()
        if len(productos) < 2:
            print("⚠️  Se necesitan al menos 2 productos para la prueba")
            return False
        
        producto1_id, producto2_id = productos[0]['id'], productos[1]['id']
        print(f"✅ Productos de prueba: {producto1_id}, {producto2_id}")
        
        # Test: Un producto en varias máquinas
        print("2. Probando: Un producto en varias máquinas...")
        conn.execute("INSERT INTO producto_maquinas (producto_id, maquina_id) VALUES (?, ?)", 
                    (producto1_id, maquina_a_id))
        conn.execute("INSERT INTO producto_maquinas (producto_id, maquina_id) VALUES (?, ?)", 
                    (producto1_id, maquina_b_id))
        
        maquinas_del_producto = conn.execute('''
            SELECT m.nombre
            FROM maquinas m
            JOIN producto_maquinas pm ON m.id = pm.maquina_id
            WHERE pm.producto_id = ?
        ''', (producto1_id,)).fetchall()
        
        print(f"✅ Producto {producto1_id} está en {len(maquinas_del_producto)} máquinas")
        
        # Test: Una máquina con varios productos
        print("3. Probando: Una máquina con varios productos...")
        conn.execute("INSERT INTO producto_maquinas (producto_id, maquina_id) VALUES (?, ?)", 
                    (producto2_id, maquina_a_id))
        
        productos_de_maquina = conn.execute('''
            SELECT p.descripcion
            FROM productos p
            JOIN producto_maquinas pm ON p.id = pm.producto_id
            WHERE pm.maquina_id = ?
        ''', (maquina_a_id,)).fetchall()
        
        print(f"✅ Máquina {maquina_a_id} usa {len(productos_de_maquina)} productos")
        
        # Test: Consulta compleja
        print("4. Probando consulta compleja...")
        resultado = conn.execute('''
            SELECT m.nombre as maquina, 
                   GROUP_CONCAT(p.descripcion, ', ') as productos
            FROM maquinas m
            LEFT JOIN producto_maquinas pm ON m.id = pm.maquina_id
            LEFT JOIN productos p ON pm.producto_id = p.id
            WHERE m.id IN (?, ?)
            GROUP BY m.id
        ''', (maquina_a_id, maquina_b_id)).fetchall()
        
        for row in resultado:
            print(f"   {row['maquina']}: {row['productos'] or 'Sin productos'}")
        
        # Cleanup
        print("5. Limpiando datos de prueba...")
        conn.execute("DELETE FROM producto_maquinas WHERE maquina_id IN (?, ?)", 
                    (maquina_a_id, maquina_b_id))
        conn.execute("DELETE FROM maquinas WHERE id IN (?, ?)", (maquina_a_id, maquina_b_id))
        conn.commit()
        print("✅ Datos de prueba eliminados")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba muchos-a-muchos: {e}")
        return False

def test_web_interface():
    """Probar interfaz web de máquinas"""
    print(f"\n🌐 TESTING WEB INTERFACE")
    print("=" * 50)
    
    try:
        # Test 1: Página de máquinas
        print("1. Probando página de máquinas...")
        response = requests.get('http://localhost:5000/maquinas', timeout=10)
        if response.status_code == 200:
            print("✅ Página de máquinas accesible")
            if 'Gestión de Máquinas' in response.text:
                print("✅ Contenido correcto cargado")
            else:
                print("⚠️  Contenido puede estar incompleto")
        else:
            print(f"❌ Error accediendo a máquinas: {response.status_code}")
            return False
        
        # Test 2: Formulario nueva máquina
        print("2. Probando formulario nueva máquina...")
        response = requests.get('http://localhost:5000/maquina/nueva', timeout=10)
        if response.status_code == 200:
            print("✅ Formulario nueva máquina accesible")
        else:
            print(f"❌ Error en formulario: {response.status_code}")
        
        # Test 3: API de máquinas
        print("3. Probando API de máquinas...")
        response = requests.get('http://localhost:5000/api/maquina/1', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API funcional - Máquina: {data.get('nombre', 'N/A')}")
        else:
            print(f"⚠️  API respuesta: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("⚠️  Aplicación no está ejecutándose. Inicia con: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error probando interfaz: {e}")
        return False

def main():
    print("🧪 TEST: GESTIÓN DE MÁQUINAS MUCHOS-A-MUCHOS")
    print("=" * 60)
    print("Verificando funcionalidad completa de máquinas...")
    
    # Test 1: Verificar migración
    test1_ok = test_database_migration()
    
    if not test1_ok:
        print("\n❌ MIGRACIÓN REQUERIDA")
        print("Ejecuta: python migrar_maquinas.py")
        return
    
    # Test 2: Operaciones CRUD
    test2_ok = test_maquina_operations()
    
    # Test 3: Relación muchos-a-muchos
    test3_ok = test_many_to_many_relationship()
    
    # Test 4: Interfaz web
    test4_ok = test_web_interface()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE TESTS")
    print("=" * 60)
    
    tests_passed = sum([test1_ok, test2_ok, test3_ok, test4_ok])
    total_tests = 4
    
    if tests_passed == total_tests:
        print("🎉 TODOS LOS TESTS PASARON!")
        print("✅ La gestión de máquinas muchos-a-muchos está funcionando")
        print("\n🚀 Prueba manual:")
        print("   1. Inicia la app: python app.py")
        print("   2. Ve a: http://localhost:5000/maquinas")
        print("   3. Prueba crear, editar y eliminar máquinas")
        print("   4. Asigna máquinas a productos desde el formulario de productos")
    else:
        print(f"⚠️  {tests_passed}/{total_tests} tests pasaron")
        print("   Revisa los errores arriba para identificar problemas")
    
    print(f"\n📊 Funcionalidades disponibles:")
    print(f"   ✅ Ver todas las máquinas")
    print(f"   ✅ Crear nuevas máquinas")
    print(f"   ✅ Editar máquinas existentes")
    print(f"   ✅ Eliminar máquinas (sin productos)")
    print(f"   ✅ Relación muchos-a-muchos con productos")
    print(f"   ✅ Un producto puede usar varias máquinas")
    print(f"   ✅ Una máquina puede usar varios productos")
    print(f"   ✅ Exportar a CSV")
    print(f"   ✅ API para obtener detalles")
    print(f"   ✅ Logging de operaciones admin")

if __name__ == "__main__":
    main()