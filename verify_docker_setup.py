#!/usr/bin/env python3
"""
Docker Setup Verification Script
Checks if all files and configurations are ready for Docker deployment
"""

import os
import sys
import json
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and report status"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NOT FOUND")
        return False

def check_directory_exists(dirpath, description):
    """Check if a directory exists and report status"""
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        print(f"✅ {description}: {dirpath}")
        return True
    else:
        print(f"❌ {description}: {dirpath} - NOT FOUND")
        return False

def check_docker_files():
    """Check Docker configuration files"""
    print("🐳 DOCKER CONFIGURATION FILES")
    print("=" * 50)
    
    files_ok = True
    files_ok &= check_file_exists("Dockerfile", "Dockerfile")
    files_ok &= check_file_exists("docker-compose.yml", "Docker Compose")
    files_ok &= check_file_exists(".dockerignore", "Docker Ignore")
    files_ok &= check_file_exists("nginx.conf", "Nginx Config")
    files_ok &= check_file_exists("docker-compose.dev.yml", "Dev Compose Override")
    files_ok &= check_file_exists(".env.example", "Environment Template")
    
    return files_ok

def check_application_files():
    """Check main application files"""
    print("\n📱 APPLICATION FILES")
    print("=" * 50)
    
    files_ok = True
    files_ok &= check_file_exists("app.py", "Main Application")
    files_ok &= check_file_exists("requirements.txt", "Python Dependencies")
    files_ok &= check_file_exists("config.py", "Configuration")
    files_ok &= check_file_exists("inventario.db", "Database")
    
    return files_ok

def check_directories():
    """Check required directories"""
    print("\n📁 DIRECTORIES")
    print("=" * 50)
    
    dirs_ok = True
    dirs_ok &= check_directory_exists("templates", "Templates Directory")
    dirs_ok &= check_directory_exists("static", "Static Files Directory")
    dirs_ok &= check_directory_exists("imagenes", "Images Directory")
    
    # Check if logs directory exists, create if not
    if not os.path.exists("logs"):
        print("⚠️  Logs directory: logs - NOT FOUND, will be created by Docker")
    else:
        print("✅ Logs directory: logs")
    
    return dirs_ok

def check_requirements():
    """Check Python requirements"""
    print("\n🐍 PYTHON REQUIREMENTS")
    print("=" * 50)
    
    try:
        with open("requirements.txt", "r") as f:
            requirements = f.read().strip().split("\n")
        
        print(f"✅ Found {len(requirements)} Python packages:")
        for req in requirements:
            if req.strip():
                print(f"   - {req.strip()}")
        
        return True
    except Exception as e:
        print(f"❌ Error reading requirements.txt: {e}")
        return False

def check_database():
    """Check database file"""
    print("\n🗄️  DATABASE")
    print("=" * 50)
    
    if not os.path.exists("inventario.db"):
        print("❌ Database file not found: inventario.db")
        print("   Run 'python importar_datos.py' to create the database")
        return False
    
    try:
        import sqlite3
        conn = sqlite3.connect("inventario.db")
        cursor = conn.cursor()
        
        # Check main tables
        tables = ["productos", "inventario", "ubicaciones", "admin_users"]
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ Table '{table}': {count} records")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_docker_compose_config():
    """Check docker-compose.yml configuration"""
    print("\n🔧 DOCKER COMPOSE CONFIGURATION")
    print("=" * 50)
    
    try:
        # This is a basic check - in a real scenario you'd parse YAML
        with open("docker-compose.yml", "r") as f:
            content = f.read()
        
        checks = [
            ("Service definition", "inventario-app:" in content),
            ("Port mapping", "5000:5000" in content),
            ("Volume mounts", "./inventario.db:/app/inventario.db" in content),
            ("Images volume", "./imagenes:/app/imagenes" in content),
            ("Nginx service", "nginx:" in content),
            ("Health check", "healthcheck:" in content),
        ]
        
        all_ok = True
        for check_name, condition in checks:
            if condition:
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name}")
                all_ok = False
        
        return all_ok
    except Exception as e:
        print(f"❌ Error reading docker-compose.yml: {e}")
        return False

def check_security():
    """Check security considerations"""
    print("\n🔒 SECURITY CHECKS")
    print("=" * 50)
    
    warnings = []
    
    # Check if .env file exists (shouldn't be in repo)
    if os.path.exists(".env"):
        warnings.append("⚠️  .env file found - ensure it's not committed to git")
    else:
        print("✅ No .env file in repository (good)")
    
    # Check if default admin credentials are documented
    print("⚠️  Remember to change default admin credentials (admin/admin123)")
    
    # Check if SSL is configured
    with open("nginx.conf", "r") as f:
        nginx_content = f.read()
    
    if "ssl_certificate" in nginx_content and "# ssl_certificate" not in nginx_content:
        print("✅ SSL configuration found in nginx.conf")
    else:
        warnings.append("⚠️  SSL not configured - add certificates for production")
    
    return len(warnings) == 0

def main():
    """Main verification function"""
    print("🔍 DOCKER DEPLOYMENT VERIFICATION")
    print("=" * 50)
    print("Checking if your application is ready for Docker deployment...\n")
    
    all_checks = []
    
    all_checks.append(check_docker_files())
    all_checks.append(check_application_files())
    all_checks.append(check_directories())
    all_checks.append(check_requirements())
    all_checks.append(check_database())
    all_checks.append(check_docker_compose_config())
    
    # Security is informational, doesn't fail the check
    check_security()
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    
    if all(all_checks):
        print("🎉 ALL CHECKS PASSED!")
        print("Your application is ready for Docker deployment.")
        print("\nNext steps:")
        print("1. Install Docker and Docker Compose")
        print("2. Run: docker-compose build")
        print("3. Run: docker-compose up -d")
        print("4. Access: http://localhost:5000")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print("Please fix the issues above before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())