import sqlite3
import csv
from datetime import datetime

# Inicializar base de datos
def init_db():
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    
    # Tabla de categorías
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            descripcion TEXT
        )
    ''')
    
    # Tabla de subcategorías
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subcategorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria_id INTEGER,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id)
        )
    ''')
    
    # Tabla de marcas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS marcas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Tabla de máquinas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maquinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            descripcion TEXT
        )
    ''')
    
    # Tabla de ubicaciones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ubicaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            empresa TEXT DEFAULT 'PPG',
            area TEXT DEFAULT 'Oficinas',
            nivel TEXT DEFAULT 'Planta Alta',
            seccion TEXT DEFAULT 'Anaquel Refacciones Maq Cepillo'
        )
    ''')
    
    # Tabla principal de productos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY,
            descripcion TEXT NOT NULL,
            codigo TEXT UNIQUE,
            categoria_id INTEGER,
            subcategoria_id INTEGER,
            marca_id INTEGER,
            notas TEXT,
            cantidad_requerida INTEGER DEFAULT 1,
            maquina_id INTEGER,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id),
            FOREIGN KEY (subcategoria_id) REFERENCES subcategorias (id),
            FOREIGN KEY (marca_id) REFERENCES marcas (id),
            FOREIGN KEY (maquina_id) REFERENCES maquinas (id)
        )
    ''')
    
    # Tabla de inventario (stock por ubicación)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            ubicacion_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL DEFAULT 0,
            fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (producto_id) REFERENCES productos (id),
            FOREIGN KEY (ubicacion_id) REFERENCES ubicaciones (id),
            UNIQUE(producto_id, ubicacion_id)
        )
    ''')
    
    conn.commit()
    return conn

def importar_productos():
    """Importar productos desde el CSV"""
    conn = init_db()
    cursor = conn.cursor()
    
    print("=== IMPORTANDO PRODUCTOS ===\n")
    
    # Leer productos del CSV
    with open('Productos.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        productos_importados = 0
        
        for row in reader:
            try:
                # Obtener o crear categoría
                categoria_id = None
                if row['Categoria'].strip():
                    cursor.execute('INSERT OR IGNORE INTO categorias (nombre) VALUES (?)', 
                                 (row['Categoria'].strip(),))
                    cursor.execute('SELECT id FROM categorias WHERE nombre = ?', 
                                 (row['Categoria'].strip(),))
                    categoria_id = cursor.fetchone()[0]
                
                # Obtener o crear subcategoría
                subcategoria_id = None
                if row['SubCategoria'].strip() and categoria_id:
                    cursor.execute('INSERT OR IGNORE INTO subcategorias (nombre, categoria_id) VALUES (?, ?)', 
                                 (row['SubCategoria'].strip(), categoria_id))
                    cursor.execute('SELECT id FROM subcategorias WHERE nombre = ? AND categoria_id = ?', 
                                 (row['SubCategoria'].strip(), categoria_id))
                    result = cursor.fetchone()
                    if result:
                        subcategoria_id = result[0]
                
                # Obtener o crear marca
                marca_id = None
                if row['Marca'].strip():
                    cursor.execute('INSERT OR IGNORE INTO marcas (nombre) VALUES (?)', 
                                 (row['Marca'].strip(),))
                    cursor.execute('SELECT id FROM marcas WHERE nombre = ?', 
                                 (row['Marca'].strip(),))
                    marca_id = cursor.fetchone()[0]
                
                # Obtener o crear máquina
                maquina_id = None
                if row['Maquina'].strip():
                    cursor.execute('INSERT OR IGNORE INTO maquinas (nombre) VALUES (?)', 
                                 (row['Maquina'].strip(),))
                    cursor.execute('SELECT id FROM maquinas WHERE nombre = ?', 
                                 (row['Maquina'].strip(),))
                    maquina_id = cursor.fetchone()[0]
                
                # Insertar producto
                producto_id = int(row['ID']) if row['ID'].strip() else None
                if producto_id:
                    cursor.execute('''
                        INSERT OR REPLACE INTO productos 
                        (id, descripcion, codigo, categoria_id, subcategoria_id, marca_id, 
                         notas, cantidad_requerida, maquina_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        producto_id,
                        row['Descripcion'].strip(),
                        row['Codigo'].strip() if row['Codigo'].strip() else None,
                        categoria_id,
                        subcategoria_id,
                        marca_id,
                        row['Notas Adicionales'].strip() if row['Notas Adicionales'].strip() else None,
                        int(row['Cantidad Requerida por Maquina']) if row['Cantidad Requerida por Maquina'].strip() else 1,
                        maquina_id
                    ))
                    productos_importados += 1
                    
                    if productos_importados % 10 == 0:
                        print(f"Importados {productos_importados} productos...")
                
            except Exception as e:
                print(f"Error importando producto {row.get('ID', 'N/A')}: {e}")
    
    conn.commit()
    print(f"\n✅ Productos importados: {productos_importados}")
    return conn

def importar_inventario():
    """Importar inventario desde el CSV"""
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    
    print("\n=== IMPORTANDO INVENTARIO ===\n")
    
    # Leer inventario del CSV
    with open('Inventario.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        inventario_importado = 0
        
        for row in reader:
            try:
                # Buscar producto por nombre o ProductoID
                producto_id = None
                if row['ProductoID'].strip():
                    producto_id = int(row['ProductoID'])
                else:
                    # Buscar por nombre del producto
                    cursor.execute('SELECT id FROM productos WHERE descripcion LIKE ?', 
                                 (f"%{row['Producto'].strip()}%",))
                    result = cursor.fetchone()
                    if result:
                        producto_id = result[0]
                
                if not producto_id:
                    print(f"⚠️  Producto no encontrado: {row['Producto']}")
                    continue
                
                # Obtener o crear ubicación
                ubicacion_codigo = row['UbicacionPrincipal'].strip()
                if ubicacion_codigo:
                    cursor.execute('INSERT OR IGNORE INTO ubicaciones (codigo, nombre, empresa, area, nivel, seccion) VALUES (?, ?, ?, ?, ?, ?)', 
                                 (ubicacion_codigo, 
                                  ubicacion_codigo,
                                  row['Empresa'].strip() if row['Empresa'].strip() else 'PPG',
                                  row['Area'].strip() if row['Area'].strip() else 'Oficinas',
                                  row['Nivel'].strip() if row['Nivel'].strip() else 'Planta Alta',
                                  row['Seccion'].strip() if row['Seccion'].strip() else 'Anaquel Refacciones Maq Cepillo'))
                    
                    cursor.execute('SELECT id FROM ubicaciones WHERE codigo = ?', (ubicacion_codigo,))
                    ubicacion_id = cursor.fetchone()[0]
                    
                    # Insertar en inventario
                    cantidad = row['Cantidad'].strip()
                    if cantidad.isdigit():
                        cantidad_num = int(cantidad)
                    elif cantidad.lower() == 'varios':
                        cantidad_num = 1  # Asignar 1 para "varios"
                    else:
                        cantidad_num = 0
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO inventario (producto_id, ubicacion_id, cantidad)
                        VALUES (?, ?, ?)
                    ''', (producto_id, ubicacion_id, cantidad_num))
                    
                    inventario_importado += 1
                    
                    if inventario_importado % 10 == 0:
                        print(f"Importados {inventario_importado} registros de inventario...")
                
            except Exception as e:
                print(f"Error importando inventario para {row.get('Producto', 'N/A')}: {e}")
    
    conn.commit()
    conn.close()
    print(f"\n✅ Registros de inventario importados: {inventario_importado}")

def mostrar_estadisticas():
    """Mostrar estadísticas de la importación"""
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    
    print("\n=== ESTADÍSTICAS DE LA BASE DE DATOS ===")
    
    stats = {}
    stats['productos'] = cursor.execute('SELECT COUNT(*) FROM productos').fetchone()[0]
    stats['categorias'] = cursor.execute('SELECT COUNT(*) FROM categorias').fetchone()[0]
    stats['subcategorias'] = cursor.execute('SELECT COUNT(*) FROM subcategorias').fetchone()[0]
    stats['marcas'] = cursor.execute('SELECT COUNT(*) FROM marcas').fetchone()[0]
    stats['maquinas'] = cursor.execute('SELECT COUNT(*) FROM maquinas').fetchone()[0]
    stats['ubicaciones'] = cursor.execute('SELECT COUNT(*) FROM ubicaciones').fetchone()[0]
    stats['inventario'] = cursor.execute('SELECT COUNT(*) FROM inventario').fetchone()[0]
    stats['stock_total'] = cursor.execute('SELECT COALESCE(SUM(cantidad), 0) FROM inventario').fetchone()[0]
    
    for key, value in stats.items():
        print(f"   {key.capitalize()}: {value}")
    
    conn.close()

if __name__ == '__main__':
    print("🚀 INICIANDO IMPORTACIÓN DE DATOS\n")
    
    # Importar productos
    importar_productos()
    
    # Importar inventario
    importar_inventario()
    
    # Mostrar estadísticas
    mostrar_estadisticas()
    
    print(f"\n✅ IMPORTACIÓN COMPLETADA")
    print(f"📁 Base de datos creada: inventario.db")
    print(f"🌐 Ejecuta 'python app.py' para iniciar la aplicación web")