#!/usr/bin/env python3
"""
Script para configurar una demostración del sistema de alertas de stock
Configura algunos productos con stock mínimo alto para generar alertas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime

def configurar_demo_alertas():
    """Configurar productos para demostrar alertas de stock"""
    print("🎭 Configurando demostración de alertas de stock...")
    
    # Conectar a la base de datos
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    
    try:
        # Obtener algunos productos para configurar
        productos = cursor.execute('''
            SELECT p.id, p.descripcion, p.codigo, COALESCE(SUM(i.cantidad), 0) as stock_actual
            FROM productos p
            LEFT JOIN inventario i ON p.id = i.producto_id
            GROUP BY p.id, p.descripcion, p.codigo
            ORDER BY stock_actual ASC
            LIMIT 10
        ''').fetchall()
        
        print(f"📦 Configurando {len(productos)} productos para demo...")
        
        productos_configurados = 0
        
        for producto in productos:
            producto_id, descripcion, codigo, stock_actual = producto
            
            # Configurar stock mínimo más alto que el actual para generar alerta
            nuevo_stock_minimo = max(stock_actual + 5, 10)
            
            cursor.execute('''
                UPDATE productos 
                SET stock_minimo = ? 
                WHERE id = ?
            ''', (nuevo_stock_minimo, producto_id))
            
            print(f"   ✅ {descripcion[:50]}...")
            print(f"      Stock actual: {stock_actual} | Nuevo mínimo: {nuevo_stock_minimo}")
            
            productos_configurados += 1
        
        # Configurar algunos productos con stock mínimo normal
        cursor.execute('''
            UPDATE productos 
            SET stock_minimo = 3 
            WHERE stock_minimo IS NULL OR stock_minimo = 0
        ''')
        
        conn.commit()
        
        print(f"\n✅ Demo configurada exitosamente:")
        print(f"   - {productos_configurados} productos con alertas activas")
        print(f"   - Productos restantes con stock mínimo de 3")
        
        # Mostrar estadísticas
        cursor.execute('''
            SELECT 
                COUNT(*) as total_productos,
                COUNT(CASE WHEN stock_minimo > 0 THEN 1 END) as con_minimo,
                AVG(stock_minimo) as promedio_minimo
            FROM productos
        ''')
        
        stats = cursor.fetchone()
        print(f"\n📊 Estadísticas:")
        print(f"   - Total productos: {stats[0]}")
        print(f"   - Con stock mínimo: {stats[1]}")
        print(f"   - Promedio stock mínimo: {stats[2]:.1f}")
        
        # Verificar productos con stock bajo
        cursor.execute('''
            SELECT COUNT(*) 
            FROM productos p
            LEFT JOIN (
                SELECT producto_id, SUM(cantidad) as stock_total
                FROM inventario 
                GROUP BY producto_id
            ) i ON p.id = i.producto_id
            WHERE p.stock_minimo > 0 
            AND COALESCE(i.stock_total, 0) <= p.stock_minimo
        ''')
        
        productos_stock_bajo = cursor.fetchone()[0]
        print(f"   - Productos con stock bajo: {productos_stock_bajo}")
        
        if productos_stock_bajo > 0:
            print(f"\n🚨 ¡Perfecto! Ahora tienes {productos_stock_bajo} productos con stock bajo")
            print("   Puedes probar el sistema de alertas en /admin/stock-alerts")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configurando demo: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def restaurar_configuracion_original():
    """Restaurar configuración original de stock mínimo"""
    print("🔄 Restaurando configuración original...")
    
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    
    try:
        # Restaurar stock mínimo a valores más realistas
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
        
        conn.commit()
        print("✅ Configuración restaurada a valores por defecto")
        
        return True
        
    except Exception as e:
        print(f"❌ Error restaurando configuración: {e}")
        return False
    finally:
        conn.close()

def main():
    """Función principal"""
    print("🎯 Configurador de Demo - Sistema de Alertas de Stock")
    print("=" * 55)
    
    while True:
        print("\n¿Qué deseas hacer?")
        print("1. Configurar demo de alertas (genera productos con stock bajo)")
        print("2. Restaurar configuración original")
        print("3. Salir")
        
        opcion = input("\nSelecciona una opción (1-3): ").strip()
        
        if opcion == '1':
            if configurar_demo_alertas():
                print("\n🎉 ¡Demo configurada! Ahora puedes:")
                print("   1. Iniciar la aplicación: python app.py")
                print("   2. Ir a /admin/login (admin/admin123)")
                print("   3. Acceder a 'Alertas de Stock' en el menú")
                print("   4. Configurar tu correo y enviar alertas de prueba")
            break
            
        elif opcion == '2':
            if restaurar_configuracion_original():
                print("\n✅ Configuración restaurada")
            break
            
        elif opcion == '3':
            print("👋 ¡Hasta luego!")
            break
            
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    main()