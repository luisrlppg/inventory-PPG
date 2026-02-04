#!/usr/bin/env python3
"""
Development server with auto-reload and debug mode
"""

import os
from app import app

if __name__ == '__main__':
    # Configurar modo desarrollo
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    print("🚀 Starting development server...")
    print("📍 URL: http://localhost:5000")
    print("👤 Admin: admin / admin123")
    print("🔄 Auto-reload enabled")
    print("🐛 Debug mode enabled")
    print("\n" + "="*50)
    
    # Iniciar servidor con auto-reload
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=True,
        use_debugger=True
    )