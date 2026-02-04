#!/usr/bin/env python3
"""
Script para probar el rendimiento de la actualización de stock
"""

import time
import requests
import json
import sqlite3

def test_database_performance():
    """Probar rendimiento directo de la base de datos"""
    print("🔍 Testing database performance...")
    
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    
    # Test 1: Consulta simple
    start_time = time.time()
    result = conn.execute('SELECT COUNT(*) FROM inventario').fetchone()
    end_time = time.time()
    print(f"✅ Simple query: {(end_time - start_time)*1000:.2f}ms - {result[0]} records")
    
    # Test 2: Consulta compleja (como la del inventario)
    start_time = time.time()
    result = conn.execute('''
        SELECT p.id, p.descripcion, i.cantidad, u.codigo
        FROM inventario i
        JOIN productos p ON i.producto_id = p.id
        JOIN ubicaciones u ON i.ubicacion_id = u.id
        LIMIT 10
    ''').fetchall()
    end_time = time.time()
    print(f"✅ Complex query: {(end_time - start_time)*1000:.2f}ms - {len(result)} records")
    
    # Test 3: Actualización simple
    start_time = time.time()
    conn.execute('UPDATE inventario SET fecha_actualizacion = CURRENT_TIMESTAMP WHERE id = 1')
    conn.commit()
    end_time = time.time()
    print(f"✅ Simple update: {(end_time - start_time)*1000:.2f}ms")
    
    conn.close()

def test_api_performance():
    """Probar rendimiento de la API (requiere app corriendo)"""
    print("\n🌐 Testing API performance...")
    
    try:
        # Test health endpoint
        start_time = time.time()
        response = requests.get('http://localhost:5000/health', timeout=10)
        end_time = time.time()
        
        if response.status_code == 200:
            print(f"✅ Health endpoint: {(end_time - start_time)*1000:.2f}ms")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return
        
        # Test inventario page
        start_time = time.time()
        response = requests.get('http://localhost:5000/inventario', timeout=10)
        end_time = time.time()
        
        if response.status_code == 200:
            print(f"✅ Inventario page: {(end_time - start_time)*1000:.2f}ms")
        else:
            print(f"❌ Inventario page failed: {response.status_code}")
        
    except requests.exceptions.ConnectionError:
        print("⚠️  Application not running. Start with: python app.py")
    except requests.exceptions.Timeout:
        print("❌ Request timed out - this indicates a performance problem")
    except Exception as e:
        print(f"❌ API test failed: {e}")

def simulate_stock_update():
    """Simular actualización de stock para medir tiempo"""
    print("\n⚡ Simulating stock update...")
    
    # Datos de prueba para actualización
    test_data = {
        "cambios": {
            "test1": {
                "producto_id": 1,
                "ubicacion_id": 1,
                "stock_actual": 10,
                "nuevo_stock": 15
            }
        }
    }
    
    try:
        # Primero necesitamos hacer login como admin
        session = requests.Session()
        
        # Login
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        login_response = session.post('http://localhost:5000/admin/login', 
                                    data=login_data, timeout=10)
        
        if login_response.status_code != 200 and 'admin' not in login_response.text.lower():
            print("❌ Admin login failed")
            return
        
        print("✅ Admin login successful")
        
        # Test stock update
        start_time = time.time()
        response = session.post('http://localhost:5000/admin/actualizar-stock-rapido',
                              json=test_data,
                              headers={'Content-Type': 'application/json'},
                              timeout=10)
        end_time = time.time()
        
        duration_ms = (end_time - start_time) * 1000
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Stock update successful: {duration_ms:.2f}ms")
                print(f"   Changes applied: {result.get('cambios_aplicados', 0)}")
                
                if duration_ms > 1000:  # More than 1 second
                    print("⚠️  WARNING: Update took more than 1 second!")
                elif duration_ms > 500:  # More than 500ms
                    print("⚠️  SLOW: Update took more than 500ms")
                else:
                    print("🚀 FAST: Update completed quickly")
            else:
                print(f"❌ Stock update failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ Stock update request failed: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Application not running. Start with: python app.py")
    except requests.exceptions.Timeout:
        print("❌ Stock update timed out - this is the problem!")
    except Exception as e:
        print(f"❌ Stock update test failed: {e}")

def main():
    print("🚀 PERFORMANCE TESTING")
    print("=" * 50)
    
    # Test 1: Database performance
    test_database_performance()
    
    # Test 2: API performance
    test_api_performance()
    
    # Test 3: Stock update simulation
    simulate_stock_update()
    
    print("\n" + "=" * 50)
    print("📊 PERFORMANCE ANALYSIS")
    print("=" * 50)
    print("Expected times:")
    print("- Database queries: < 50ms")
    print("- API endpoints: < 500ms")
    print("- Stock updates: < 200ms")
    print("\nIf any operation takes > 1 second, there's a performance issue.")

if __name__ == "__main__":
    main()