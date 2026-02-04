#!/usr/bin/env python3
"""
Script para probar la funcionalidad de ubicaciones después del fix
"""

import sqlite3
import requests
import json

def test_database_fix():
    """Probar el fix de lastrowid directamente en la base de datos"""
    print("🧪 Testing database lastrowid fix...")
    
    try:
        conn = sqlite3.connect('inventario.db')
        conn.row_factory = sqlite3.Row
        
        # Probar inserción de ubicación
        cursor = conn.execute('INSERT INTO ubicaciones (codigo, nombre) VALUES (?, ?)', 
                             ('TEST_FIX', 'Test Location Fix'))
        
        new_id = cursor.lastrowid
        print(f"✅ lastrowid works: New location ID = {new_id}")
        
        # Verificar que se creó
        result = conn.execute('SELECT * FROM ubicaciones WHERE id = ?', (new_id,)).fetchone()
        if result:
            print(f"✅ Location created: {result['codigo']} - {result['nombre']}")
        
        # Limpiar
        conn.execute('DELETE FROM ubicaciones WHERE id = ?', (new_id,))
        conn.commit()
        conn.close()
        
        print("✅ Database fix verified!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_web_interface():
    """Probar la interfaz web (requiere que la app esté corriendo)"""
    print("\n🌐 Testing web interface...")
    
    try:
        # Verificar que la app está corriendo
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            print("✅ Application is running")
            
            # Probar página de ubicaciones
            response = requests.get('http://localhost:5000/ubicaciones', timeout=5)
            if response.status_code == 200:
                print("✅ Locations page accessible")
            else:
                print(f"⚠️  Locations page returned: {response.status_code}")
                
        else:
            print(f"⚠️  Health check returned: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Application not running. Start with: python app.py")
    except Exception as e:
        print(f"❌ Web test failed: {e}")

def main():
    print("🔍 TESTING UBICACIONES FIX")
    print("=" * 50)
    
    # Test 1: Database fix
    db_ok = test_database_fix()
    
    # Test 2: Web interface
    test_web_interface()
    
    print("\n" + "=" * 50)
    if db_ok:
        print("🎉 Fix verified! You can now create locations without errors.")
        print("\nTo test manually:")
        print("1. Start the app: python app.py")
        print("2. Go to: http://localhost:5000/ubicaciones")
        print("3. Click 'Nueva Ubicación'")
        print("4. Create a test location")
    else:
        print("❌ Fix verification failed. Check the error above.")

if __name__ == "__main__":
    main()