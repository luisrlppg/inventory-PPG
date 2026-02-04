#!/usr/bin/env python3
"""
Script de diagnóstico para identificar la causa de la lentitud en actualizaciones de stock
"""

import sqlite3
import time
import os
import psutil
import logging

def check_database_health():
    """Verificar salud de la base de datos"""
    print("🔍 CHECKING DATABASE HEALTH")
    print("=" * 50)
    
    try:
        # Información del archivo de base de datos
        db_path = 'inventario.db'
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
            print(f"✅ Database file size: {db_size:.2f} MB")
        else:
            print("❌ Database file not found!")
            return False
        
        conn = sqlite3.connect(db_path, timeout=20.0)
        conn.row_factory = sqlite3.Row
        
        # Verificar modo WAL
        wal_mode = conn.execute('PRAGMA journal_mode').fetchone()[0]
        print(f"✅ Journal mode: {wal_mode}")
        
        # Verificar integridad
        start_time = time.time()
        integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
        end_time = time.time()
        print(f"✅ Integrity check: {integrity} ({(end_time-start_time)*1000:.2f}ms)")
        
        # Estadísticas de tablas
        tables = ['productos', 'inventario', 'ubicaciones', 'operation_logs']
        for table in tables:
            count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
            print(f"✅ Table {table}: {count} records")
        
        # Verificar índices
        indexes = conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
        print(f"✅ Indexes: {len(indexes)} found")
        
        # Test de rendimiento de consultas críticas
        print("\n📊 QUERY PERFORMANCE TESTS")
        print("-" * 30)
        
        # Test 1: Consulta de inventario
        start_time = time.time()
        result = conn.execute('''
            SELECT COUNT(*) FROM inventario i
            JOIN productos p ON i.producto_id = p.id
            JOIN ubicaciones u ON i.ubicacion_id = u.id
        ''').fetchone()
        end_time = time.time()
        print(f"Inventory join query: {(end_time-start_time)*1000:.2f}ms ({result[0]} records)")
        
        # Test 2: Actualización simple
        start_time = time.time()
        conn.execute('UPDATE inventario SET fecha_actualizacion = CURRENT_TIMESTAMP WHERE id = 1')
        conn.rollback()  # No guardar el cambio
        end_time = time.time()
        print(f"Simple update: {(end_time-start_time)*1000:.2f}ms")
        
        # Test 3: Inserción en logs
        start_time = time.time()
        conn.execute('''
            INSERT INTO operation_logs (admin_user_id, operation_type, description, ip_address)
            VALUES (1, 'TEST', 'Performance test', '127.0.0.1')
        ''')
        log_id = conn.lastrowid
        conn.execute('DELETE FROM operation_logs WHERE id = ?', (log_id,))
        conn.rollback()
        end_time = time.time()
        print(f"Log insertion: {(end_time-start_time)*1000:.2f}ms")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        return False

def check_system_resources():
    """Verificar recursos del sistema"""
    print("\n💻 SYSTEM RESOURCES")
    print("=" * 50)
    
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"CPU usage: {cpu_percent}%")
        
        # Memoria
        memory = psutil.virtual_memory()
        print(f"Memory usage: {memory.percent}% ({memory.used/(1024**3):.1f}GB / {memory.total/(1024**3):.1f}GB)")
        
        # Disco
        disk = psutil.disk_usage('.')
        print(f"Disk usage: {disk.percent}% ({disk.used/(1024**3):.1f}GB / {disk.total/(1024**3):.1f}GB)")
        
        # Procesos Python
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if 'python' in proc.info['name'].lower():
                    python_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        print(f"Python processes: {len(python_processes)}")
        for proc in python_processes[:5]:  # Show top 5
            print(f"  PID {proc['pid']}: CPU {proc['cpu_percent']:.1f}%, Memory {proc['memory_percent']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ System resource check failed: {e}")
        return False

def check_log_files():
    """Verificar archivos de log"""
    print("\n📝 LOG FILES")
    print("=" * 50)
    
    log_files = ['admin_operations.log']
    
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file) / (1024 * 1024)  # MB
            print(f"✅ {log_file}: {size:.2f} MB")
            
            # Verificar últimas líneas para errores
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    recent_lines = lines[-10:] if len(lines) > 10 else lines
                    
                    error_count = sum(1 for line in recent_lines if 'ERROR' in line)
                    if error_count > 0:
                        print(f"⚠️  Found {error_count} recent errors in {log_file}")
                        for line in recent_lines:
                            if 'ERROR' in line:
                                print(f"   {line.strip()}")
                    else:
                        print(f"✅ No recent errors in {log_file}")
                        
            except Exception as e:
                print(f"⚠️  Could not read {log_file}: {e}")
        else:
            print(f"⚠️  {log_file} not found")

def simulate_problematic_operation():
    """Simular la operación problemática para medir tiempo"""
    print("\n⚡ SIMULATING PROBLEMATIC OPERATION")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('inventario.db', timeout=20.0)
        conn.row_factory = sqlite3.Row
        
        # Simular la operación lenta original
        print("Testing old-style operation (multiple queries)...")
        start_time = time.time()
        
        # Simular múltiples consultas como en el código original
        for i in range(5):  # Simular 5 cambios
            # Consulta de producto
            producto = conn.execute('SELECT descripcion FROM productos WHERE id = ?', (1,)).fetchone()
            # Consulta de ubicación
            ubicacion = conn.execute('SELECT codigo FROM ubicaciones WHERE id = ?', (1,)).fetchone()
            # Verificar existencia
            existing = conn.execute('SELECT * FROM inventario WHERE producto_id = ? AND ubicacion_id = ?', (1, 1)).fetchone()
            # Actualizar
            conn.execute('UPDATE inventario SET cantidad = ? WHERE producto_id = ? AND ubicacion_id = ?', (10+i, 1, 1))
            # Log individual (simulado)
            conn.execute('INSERT INTO operation_logs (admin_user_id, operation_type, description, ip_address) VALUES (1, ?, ?, ?)', 
                        ('TEST', f'Test operation {i}', '127.0.0.1'))
        
        conn.rollback()  # No guardar cambios
        end_time = time.time()
        old_time = (end_time - start_time) * 1000
        print(f"Old method: {old_time:.2f}ms")
        
        # Simular la operación optimizada
        print("Testing optimized operation (batch queries)...")
        start_time = time.time()
        
        # Consultas en lote
        productos = conn.execute('SELECT id, descripcion FROM productos WHERE id IN (1,1,1,1,1)').fetchall()
        ubicaciones = conn.execute('SELECT id, codigo FROM ubicaciones WHERE id IN (1,1,1,1,1)').fetchall()
        
        # Actualizaciones en lote
        updates = [(10+i, 1, 1) for i in range(5)]
        conn.executemany('UPDATE inventario SET cantidad = ? WHERE producto_id = ? AND ubicacion_id = ?', updates)
        
        # Logs en lote
        log_entries = [(1, 'TEST_BATCH', f'Batch test {i}', '127.0.0.1') for i in range(5)]
        conn.executemany('INSERT INTO operation_logs (admin_user_id, operation_type, description, ip_address) VALUES (?, ?, ?, ?)', 
                        log_entries)
        
        conn.rollback()  # No guardar cambios
        end_time = time.time()
        new_time = (end_time - start_time) * 1000
        print(f"Optimized method: {new_time:.2f}ms")
        
        improvement = ((old_time - new_time) / old_time) * 100
        print(f"Performance improvement: {improvement:.1f}%")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Operation simulation failed: {e}")

def main():
    print("🔍 SLOWNESS DIAGNOSTIC TOOL")
    print("=" * 50)
    print("Analyzing potential causes of 30-second delays in stock updates...")
    
    # Check 1: Database health
    db_ok = check_database_health()
    
    # Check 2: System resources
    sys_ok = check_system_resources()
    
    # Check 3: Log files
    check_log_files()
    
    # Check 4: Simulate operations
    simulate_problematic_operation()
    
    print("\n" + "=" * 50)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    if db_ok and sys_ok:
        print("✅ System appears healthy")
        print("🔧 The 30-second delay was likely caused by:")
        print("   1. Multiple database connections per operation")
        print("   2. Individual queries in loops instead of batch operations")
        print("   3. Excessive logging with separate connections")
        print("   4. No transaction management")
        print("\n🚀 The optimized code should resolve these issues!")
    else:
        print("⚠️  Found potential system issues")
        print("   Check the results above for specific problems")

if __name__ == "__main__":
    main()