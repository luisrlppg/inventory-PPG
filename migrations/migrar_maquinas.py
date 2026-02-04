#!/usr/bin/env python3
"""
Script de migración para cambiar la relación de máquinas de uno-a-muchos a muchos-a-muchos
"""

import sqlite3
import os
from datetime import datetime

def backup_database():
    """Crear backup de la base de datos antes de la migración"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'inventario_backup_before_maquinas_migration_{timestamp}.db'
    
    try:
        import shutil
        shutil.copy2('inventario.db', backup_name)
        print(f"✅ Backup creado: {backup_name}")
        return backup_name
    except Exception as e:
        print(f"❌ Error creando backup: {e}")
        return None

def migrate_maquinas_relationship():
    """Migrar de relación uno-a-muchos a muchos-a-muchos para máquinas"""
    print("🔄 MIGRACIÓN: RELACIÓN MÁQUINAS MUCHOS-A-MUCHOS")
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
        
        # Verificar si ya existe la tabla de relación
        existing_table = cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='producto_maquinas'
        """).fetchone()
        
        if existing_table:
            print("⚠️  La tabla producto_maquinas ya existe. Migración ya realizada.")
            conn.close()
            return True
        
        print("2. Creando tabla de relación producto_maquinas...")
        
        # Crear tabla de relación muchos-a-muchos
        cursor.execute('''
            CREATE TABLE producto_maquinas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                maquina_id INTEGER NOT NULL,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (producto_id) REFERENCES productos (id) ON DELETE CASCADE,
                FOREIGN KEY (maquina_id) REFERENCES maquinas (id) ON DELETE CASCADE,
                UNIQUE(producto_id, maquina_id)
            )
        ''')
        
        print("3. Migrando datos existentes...")
        
        # Obtener productos que tienen máquina asignada
        productos_con_maquina = cursor.execute('''
            SELECT id, maquina_id 
            FROM productos 
            WHERE maquina_id IS NOT NULL
        ''').fetchall()
        
        print(f"   Encontrados {len(productos_con_maquina)} productos con máquina asignada")
        
        # Migrar relaciones existentes
        migrated_count = 0
        for producto in productos_con_maquina:
            try:
                cursor.execute('''
                    INSERT INTO producto_maquinas (producto_id, maquina_id)
                    VALUES (?, ?)
                ''', (producto['id'], producto['maquina_id']))
                migrated_count += 1
            except sqlite3.IntegrityError:
                # Relación ya existe, continuar
                pass
        
        print(f"   ✅ {migrated_count} relaciones migradas")
        
        print("4. Creando nueva tabla productos sin maquina_id...")
        
        # Crear nueva tabla productos sin la columna maquina_id
        cursor.execute('''
            CREATE TABLE productos_new (
                id INTEGER PRIMARY KEY,
                descripcion TEXT NOT NULL,
                codigo TEXT UNIQUE,
                categoria_id INTEGER,
                subcategoria_id INTEGER,
                marca_id INTEGER,
                notas TEXT,
                cantidad_requerida INTEGER DEFAULT 1,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (categoria_id) REFERENCES categorias (id),
                FOREIGN KEY (subcategoria_id) REFERENCES subcategorias (id),
                FOREIGN KEY (marca_id) REFERENCES marcas (id)
            )
        ''')
        
        print("5. Copiando datos de productos...")
        
        # Copiar datos sin la columna maquina_id
        cursor.execute('''
            INSERT INTO productos_new 
            (id, descripcion, codigo, categoria_id, subcategoria_id, marca_id, 
             notas, cantidad_requerida, fecha_creacion, fecha_actualizacion)
            SELECT id, descripcion, codigo, categoria_id, subcategoria_id, marca_id,
                   notas, cantidad_requerida, fecha_creacion, fecha_actualizacion
            FROM productos
        ''')
        
        print("6. Reemplazando tabla productos...")
        
        # Eliminar tabla antigua y renombrar nueva
        cursor.execute('DROP TABLE productos')
        cursor.execute('ALTER TABLE productos_new RENAME TO productos')
        
        print("7. Creando índices para optimización...")
        
        # Crear índices para mejor rendimiento
        cursor.execute('CREATE INDEX idx_producto_maquinas_producto ON producto_maquinas(producto_id)')
        cursor.execute('CREATE INDEX idx_producto_maquinas_maquina ON producto_maquinas(maquina_id)')
        
        print("8. Verificando migración...")
        
        # Verificar que todo está correcto
        productos_count = cursor.execute('SELECT COUNT(*) FROM productos').fetchone()[0]
        relaciones_count = cursor.execute('SELECT COUNT(*) FROM producto_maquinas').fetchone()[0]
        maquinas_count = cursor.execute('SELECT COUNT(*) FROM maquinas').fetchone()[0]
        
        print(f"   ✅ Productos: {productos_count}")
        print(f"   ✅ Relaciones producto-máquina: {relaciones_count}")
        print(f"   ✅ Máquinas: {maquinas_count}")
        
        # Commit de todos los cambios
        conn.commit()
        conn.close()
        
        print("\n🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print(f"📁 Backup guardado en: {backup_file}")
        print("🔄 La base de datos ahora soporta relación muchos-a-muchos para máquinas")
        
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
        
        # Verificar que existe la tabla producto_maquinas
        table_exists = cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='producto_maquinas'
        """).fetchone()
        
        if not table_exists:
            print("❌ Tabla producto_maquinas no existe")
            return False
        
        print("✅ Tabla producto_maquinas existe")
        
        # Verificar que la tabla productos no tiene maquina_id
        columns = cursor.execute("PRAGMA table_info(productos)").fetchall()
        column_names = [col['name'] for col in columns]
        
        if 'maquina_id' in column_names:
            print("❌ Columna maquina_id aún existe en productos")
            return False
        
        print("✅ Columna maquina_id eliminada de productos")
        
        # Verificar datos
        relaciones = cursor.execute('SELECT COUNT(*) FROM producto_maquinas').fetchone()[0]
        print(f"✅ {relaciones} relaciones producto-máquina encontradas")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verificando migración: {e}")
        return False

def main():
    print("🚀 MIGRACIÓN DE MÁQUINAS A RELACIÓN MUCHOS-A-MUCHOS")
    print("=" * 60)
    print("Este script migrará la base de datos para permitir que:")
    print("- Un producto pueda usarse en varias máquinas")
    print("- Una máquina pueda usar varios productos")
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
    if migrate_maquinas_relationship():
        # Verificar migración
        if verify_migration():
            print("\n🎉 MIGRACIÓN COMPLETADA Y VERIFICADA")
            print("\nPróximos pasos:")
            print("1. Actualizar el código de la aplicación")
            print("2. Probar la nueva funcionalidad")
            print("3. Eliminar el backup si todo funciona correctamente")
        else:
            print("\n⚠️  Migración completada pero verificación falló")
    else:
        print("\n❌ Migración falló")

if __name__ == "__main__":
    main()