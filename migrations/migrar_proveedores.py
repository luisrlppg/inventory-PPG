#!/usr/bin/env python3
"""
Script de migración para agregar sistema de proveedores
"""

import sqlite3
import os
from datetime import datetime

def backup_database():
    """Crear backup de la base de datos antes de la migración"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'inventario_backup_before_proveedores_migration_{timestamp}.db'
    
    try:
        import shutil
        shutil.copy2('inventario.db', backup_name)
        print(f"✅ Backup creado: {backup_name}")
        return backup_name
    except Exception as e:
        print(f"❌ Error creando backup: {e}")
        return None

def migrate_proveedores():
    """Agregar tabla de proveedores y campo proveedor_id a productos"""
    print("🔄 MIGRACIÓN: SISTEMA DE PROVEEDORES")
    print("=" * 60)
    
    # Crear backup
    backup_file = backup_database()
    if not backup_file:
        print("❌ No se pudo crear backup. Abortando migración.")
        return False
    
    try:
        conn = sqlite3.connect('inventario.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("1. Verificando estructura actual...")
        
        # Verificar si ya existe la tabla de proveedores
        existing_table = cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='proveedores'
        """).fetchone()
        
        if existing_table:
            print("⚠️  La tabla proveedores ya existe. Verificando estructura...")
        else:
            print("2. Creando tabla de proveedores...")
            
            # Crear tabla de proveedores
            cursor.execute('''
                CREATE TABLE proveedores (
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
            print("✅ Tabla proveedores creada")
        
        print("3. Verificando columna proveedor_id en productos...")
        
        # Verificar si ya existe la columna proveedor_id en productos
        columns = cursor.execute("PRAGMA table_info(productos)").fetchall()
        column_names = [col['name'] for col in columns]
        
        if 'proveedor_id' in column_names:
            print("⚠️  La columna proveedor_id ya existe en productos")
        else:
            print("4. Agregando columna proveedor_id a productos...")
            
            # Agregar columna proveedor_id a productos
            cursor.execute('''
                ALTER TABLE productos 
                ADD COLUMN proveedor_id INTEGER 
                REFERENCES proveedores(id)
            ''')
            print("✅ Columna proveedor_id agregada a productos")
        
        print("5. Creando índices para optimización...")
        
        # Crear índices para mejor rendimiento
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_productos_proveedor ON productos(proveedor_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_proveedores_nombre ON proveedores(nombre)')
            print("✅ Índices creados")
        except Exception as e:
            print(f"⚠️  Algunos índices ya existían: {e}")
        
        print("6. Insertando proveedores de ejemplo...")
        
        # Insertar algunos proveedores de ejemplo
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
        
        print("7. Verificando migración...")
        
        # Verificar que todo está correcto
        proveedores_count = cursor.execute('SELECT COUNT(*) FROM proveedores').fetchone()[0]
        productos_count = cursor.execute('SELECT COUNT(*) FROM productos').fetchone()[0]
        
        print(f"   ✅ Proveedores: {proveedores_count}")
        print(f"   ✅ Productos: {productos_count}")
        
        # Verificar estructura de proveedores
        prov_columns = cursor.execute("PRAGMA table_info(proveedores)").fetchall()
        expected_columns = ['id', 'nombre', 'contacto', 'telefono', 'email', 'pagina_web', 'direccion', 'notas']
        
        for col in expected_columns:
            if col in [c['name'] for c in prov_columns]:
                print(f"   ✅ Columna '{col}' existe en proveedores")
            else:
                print(f"   ❌ Columna '{col}' falta en proveedores")
        
        # Commit de todos los cambios
        conn.commit()
        conn.close()
        
        print("\n🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print(f"📁 Backup guardado en: {backup_file}")
        print("🏢 Sistema de proveedores agregado con éxito")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN MIGRACIÓN: {e}")
        print("🔄 Restaurando desde backup...")
        
        try:
            conn.rollback()
            conn.close()
            
            # Restaurar backup
            import shutil
            shutil.copy2(backup_file, 'inventario.db')
            print("✅ Base de datos restaurada desde backup")
            
        except Exception as restore_error:
            print(f"❌ Error restaurando backup: {restore_error}")
            print(f"⚠️  Restaura manualmente desde: {backup_file}")
        
        return False

def verify_migration():
    """Verificar que la migración se completó correctamente"""
    print("\n🔍 VERIFICANDO MIGRACIÓN")
    print("=" * 30)
    
    try:
        conn = sqlite3.connect('inventario.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verificar que existe la tabla proveedores
        table_exists = cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='proveedores'
        """).fetchone()
        
        if not table_exists:
            print("❌ Tabla proveedores no existe")
            return False
        
        print("✅ Tabla proveedores existe")
        
        # Verificar que la tabla productos tiene proveedor_id
        columns = cursor.execute("PRAGMA table_info(productos)").fetchall()
        column_names = [col['name'] for col in columns]
        
        if 'proveedor_id' not in column_names:
            print("❌ Columna proveedor_id no existe en productos")
            return False
        
        print("✅ Columna proveedor_id agregada a productos")
        
        # Verificar datos
        proveedores = cursor.execute('SELECT COUNT(*) FROM proveedores').fetchone()[0]
        print(f"✅ {proveedores} proveedores encontrados")
        
        # Verificar estructura completa de proveedores
        sample_proveedor = cursor.execute('SELECT * FROM proveedores LIMIT 1').fetchone()
        if sample_proveedor:
            print("✅ Estructura de proveedores verificada")
            print(f"   Ejemplo: {sample_proveedor['nombre']}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verificando migración: {e}")
        return False

def main():
    print("🏢 MIGRACIÓN DE PROVEEDORES")
    print("=" * 60)
    print("Este script agregará:")
    print("- Tabla 'proveedores' con información de contacto")
    print("- Campo 'proveedor_id' en tabla 'productos'")
    print("- Proveedores de ejemplo")
    print("- Índices para optimización")
    print()
    
    if not os.path.exists('inventario.db'):
        print("❌ No se encontró inventario.db")
        return
    
    # Confirmar migración
    respuesta = input("¿Continuar con la migración? (s/N): ")
    if respuesta.lower() != 's':
        print("Migración cancelada")
        return
    
    # Ejecutar migración
    if migrate_proveedores():
        # Verificar migración
        if verify_migration():
            print("\n🎉 MIGRACIÓN COMPLETADA Y VERIFICADA")
            print("\nPróximos pasos:")
            print("1. Actualizar el código de la aplicación")
            print("2. Probar la nueva funcionalidad de proveedores")
            print("3. Asignar proveedores a productos existentes")
            print("4. Eliminar el backup si todo funciona correctamente")
        else:
            print("\n⚠️  Migración completada pero verificación falló")
    else:
        print("\n❌ Migración falló")

if __name__ == "__main__":
    main()