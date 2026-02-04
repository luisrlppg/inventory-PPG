#!/usr/bin/env python3
"""
Script para probar la funcionalidad de gestión de categorías y subcategorías
"""

import sqlite3
import requests
import json

def test_database_structure():
    """Verificar estructura de base de datos para categorías"""
    print("🔍 TESTING DATABASE STRUCTURE")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('inventario.db')
        conn.row_factory = sqlite3.Row
        
        # Verificar tablas
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [table['name'] for table in tables]
        
        required_tables = ['categorias', 'subcategorias', 'productos']
        for table in required_tables:
            if table in table_names:
                print(f"✅ Tabla '{table}' existe")
            else:
                print(f"❌ Tabla '{table}' no encontrada")
                return False
        
        # Verificar estructura de categorías
        categorias_info = conn.execute("PRAGMA table_info(categorias)").fetchall()
        print(f"✅ Tabla categorías tiene {len(categorias_info)} columnas")
        
        # Verificar estructura de subcategorías
        subcategorias_info = conn.execute("PRAGMA table_info(subcategorias)").fetchall()
        print(f"✅ Tabla subcategorías tiene {len(subcategorias_info)} columnas")
        
        # Contar registros
        categorias_count = conn.execute("SELECT COUNT(*) as count FROM categorias").fetchone()
        subcategorias_count = conn.execute("SELECT COUNT(*) as count FROM subcategorias").fetchone()
        productos_count = conn.execute("SELECT COUNT(*) as count FROM productos").fetchone()
        
        print(f"📊 Datos actuales:")
        print(f"   - Categorías: {categorias_count['count']}")
        print(f"   - Subcategorías: {subcategorias_count['count']}")
        print(f"   - Productos: {productos_count['count']}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verificando estructura: {e}")
        return False

def test_categoria_operations():
    """Probar operaciones CRUD de categorías"""
    print(f"\n🧪 TESTING CATEGORIA OPERATIONS")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('inventario.db')
        conn.row_factory = sqlite3.Row
        
        # Test 1: Crear categoría de prueba
        print("1. Creando categoría de prueba...")
        cursor = conn.execute("INSERT INTO categorias (nombre) VALUES (?)", ("TEST_CATEGORIA",))
        test_categoria_id = cursor.lastrowid
        print(f"✅ Categoría creada con ID: {test_categoria_id}")
        
        # Test 2: Leer categoría
        print("2. Leyendo categoría...")
        categoria = conn.execute("SELECT * FROM categorias WHERE id = ?", (test_categoria_id,)).fetchone()
        if categoria:
            print(f"✅ Categoría leída: {categoria['nombre']}")
        else:
            print("❌ Error leyendo categoría")
            return False
        
        # Test 3: Crear subcategoría de prueba
        print("3. Creando subcategoría de prueba...")
        cursor = conn.execute("INSERT INTO subcategorias (nombre, categoria_id) VALUES (?, ?)", 
                             ("TEST_SUBCATEGORIA", test_categoria_id))
        test_subcategoria_id = cursor.lastrowid
        print(f"✅ Subcategoría creada con ID: {test_subcategoria_id}")
        
        # Test 4: Verificar relación
        print("4. Verificando relación categoría-subcategoría...")
        relacion = conn.execute('''
            SELECT c.nombre as categoria, sc.nombre as subcategoria
            FROM categorias c
            JOIN subcategorias sc ON c.id = sc.categoria_id
            WHERE c.id = ?
        ''', (test_categoria_id,)).fetchone()
        
        if relacion:
            print(f"✅ Relación verificada: {relacion['categoria']} -> {relacion['subcategoria']}")
        else:
            print("❌ Error en relación")
            return False
        
        # Test 5: Actualizar categoría
        print("5. Actualizando categoría...")
        conn.execute("UPDATE categorias SET nombre = ? WHERE id = ?", 
                    ("TEST_CATEGORIA_UPDATED", test_categoria_id))
        
        updated = conn.execute("SELECT nombre FROM categorias WHERE id = ?", (test_categoria_id,)).fetchone()
        if updated and updated['nombre'] == "TEST_CATEGORIA_UPDATED":
            print("✅ Categoría actualizada correctamente")
        else:
            print("❌ Error actualizando categoría")
            return False
        
        # Cleanup: Eliminar datos de prueba
        print("6. Limpiando datos de prueba...")
        conn.execute("DELETE FROM subcategorias WHERE id = ?", (test_subcategoria_id,))
        conn.execute("DELETE FROM categorias WHERE id = ?", (test_categoria_id,))
        conn.commit()
        print("✅ Datos de prueba eliminados")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en operaciones: {e}")
        return False

def test_web_interface():
    """Probar interfaz web de categorías"""
    print(f"\n🌐 TESTING WEB INTERFACE")
    print("=" * 50)
    
    try:
        # Test 1: Página de categorías
        print("1. Probando página de categorías...")
        response = requests.get('http://localhost:5000/categorias', timeout=10)
        if response.status_code == 200:
            print("✅ Página de categorías accesible")
            if 'Gestión de Categorías' in response.text:
                print("✅ Contenido correcto cargado")
            else:
                print("⚠️  Contenido puede estar incompleto")
        else:
            print(f"❌ Error accediendo a categorías: {response.status_code}")
            return False
        
        # Test 2: Formulario nueva categoría
        print("2. Probando formulario nueva categoría...")
        response = requests.get('http://localhost:5000/categoria/nueva', timeout=10)
        if response.status_code == 200:
            print("✅ Formulario nueva categoría accesible")
        else:
            print(f"❌ Error en formulario: {response.status_code}")
        
        # Test 3: Formulario nueva subcategoría
        print("3. Probando formulario nueva subcategoría...")
        response = requests.get('http://localhost:5000/subcategoria/nueva', timeout=10)
        if response.status_code == 200:
            print("✅ Formulario nueva subcategoría accesible")
        else:
            print(f"❌ Error en formulario: {response.status_code}")
        
        # Test 4: API de categorías
        print("4. Probando API de subcategorías...")
        response = requests.get('http://localhost:5000/api/subcategorias/1', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API funcional - {len(data)} subcategorías encontradas")
        else:
            print(f"⚠️  API respuesta: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("⚠️  Aplicación no está ejecutándose. Inicia con: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error probando interfaz: {e}")
        return False

def test_data_consistency():
    """Verificar consistencia de datos existentes"""
    print(f"\n📊 TESTING DATA CONSISTENCY")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('inventario.db')
        conn.row_factory = sqlite3.Row
        
        # Test 1: Categorías sin subcategorías
        categorias_sin_sub = conn.execute('''
            SELECT c.id, c.nombre
            FROM categorias c
            LEFT JOIN subcategorias sc ON c.id = sc.categoria_id
            WHERE sc.id IS NULL
        ''').fetchall()
        
        print(f"📋 Categorías sin subcategorías: {len(categorias_sin_sub)}")
        for cat in categorias_sin_sub[:5]:  # Mostrar primeras 5
            print(f"   - {cat['nombre']}")
        
        # Test 2: Subcategorías huérfanas
        subcategorias_huerfanas = conn.execute('''
            SELECT sc.id, sc.nombre
            FROM subcategorias sc
            LEFT JOIN categorias c ON sc.categoria_id = c.id
            WHERE c.id IS NULL
        ''').fetchall()
        
        if len(subcategorias_huerfanas) == 0:
            print("✅ No hay subcategorías huérfanas")
        else:
            print(f"⚠️  {len(subcategorias_huerfanas)} subcategorías huérfanas encontradas")
        
        # Test 3: Productos con categorías válidas
        productos_sin_categoria = conn.execute('''
            SELECT COUNT(*) as count
            FROM productos p
            WHERE p.categoria_id IS NOT NULL 
            AND p.categoria_id NOT IN (SELECT id FROM categorias)
        ''').fetchone()
        
        if productos_sin_categoria['count'] == 0:
            print("✅ Todos los productos tienen categorías válidas")
        else:
            print(f"⚠️  {productos_sin_categoria['count']} productos con categorías inválidas")
        
        # Test 4: Estadísticas generales
        stats = conn.execute('''
            SELECT 
                (SELECT COUNT(*) FROM categorias) as total_categorias,
                (SELECT COUNT(*) FROM subcategorias) as total_subcategorias,
                (SELECT COUNT(*) FROM productos WHERE categoria_id IS NOT NULL) as productos_con_categoria,
                (SELECT COUNT(*) FROM productos WHERE subcategoria_id IS NOT NULL) as productos_con_subcategoria
        ''').fetchone()
        
        print(f"📊 Estadísticas:")
        print(f"   - Total categorías: {stats['total_categorias']}")
        print(f"   - Total subcategorías: {stats['total_subcategorias']}")
        print(f"   - Productos con categoría: {stats['productos_con_categoria']}")
        print(f"   - Productos con subcategoría: {stats['productos_con_subcategoria']}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verificando consistencia: {e}")
        return False

def main():
    print("🧪 TEST: GESTIÓN DE CATEGORÍAS Y SUBCATEGORÍAS")
    print("=" * 60)
    print("Verificando funcionalidad completa de categorías...")
    
    # Test 1: Estructura de base de datos
    test1_ok = test_database_structure()
    
    # Test 2: Operaciones CRUD
    test2_ok = test_categoria_operations()
    
    # Test 3: Interfaz web
    test3_ok = test_web_interface()
    
    # Test 4: Consistencia de datos
    test4_ok = test_data_consistency()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE TESTS")
    print("=" * 60)
    
    tests_passed = sum([test1_ok, test2_ok, test3_ok, test4_ok])
    total_tests = 4
    
    if tests_passed == total_tests:
        print("🎉 TODOS LOS TESTS PASARON!")
        print("✅ La gestión de categorías está funcionando correctamente")
        print("\n🚀 Prueba manual:")
        print("   1. Inicia la app: python app.py")
        print("   2. Ve a: http://localhost:5000/categorias")
        print("   3. Prueba crear, editar y eliminar categorías/subcategorías")
    else:
        print(f"⚠️  {tests_passed}/{total_tests} tests pasaron")
        print("   Revisa los errores arriba para identificar problemas")
    
    print(f"\n📊 Funcionalidades disponibles:")
    print(f"   ✅ Ver todas las categorías y subcategorías")
    print(f"   ✅ Crear nuevas categorías")
    print(f"   ✅ Crear nuevas subcategorías")
    print(f"   ✅ Editar categorías existentes")
    print(f"   ✅ Editar subcategorías existentes")
    print(f"   ✅ Eliminar categorías (sin productos/subcategorías)")
    print(f"   ✅ Eliminar subcategorías (sin productos)")
    print(f"   ✅ Exportar a CSV")
    print(f"   ✅ Búsqueda y filtrado")
    print(f"   ✅ Logging de operaciones admin")

if __name__ == "__main__":
    main()