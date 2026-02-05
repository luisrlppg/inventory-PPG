#!/usr/bin/env python3
"""
Migración: Agregar campo stock_minimo a la tabla productos
Fecha: 2026-02-05
Descripción: Agrega el campo stock_minimo para configurar alertas de stock bajo
"""

import sqlite3
import os
from datetime import datetime

def agregar_stock_minimo():
    """Agregar campo stock_minimo a la tabla productos"""
    
    # Verificar que existe la base de datos
    if not os.path.exists('inventario.db'):
        print("❌ Error: No se encontró la base de datos inventario.db")
        return False
    
    # Crear backup antes de la migración
    backup_name = f"inventario_backup_before_stock_minimo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    print(f"📦 Creando backup: {backup_name}")
    
    try:
        import shutil
        shutil.copy2('inventario.db', backup_name)
        print(f"✅ Backup creado exitosamente")
    except Exception as e:
        print(f"❌ Error creando backup: {e}")
        return False
    
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    
    try:
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(productos)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'stock_minimo' in columns:
            print("ℹ️  La columna stock_minimo ya existe en la tabla productos")
            conn.close()
            return True
        
        print("🔄 Agregando columna stock_minimo a la tabla productos...")
        
        # Agregar la columna stock_minimo
        cursor.execute('''
            ALTER TABLE productos 
            ADD COLUMN stock_minimo INTEGER DEFAULT 5
        ''')
        
        # Actualizar productos existentes con valores por defecto basados en categoría
        print("🔄 Configurando valores por defecto de stock mínimo...")
        
        # Stock mínimo por categoría (puedes ajustar estos valores)
        cursor.execute('''
            UPDATE productos 
            SET stock_minimo = CASE 
                WHEN categoria_id IN (
                    SELECT id FROM categorias WHERE nombre LIKE '%Crítico%' OR nombre LIKE '%Esencial%'
                ) THEN 10
                WHEN categoria_id IN (
                    SELECT id FROM categorias WHERE nombre LIKE '%Repuesto%' OR nombre LIKE '%Refacción%'
                ) THEN 5
                ELSE 3
            END
        ''')
        
        # Crear índice para optimizar consultas de stock bajo
        print("🔄 Creando índice para optimizar consultas...")
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_productos_stock_minimo 
            ON productos(stock_minimo)
        ''')
        
        conn.commit()
        print("✅ Migración completada exitosamente")
        
        # Mostrar estadísticas
        cursor.execute("SELECT COUNT(*) FROM productos WHERE stock_minimo > 0")
        productos_con_minimo = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(stock_minimo) FROM productos")
        promedio_minimo = cursor.fetchone()[0] or 0
        
        print(f"📊 Estadísticas:")
        print(f"   - Productos con stock mínimo configurado: {productos_con_minimo}")
        print(f"   - Stock mínimo promedio: {promedio_minimo:.1f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def verificar_migracion():
    """Verificar que la migración se aplicó correctamente"""
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    
    try:
        # Verificar estructura de la tabla
        cursor.execute("PRAGMA table_info(productos)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'stock_minimo' not in columns:
            print("❌ La columna stock_minimo no existe")
            return False
        
        # Verificar datos
        cursor.execute("SELECT COUNT(*) FROM productos WHERE stock_minimo IS NOT NULL")
        productos_con_minimo = cursor.fetchone()[0]
        
        print(f"✅ Verificación exitosa:")
        print(f"   - Columna stock_minimo existe: ✓")
        print(f"   - Productos con stock mínimo: {productos_con_minimo}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Iniciando migración: Agregar stock_minimo")
    print("=" * 50)
    
    if agregar_stock_minimo():
        print("\n🔍 Verificando migración...")
        if verificar_migracion():
            print("\n🎉 Migración completada exitosamente!")
        else:
            print("\n❌ Error en la verificación")
    else:
        print("\n❌ Error en la migración")