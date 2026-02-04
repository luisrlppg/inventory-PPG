#!/usr/bin/env python3
"""
Script para comparar las bases de datos antes de la migración
Compara inventario.db vs bkpinventario.db
"""

import sqlite3
import os

def analizar_base_datos(db_path):
    """Analizar una base de datos y retornar información detallada"""
    if not os.path.exists(db_path):
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        info = {
            'archivo': db_path,
            'tamaño': os.path.getsize(db_path),
            'tablas': {}
        }
        
        # Obtener todas las tablas
        tables = cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()
        
        for table in tables:
            table_name = table['name']
            
            # Contar registros
            count = cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}").fetchone()['count']
            
            # Obtener columnas
            columns = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
            column_info = [(col['name'], col['type']) for col in columns]
            
            info['tablas'][table_name] = {
                'registros': count,
                'columnas': column_info
            }
        
        conn.close()
        return info
        
    except Exception as e:
        print(f"❌ Error analizando {db_path}: {e}")
        return None

def comparar_bases_datos():
    """Comparar las dos bases de datos"""
    print("🔍 COMPARACIÓN DE BASES DE DATOS")
    print("=" * 50)
    
    # Analizar ambas bases de datos
    info_actual = analizar_base_datos('inventario.db')
    info_produccion = analizar_base_datos('bkpinventario.db')
    
    if not info_actual:
        print("❌ No se pudo analizar inventario.db")
        return
    
    if not info_produccion:
        print("❌ No se pudo analizar bkpinventario.db")
        return
    
    print("📊 INFORMACIÓN GENERAL")
    print("-" * 30)
    print(f"inventario.db:")
    print(f"   📁 Tamaño: {info_actual['tamaño']:,} bytes")
    print(f"   📋 Tablas: {len(info_actual['tablas'])}")
    
    print(f"\nbkpinventario.db:")
    print(f"   📁 Tamaño: {info_produccion['tamaño']:,} bytes")
    print(f"   📋 Tablas: {len(info_produccion['tablas'])}")
    
    # Comparar tablas
    print(f"\n📋 COMPARACIÓN DE TABLAS")
    print("-" * 30)
    
    tablas_actual = set(info_actual['tablas'].keys())
    tablas_produccion = set(info_produccion['tablas'].keys())
    
    # Tablas comunes
    tablas_comunes = tablas_actual & tablas_produccion
    print(f"✅ Tablas comunes ({len(tablas_comunes)}):")
    for tabla in sorted(tablas_comunes):
        registros_actual = info_actual['tablas'][tabla]['registros']
        registros_produccion = info_produccion['tablas'][tabla]['registros']
        
        if registros_produccion > registros_actual:
            status = "📈 MÁS DATOS"
        elif registros_produccion < registros_actual:
            status = "📉 MENOS DATOS"
        else:
            status = "📊 IGUAL"
        
        print(f"   {tabla}:")
        print(f"      inventario.db: {registros_actual:,} registros")
        print(f"      bkpinventario.db: {registros_produccion:,} registros {status}")
    
    # Tablas solo en actual
    tablas_solo_actual = tablas_actual - tablas_produccion
    if tablas_solo_actual:
        print(f"\n⚠️  Tablas solo en inventario.db ({len(tablas_solo_actual)}):")
        for tabla in sorted(tablas_solo_actual):
            registros = info_actual['tablas'][tabla]['registros']
            print(f"   {tabla}: {registros:,} registros")
    
    # Tablas solo en producción
    tablas_solo_produccion = tablas_produccion - tablas_actual
    if tablas_solo_produccion:
        print(f"\n📋 Tablas solo en bkpinventario.db ({len(tablas_solo_produccion)}):")
        for tabla in sorted(tablas_solo_produccion):
            registros = info_produccion['tablas'][tabla]['registros']
            print(f"   {tabla}: {registros:,} registros")
    
    # Análisis detallado de productos e inventario
    print(f"\n🔍 ANÁLISIS DETALLADO")
    print("-" * 30)
    
    if 'productos' in tablas_comunes:
        print("📦 Tabla PRODUCTOS:")
        cols_actual = set(col[0] for col in info_actual['tablas']['productos']['columnas'])
        cols_produccion = set(col[0] for col in info_produccion['tablas']['productos']['columnas'])
        
        cols_comunes = cols_actual & cols_produccion
        cols_solo_actual = cols_actual - cols_produccion
        cols_solo_produccion = cols_produccion - cols_actual
        
        print(f"   ✅ Columnas comunes: {len(cols_comunes)}")
        if cols_solo_actual:
            print(f"   📋 Solo en inventario.db: {', '.join(cols_solo_actual)}")
        if cols_solo_produccion:
            print(f"   📋 Solo en bkpinventario.db: {', '.join(cols_solo_produccion)}")
    
    if 'inventario' in tablas_comunes:
        print("\n📊 Tabla INVENTARIO:")
        print(f"   inventario.db: {info_actual['tablas']['inventario']['registros']:,} registros")
        print(f"   bkpinventario.db: {info_produccion['tablas']['inventario']['registros']:,} registros")
    
    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES")
    print("-" * 30)
    
    total_registros_produccion = sum(tabla['registros'] for tabla in info_produccion['tablas'].values())
    total_registros_actual = sum(tabla['registros'] for tabla in info_actual['tablas'].values())
    
    if total_registros_produccion > total_registros_actual:
        print("✅ bkpinventario.db tiene más datos - RECOMENDADO para migración")
    elif total_registros_produccion < total_registros_actual:
        print("⚠️  inventario.db tiene más datos - Revisar antes de migrar")
    else:
        print("📊 Ambas bases tienen similar cantidad de datos")
    
    if tablas_solo_actual:
        print("⚠️  inventario.db tiene tablas nuevas que se perderían")
        print("   💡 La migración agregará estas funcionalidades a bkpinventario.db")
    
    print("\n🚀 PRÓXIMOS PASOS:")
    print("1. Si bkpinventario.db tiene más datos → Ejecutar migración")
    print("2. Ejecutar: python migrar_produccion_completa.py")
    print("3. Ejecutar: python intercambiar_base_datos.py")
    print("4. Probar la aplicación con los datos migrados")

def main():
    """Función principal"""
    print("🔍 COMPARADOR DE BASES DE DATOS")
    print("=" * 60)
    print("Este script compara inventario.db vs bkpinventario.db")
    print("para ayudarte a decidir el proceso de migración.")
    print()
    
    if not os.path.exists('inventario.db'):
        print("❌ No se encontró inventario.db")
        return
    
    if not os.path.exists('bkpinventario.db'):
        print("❌ No se encontró bkpinventario.db")
        return
    
    comparar_bases_datos()

if __name__ == "__main__":
    main()