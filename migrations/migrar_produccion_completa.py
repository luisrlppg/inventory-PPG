#!/usr/bin/env python3
"""
Script de migración completa para base de datos de producción
Migra bkpinventario.db con todas las nuevas funcionalidades:
- Sistema de categorías y subcategorías
- Sistema de máquinas (relación N:M)
- Sistema de proveedores
- Tablas de administración y logs
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_database(source_db):
    """Crear backup de seguridad de la base de datos"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'{source_db}_backup_before_full_migration_{timestamp}.db'
    
    try:
        shutil.copy2(source_db, backup_name)
        print(f"✅ Backup creado: {backup_name}")
        return backup_name
    except Exception as e:
        print(f"❌ Error creando backup: {e}")
        return None

def analyze_current_structure(db_path):
    """Analizar estructura actual de la base de datos"""
    print(f"🔍 ANALIZANDO ESTRUCTURA DE {db_path}")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Obtener todas las tablas
        tables = cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()
        
        print("📋 Tablas existentes:")
        table_info = {}
        
        for table in tables:
            table_name = table['name']
            
            # Obtener columnas de cada tabla
            columns = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
            column_names = [col['name'] for col in columns]
            
            # Contar registros
            count = cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}").fetchone()['count']
            
            table_info[table_name] = {
                'columns': column_names,
                'count': count
            }
            
            print(f"   📊 {table_name}: {count} registros")
            print(f"      Columnas: {', '.join(column_names)}")
        
        conn.close()
        return table_info
        
    except Exception as e:
        print(f"❌ Error analizando estructura: {e}")
        return {}

def create_missing_tables(conn):
    """Crear tablas que faltan en la base de datos de producción"""
    cursor = conn.cursor()
    
    print("🏗️  CREANDO TABLAS FALTANTES")
    print("=" * 40)
    
    # 1. Tabla de categorías
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Tabla 'categorias' verificada/creada")
    except Exception as e:
        print(f"⚠️  Error con tabla categorias: {e}")
    
    # 2. Tabla de subcategorías
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subcategorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                categoria_id INTEGER NOT NULL,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (categoria_id) REFERENCES categorias(id),
                UNIQUE(nombre, categoria_id)
            )
        ''')
        print("✅ Tabla 'subcategorias' verificada/creada")
    except Exception as e:
        print(f"⚠️  Error con tabla subcategorias: {e}")
    
    # 3. Tabla de máquinas
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS maquinas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                descripcion TEXT,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Tabla 'maquinas' verificada/creada")
    except Exception as e:
        print(f"⚠️  Error con tabla maquinas: {e}")
    
    # 4. Tabla de relación producto-máquinas (N:M)
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS producto_maquinas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                maquina_id INTEGER NOT NULL,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
                FOREIGN KEY (maquina_id) REFERENCES maquinas(id) ON DELETE CASCADE,
                UNIQUE(producto_id, maquina_id)
            )
        ''')
        print("✅ Tabla 'producto_maquinas' verificada/creada")
    except Exception as e:
        print(f"⚠️  Error con tabla producto_maquinas: {e}")
    
    # 5. Tabla de proveedores
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                contacto TEXT,
                telefono TEXT,
                email TEXT,
                pagina_web TEXT,
                direccion TEXT,
                notas TEXT,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Tabla 'proveedores' verificada/creada")
    except Exception as e:
        print(f"⚠️  Error con tabla proveedores: {e}")
    
    # 6. Tabla de usuarios administradores
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')
        print("✅ Tabla 'admin_users' verificada/creada")
    except Exception as e:
        print(f"⚠️  Error con tabla admin_users: {e}")
    
    # 7. Tabla de sesiones de administradores
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                FOREIGN KEY (admin_user_id) REFERENCES admin_users(id) ON DELETE CASCADE
            )
        ''')
        print("✅ Tabla 'admin_sessions' verificada/creada")
    except Exception as e:
        print(f"⚠️  Error con tabla admin_sessions: {e}")
    
    # 8. Tabla de logs de operaciones
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_user_id INTEGER,
                operation_type TEXT NOT NULL,
                producto_id INTEGER,
                ubicacion_id INTEGER,
                old_quantity INTEGER,
                new_quantity INTEGER,
                description TEXT,
                ip_address TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_user_id) REFERENCES admin_users(id),
                FOREIGN KEY (producto_id) REFERENCES productos(id),
                FOREIGN KEY (ubicacion_id) REFERENCES ubicaciones(id)
            )
        ''')
        print("✅ Tabla 'operation_logs' verificada/creada")
    except Exception as e:
        print(f"⚠️  Error con tabla operation_logs: {e}")

def add_missing_columns(conn):
    """Agregar columnas faltantes a tablas existentes"""
    cursor = conn.cursor()
    
    print("\n🔧 AGREGANDO COLUMNAS FALTANTES")
    print("=" * 40)
    
    # Obtener estructura actual de productos
    productos_columns = cursor.execute("PRAGMA table_info(productos)").fetchall()
    productos_column_names = [col['name'] for col in productos_columns]
    
    # Agregar columnas a productos si no existen
    columns_to_add = [
        ('categoria_id', 'INTEGER REFERENCES categorias(id)'),
        ('subcategoria_id', 'INTEGER REFERENCES subcategorias(id)'),
        ('proveedor_id', 'INTEGER REFERENCES proveedores(id)'),
        ('cantidad_requerida', 'INTEGER DEFAULT 1'),
        ('fecha_creacion', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
        ('fecha_actualizacion', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
    ]
    
    for column_name, column_def in columns_to_add:
        if column_name not in productos_column_names:
            try:
                cursor.execute(f'ALTER TABLE productos ADD COLUMN {column_name} {column_def}')
                print(f"✅ Columna '{column_name}' agregada a productos")
            except Exception as e:
                print(f"⚠️  Error agregando columna {column_name}: {e}")
        else:
            print(f"✅ Columna '{column_name}' ya existe en productos")
    
    # Verificar tabla ubicaciones
    try:
        ubicaciones_columns = cursor.execute("PRAGMA table_info(ubicaciones)").fetchall()
        ubicaciones_column_names = [col['name'] for col in ubicaciones_columns]
        
        if 'fecha_creacion' not in ubicaciones_column_names:
            cursor.execute('ALTER TABLE ubicaciones ADD COLUMN fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP')
            print("✅ Columna 'fecha_creacion' agregada a ubicaciones")
        
        if 'fecha_actualizacion' not in ubicaciones_column_names:
            cursor.execute('ALTER TABLE ubicaciones ADD COLUMN fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP')
            print("✅ Columna 'fecha_actualizacion' agregada a ubicaciones")
            
    except Exception as e:
        print(f"⚠️  Error con columnas de ubicaciones: {e}")

def create_indexes(conn):
    """Crear índices para optimización"""
    cursor = conn.cursor()
    
    print("\n📊 CREANDO ÍNDICES DE OPTIMIZACIÓN")
    print("=" * 40)
    
    indexes = [
        ('idx_productos_categoria', 'productos(categoria_id)'),
        ('idx_productos_subcategoria', 'productos(subcategoria_id)'),
        ('idx_productos_proveedor', 'productos(proveedor_id)'),
        ('idx_productos_descripcion', 'productos(descripcion)'),
        ('idx_inventario_producto', 'inventario(producto_id)'),
        ('idx_inventario_ubicacion', 'inventario(ubicacion_id)'),
        ('idx_ubicaciones_codigo', 'ubicaciones(codigo)'),
        ('idx_categorias_nombre', 'categorias(nombre)'),
        ('idx_subcategorias_categoria', 'subcategorias(categoria_id)'),
        ('idx_maquinas_nombre', 'maquinas(nombre)'),
        ('idx_proveedores_nombre', 'proveedores(nombre)'),
        ('idx_producto_maquinas_producto', 'producto_maquinas(producto_id)'),
        ('idx_producto_maquinas_maquina', 'producto_maquinas(maquina_id)'),
        ('idx_operation_logs_timestamp', 'operation_logs(timestamp)'),
        ('idx_operation_logs_admin', 'operation_logs(admin_user_id)')
    ]
    
    for index_name, index_def in indexes:
        try:
            cursor.execute(f'CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}')
            print(f"✅ Índice '{index_name}' creado")
        except Exception as e:
            print(f"⚠️  Error creando índice {index_name}: {e}")

def insert_default_data(conn):
    """Insertar datos por defecto"""
    cursor = conn.cursor()
    
    print("\n📝 INSERTANDO DATOS POR DEFECTO")
    print("=" * 40)
    
    # Insertar usuario administrador por defecto
    try:
        import hashlib
        admin_password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        
        cursor.execute('''
            INSERT OR IGNORE INTO admin_users (username, password_hash)
            VALUES (?, ?)
        ''', ('admin', admin_password_hash))
        print("✅ Usuario administrador por defecto creado (admin/admin123)")
    except Exception as e:
        print(f"⚠️  Error creando usuario admin: {e}")
    
    # Insertar categorías de ejemplo
    categorias_ejemplo = [
        'Herramientas',
        'Refacciones',
        'Consumibles',
        'Equipos',
        'Materiales'
    ]
    
    for categoria in categorias_ejemplo:
        try:
            cursor.execute('INSERT OR IGNORE INTO categorias (nombre) VALUES (?)', (categoria,))
        except Exception as e:
            print(f"⚠️  Error insertando categoría {categoria}: {e}")
    
    print("✅ Categorías de ejemplo insertadas")
    
    # Insertar máquinas de ejemplo
    maquinas_ejemplo = [
        ('Máquina General', 'Máquina por defecto'),
        ('Torno', 'Torno industrial'),
        ('Fresadora', 'Fresadora CNC'),
        ('Soldadora', 'Equipo de soldadura')
    ]
    
    for nombre, descripcion in maquinas_ejemplo:
        try:
            cursor.execute('INSERT OR IGNORE INTO maquinas (nombre, descripcion) VALUES (?, ?)', 
                          (nombre, descripcion))
        except Exception as e:
            print(f"⚠️  Error insertando máquina {nombre}: {e}")
    
    print("✅ Máquinas de ejemplo insertadas")
    
    # Insertar proveedores de ejemplo
    proveedores_ejemplo = [
        ('Proveedor General', 'Contacto General', '555-0001', 'contacto@general.com', 'www.general.com', 'Dirección General', 'Proveedor por defecto'),
        ('Suministros Industriales', 'Juan Pérez', '555-0002', 'ventas@industriales.com', 'www.industriales.com', 'Zona Industrial', 'Especialista en herramientas'),
        ('Refacciones PPG', 'María González', '555-0003', 'info@refaccionesppg.com', 'www.refaccionesppg.com', 'Centro de la ciudad', 'Proveedor especializado')
    ]
    
    for proveedor in proveedores_ejemplo:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO proveedores 
                (nombre, contacto, telefono, email, pagina_web, direccion, notas)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', proveedor)
        except Exception as e:
            print(f"⚠️  Error insertando proveedor {proveedor[0]}: {e}")
    
    print("✅ Proveedores de ejemplo insertados")

def migrate_existing_data(conn):
    """Migrar datos existentes si es necesario"""
    cursor = conn.cursor()
    
    print("\n🔄 MIGRANDO DATOS EXISTENTES")
    print("=" * 40)
    
    # Si existe la columna maquina_id en productos, migrar a la relación N:M
    try:
        productos_columns = cursor.execute("PRAGMA table_info(productos)").fetchall()
        column_names = [col['name'] for col in productos_columns]
        
        if 'maquina_id' in column_names:
            print("🔄 Migrando relación 1:N a N:M para máquinas...")
            
            # Obtener productos con maquina_id
            productos_con_maquina = cursor.execute('''
                SELECT id, maquina_id FROM productos 
                WHERE maquina_id IS NOT NULL
            ''').fetchall()
            
            # Insertar en tabla de relación N:M
            for producto in productos_con_maquina:
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO producto_maquinas (producto_id, maquina_id)
                        VALUES (?, ?)
                    ''', (producto['id'], producto['maquina_id']))
                except Exception as e:
                    print(f"⚠️  Error migrando producto {producto['id']}: {e}")
            
            print(f"✅ {len(productos_con_maquina)} relaciones producto-máquina migradas")
            
            # Opcional: Eliminar columna maquina_id (comentado por seguridad)
            # print("⚠️  Columna maquina_id mantenida por seguridad")
        
    except Exception as e:
        print(f"⚠️  Error en migración de máquinas: {e}")

def verify_migration(conn):
    """Verificar que la migración fue exitosa"""
    cursor = conn.cursor()
    
    print("\n✅ VERIFICANDO MIGRACIÓN")
    print("=" * 30)
    
    # Verificar tablas principales
    tables_to_check = [
        'productos', 'inventario', 'ubicaciones', 'categorias', 
        'subcategorias', 'maquinas', 'producto_maquinas', 'proveedores',
        'admin_users', 'admin_sessions', 'operation_logs'
    ]
    
    for table in tables_to_check:
        try:
            count = cursor.execute(f'SELECT COUNT(*) as count FROM {table}').fetchone()['count']
            print(f"✅ {table}: {count} registros")
        except Exception as e:
            print(f"❌ Error verificando {table}: {e}")
    
    # Verificar columnas críticas en productos
    productos_columns = cursor.execute("PRAGMA table_info(productos)").fetchall()
    critical_columns = ['categoria_id', 'subcategoria_id', 'proveedor_id', 'cantidad_requerida']
    
    print("\n📋 Columnas en productos:")
    for col in productos_columns:
        status = "✅" if col['name'] in critical_columns else "📄"
        print(f"   {status} {col['name']} ({col['type']})")

def main():
    """Función principal de migración"""
    print("🚀 MIGRACIÓN COMPLETA DE BASE DE DATOS DE PRODUCCIÓN")
    print("=" * 70)
    print("Este script migrará bkpinventario.db con todas las nuevas funcionalidades:")
    print("- Sistema de categorías y subcategorías")
    print("- Sistema de máquinas (relación N:M)")
    print("- Sistema de proveedores")
    print("- Sistema de administración y logs")
    print("- Índices de optimización")
    print()
    
    # Verificar que existe la base de datos de producción
    if not os.path.exists('bkpinventario.db'):
        print("❌ No se encontró bkpinventario.db")
        print("💡 Asegúrate de que el archivo esté en el directorio actual")
        return
    
    # Analizar estructura actual
    current_structure = analyze_current_structure('bkpinventario.db')
    
    # Confirmar migración
    print(f"\n⚠️  IMPORTANTE: Se va a modificar bkpinventario.db")
    print("Se creará un backup automático antes de proceder.")
    respuesta = input("\n¿Continuar con la migración completa? (s/N): ")
    if respuesta.lower() != 's':
        print("Migración cancelada")
        return
    
    # Crear backup
    backup_file = backup_database('bkpinventario.db')
    if not backup_file:
        print("❌ No se pudo crear backup. Abortando migración.")
        return
    
    try:
        # Conectar a la base de datos de producción
        conn = sqlite3.connect('bkpinventario.db')
        conn.row_factory = sqlite3.Row
        
        # Configurar WAL mode para mejor rendimiento
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA foreign_keys=ON')
        
        print(f"\n🔄 INICIANDO MIGRACIÓN DE bkpinventario.db")
        print("=" * 50)
        
        # Ejecutar pasos de migración
        create_missing_tables(conn)
        add_missing_columns(conn)
        create_indexes(conn)
        insert_default_data(conn)
        migrate_existing_data(conn)
        
        # Commit de todos los cambios
        conn.commit()
        
        # Verificar migración
        verify_migration(conn)
        
        conn.close()
        
        print("\n🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 50)
        print(f"✅ Base de datos migrada: bkpinventario.db")
        print(f"📁 Backup guardado en: {backup_file}")
        print("🏢 Todas las nuevas funcionalidades agregadas")
        print("\nPróximos pasos:")
        print("1. Renombrar bkpinventario.db a inventario.db")
        print("2. Probar la aplicación con la nueva base de datos")
        print("3. Verificar que todos los datos se mantuvieron")
        print("4. Eliminar el backup si todo funciona correctamente")
        
    except Exception as e:
        print(f"\n❌ ERROR EN MIGRACIÓN: {e}")
        print("🔄 Restaurando desde backup...")
        
        try:
            shutil.copy2(backup_file, 'bkpinventario.db')
            print("✅ Base de datos restaurada desde backup")
        except Exception as restore_error:
            print(f"❌ Error restaurando backup: {restore_error}")
            print(f"⚠️  Restaura manualmente desde: {backup_file}")

if __name__ == "__main__":
    main()