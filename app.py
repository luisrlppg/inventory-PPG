from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, make_response, send_file
from flask_mail import Mail, Message
import sqlite3
import os
import hashlib
import secrets
import logging
import csv
import io
import shutil
import tempfile
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.utils import secure_filename
from config.config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar Flask-Mail
mail = Mail(app)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('admin_operations.log'),
        logging.StreamHandler()
    ]
)

# Configuración de la base de datos
DATABASE = 'inventario.db'

def get_db_connection():
    """Obtener conexión a la base de datos - OPTIMIZADA"""
    conn = sqlite3.connect(DATABASE, timeout=20.0)
    conn.row_factory = sqlite3.Row
    
    # Optimizaciones de rendimiento
    conn.execute('PRAGMA journal_mode=WAL')  # Better concurrent access
    conn.execute('PRAGMA busy_timeout=20000')  # 20 second timeout
    conn.execute('PRAGMA synchronous=NORMAL')  # Faster writes
    conn.execute('PRAGMA cache_size=10000')  # Larger cache
    conn.execute('PRAGMA temp_store=MEMORY')  # Use memory for temp tables
    
    return conn

def hash_password(password):
    """Hash de contraseña usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_session_token():
    """Generar token de sesión seguro"""
    return secrets.token_urlsafe(32)

def is_admin_logged_in():
    """Verificar si hay un administrador logueado"""
    if 'admin_token' not in session:
        return False
    
    conn = get_db_connection()
    admin_session = conn.execute('''
        SELECT au.id, au.username, au.is_active
        FROM admin_sessions as_table
        JOIN admin_users au ON as_table.admin_user_id = au.id
        WHERE as_table.session_token = ? AND as_table.expires_at > CURRENT_TIMESTAMP AND au.is_active = 1
    ''', (session['admin_token'],)).fetchone()
    conn.close()
    
    if admin_session:
        session['admin_user_id'] = admin_session['id']
        session['admin_username'] = admin_session['username']
        return True
    else:
        session.pop('admin_token', None)
        session.pop('admin_user_id', None)
        session.pop('admin_username', None)
        return False

def require_admin(f):
    """Decorador para requerir autenticación de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin_logged_in():
            flash('Acceso denegado. Se requieren permisos de administrador.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def log_admin_operation(operation_type, description, producto_id=None, ubicacion_id=None, old_quantity=None, new_quantity=None, conn=None):
    """Registrar operación de administrador en logs"""
    if not is_admin_logged_in():
        return
    
    # Use existing connection if provided, otherwise create new one
    should_close_conn = False
    if conn is None:
        conn = get_db_connection()
        should_close_conn = True
    
    try:
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        
        conn.execute('''
            INSERT INTO operation_logs (admin_user_id, operation_type, producto_id, ubicacion_id, 
                                      old_quantity, new_quantity, description, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session.get('admin_user_id'), operation_type, producto_id, ubicacion_id, 
              old_quantity, new_quantity, description, ip_address))
        
        if should_close_conn:
            conn.commit()
        
        # Log también en archivo
        logging.info(f"ADMIN_OP: {session.get('admin_username')} - {operation_type} - {description}")
        
    except Exception as e:
        logging.error(f"Error logging admin operation: {e}")
    finally:
        if should_close_conn:
            conn.close()

def get_productos_stock_bajo():
    """Obtener productos con stock por debajo del mínimo"""
    conn = get_db_connection()
    try:
        productos_stock_bajo = conn.execute('''
            SELECT 
                p.id,
                p.codigo,
                p.descripcion,
                p.stock_minimo,
                COALESCE(SUM(i.cantidad), 0) as stock_actual,
                c.nombre as categoria,
                sc.nombre as subcategoria,
                pr.nombre as proveedor,
                pr.telefono as proveedor_telefono,
                pr.email as proveedor_email,
                GROUP_CONCAT(u.nombre || ': ' || i.cantidad, ', ') as ubicaciones_stock
            FROM productos p
            LEFT JOIN inventario i ON p.id = i.producto_id
            LEFT JOIN categorias c ON p.categoria_id = c.id
            LEFT JOIN subcategorias sc ON p.subcategoria_id = sc.id
            LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
            LEFT JOIN ubicaciones u ON i.ubicacion_id = u.id
            WHERE p.stock_minimo > 0
            GROUP BY p.id, p.codigo, p.descripcion, p.stock_minimo, c.nombre, sc.nombre, pr.nombre, pr.telefono, pr.email
            HAVING stock_actual <= p.stock_minimo
            ORDER BY (stock_actual - p.stock_minimo) ASC, p.descripcion
        ''').fetchall()
        
        return [dict(row) for row in productos_stock_bajo]
    finally:
        conn.close()

def enviar_alerta_stock_bajo(productos_stock_bajo, destinatarios=None):
    """Enviar correo de alerta de stock bajo"""
    if not app.config.get('STOCK_ALERT_ENABLED', True):
        logging.info("Alertas de stock deshabilitadas")
        return False
    
    if not productos_stock_bajo:
        logging.info("No hay productos con stock bajo")
        return True
    
    # Usar destinatarios de configuración si no se especifican
    if not destinatarios:
        destinatarios = app.config.get('STOCK_ALERT_RECIPIENTS', [])
    
    if not destinatarios:
        logging.warning("No hay destinatarios configurados para alertas de stock")
        return False
    
    # Verificar configuración de correo
    if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
        logging.error("Configuración de correo incompleta")
        return False
    
    try:
        # Crear el mensaje
        subject = app.config.get('STOCK_ALERT_SUBJECT', 'Alerta de Stock Bajo - Inventario PPG')
        
        # Generar contenido HTML
        html_content = generar_html_alerta_stock(productos_stock_bajo)
        
        # Generar contenido de texto plano
        text_content = generar_texto_alerta_stock(productos_stock_bajo)
        
        # Enviar correo a cada destinatario
        for destinatario in destinatarios:
            if destinatario.strip():  # Verificar que no esté vacío
                msg = Message(
                    subject=subject,
                    sender=app.config.get('MAIL_DEFAULT_SENDER'),
                    recipients=[destinatario.strip()],
                    body=text_content,
                    html=html_content
                )
                
                mail.send(msg)
                logging.info(f"Alerta de stock enviada a: {destinatario}")
        
        # Registrar en logs de administrador
        log_admin_operation(
            'STOCK_ALERT', 
            f'Alerta de stock bajo enviada - {len(productos_stock_bajo)} productos afectados'
        )
        
        return True
        
    except Exception as e:
        logging.error(f"Error enviando alerta de stock: {e}")
        return False

def generar_html_alerta_stock(productos_stock_bajo):
    """Generar contenido HTML para la alerta de stock"""
    fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #dc3545; color: white; padding: 15px; text-align: center; }}
            .content {{ padding: 20px; }}
            .summary {{ background-color: #f8f9fa; padding: 15px; margin: 15px 0; border-left: 4px solid #dc3545; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .critical {{ background-color: #ffebee; }}
            .warning {{ background-color: #fff3e0; }}
            .footer {{ margin-top: 30px; padding: 15px; background-color: #f8f9fa; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚨 ALERTA DE STOCK BAJO</h1>
            <p>{app.config.get('COMPANY_NAME', 'PPG - Plásticos Plasa')}</p>
        </div>
        
        <div class="content">
            <div class="summary">
                <h3>Resumen de la Alerta</h3>
                <p><strong>Fecha y Hora:</strong> {fecha_actual}</p>
                <p><strong>Productos Afectados:</strong> {len(productos_stock_bajo)}</p>
                <p><strong>Acción Requerida:</strong> Revisar y reabastecer productos con stock bajo</p>
            </div>
            
            <h3>Productos que Requieren Atención</h3>
            <table>
                <thead>
                    <tr>
                        <th>Código</th>
                        <th>Descripción</th>
                        <th>Stock Actual</th>
                        <th>Stock Mínimo</th>
                        <th>Diferencia</th>
                        <th>Categoría</th>
                        <th>Proveedor</th>
                        <th>Ubicaciones</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for producto in productos_stock_bajo:
        diferencia = producto['stock_actual'] - producto['stock_minimo']
        clase_fila = 'critical' if diferencia < 0 else 'warning'
        
        proveedor_info = producto['proveedor'] or 'Sin proveedor'
        if producto['proveedor_telefono']:
            proveedor_info += f" (Tel: {producto['proveedor_telefono']})"
        
        categoria_info = producto['categoria'] or 'Sin categoría'
        if producto['subcategoria']:
            categoria_info += f" > {producto['subcategoria']}"
        
        ubicaciones = producto['ubicaciones_stock'] or 'Sin ubicaciones'
        
        html += f"""
                    <tr class="{clase_fila}">
                        <td>{producto['codigo'] or 'N/A'}</td>
                        <td>{producto['descripcion']}</td>
                        <td style="text-align: center;"><strong>{producto['stock_actual']}</strong></td>
                        <td style="text-align: center;">{producto['stock_minimo']}</td>
                        <td style="text-align: center; color: {'red' if diferencia < 0 else 'orange'};">
                            {diferencia:+d}
                        </td>
                        <td>{categoria_info}</td>
                        <td>{proveedor_info}</td>
                        <td>{ubicaciones}</td>
                    </tr>
        """
    
    html += f"""
                </tbody>
            </table>
            
            <div class="summary">
                <h4>Recomendaciones:</h4>
                <ul>
                    <li>Contactar a los proveedores para realizar pedidos urgentes</li>
                    <li>Verificar si hay stock en otras ubicaciones</li>
                    <li>Considerar productos alternativos o sustitutos</li>
                    <li>Revisar y ajustar los niveles de stock mínimo si es necesario</li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>Este correo fue generado automáticamente por el Sistema de Inventario PPG</p>
            <p>Fecha de generación: {fecha_actual}</p>
            <p>Para más información, accede al sistema: <a href="http://localhost:5000">Sistema de Inventario</a></p>
        </div>
    </body>
    </html>
    """
    
    return html

def generar_texto_alerta_stock(productos_stock_bajo):
    """Generar contenido de texto plano para la alerta de stock"""
    fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    texto = f"""
🚨 ALERTA DE STOCK BAJO - {app.config.get('COMPANY_NAME', 'PPG - Plásticos Plasa')}

Fecha y Hora: {fecha_actual}
Productos Afectados: {len(productos_stock_bajo)}

PRODUCTOS QUE REQUIEREN ATENCIÓN:
{'='*80}

"""
    
    for i, producto in enumerate(productos_stock_bajo, 1):
        diferencia = producto['stock_actual'] - producto['stock_minimo']
        estado = "CRÍTICO" if diferencia < 0 else "BAJO"
        
        proveedor_info = producto['proveedor'] or 'Sin proveedor'
        if producto['proveedor_telefono']:
            proveedor_info += f" (Tel: {producto['proveedor_telefono']})"
        
        categoria_info = producto['categoria'] or 'Sin categoría'
        if producto['subcategoria']:
            categoria_info += f" > {producto['subcategoria']}"
        
        texto += f"""
{i}. [{estado}] {producto['descripcion']}
   Código: {producto['codigo'] or 'N/A'}
   Stock Actual: {producto['stock_actual']} | Stock Mínimo: {producto['stock_minimo']} | Diferencia: {diferencia:+d}
   Categoría: {categoria_info}
   Proveedor: {proveedor_info}
   Ubicaciones: {producto['ubicaciones_stock'] or 'Sin ubicaciones'}
   
"""
    
    texto += f"""
RECOMENDACIONES:
- Contactar a los proveedores para realizar pedidos urgentes
- Verificar si hay stock en otras ubicaciones
- Considerar productos alternativos o sustitutos
- Revisar y ajustar los niveles de stock mínimo si es necesario

---
Este correo fue generado automáticamente por el Sistema de Inventario PPG
Fecha de generación: {fecha_actual}
Para más información, accede al sistema: http://localhost:5000
"""
    
    return texto

def verificar_y_enviar_alertas_stock():
    """Verificar stock bajo y enviar alertas si es necesario"""
    try:
        # Verificar si han pasado suficientes horas desde la última alerta
        conn = get_db_connection()
        
        # Buscar la última alerta enviada
        ultima_alerta = conn.execute('''
            SELECT timestamp as fecha_creacion 
            FROM operation_logs 
            WHERE operation_type = 'STOCK_ALERT' 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''').fetchone()
        
        if ultima_alerta:
            tiempo_ultima_alerta = datetime.fromisoformat(ultima_alerta['fecha_creacion'])
            horas_transcurridas = (datetime.now() - tiempo_ultima_alerta).total_seconds() / 3600
            frecuencia_horas = app.config.get('STOCK_ALERT_FREQUENCY_HOURS', 24)
            
            if horas_transcurridas < frecuencia_horas:
                logging.info(f"Alerta de stock no enviada - faltan {frecuencia_horas - horas_transcurridas:.1f} horas")
                return False
        
        conn.close()
        
        # Obtener productos con stock bajo
        productos_stock_bajo = get_productos_stock_bajo()
        
        if productos_stock_bajo:
            logging.info(f"Encontrados {len(productos_stock_bajo)} productos con stock bajo")
            return enviar_alerta_stock_bajo(productos_stock_bajo)
        else:
            logging.info("No se encontraron productos con stock bajo")
            return True
            
    except Exception as e:
        logging.error(f"Error verificando alertas de stock: {e}")
        return False

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login de administrador"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = hash_password(password)
        
        conn = get_db_connection()
        admin_user = conn.execute('''
            SELECT id, username FROM admin_users 
            WHERE username = ? AND password_hash = ? AND is_active = 1
        ''', (username, password_hash)).fetchone()
        
        if admin_user:
            # Crear sesión
            session_token = generate_session_token()
            expires_at = datetime.now() + timedelta(hours=8)  # 8 horas de sesión
            
            conn.execute('''
                INSERT INTO admin_sessions (admin_user_id, session_token, expires_at)
                VALUES (?, ?, ?)
            ''', (admin_user['id'], session_token, expires_at))
            
            # Actualizar último login
            conn.execute('''
                UPDATE admin_users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (admin_user['id'],))
            
            conn.commit()
            conn.close()
            
            session['admin_token'] = session_token
            session['admin_user_id'] = admin_user['id']
            session['admin_username'] = admin_user['username']
            
            flash(f'Bienvenido, {admin_user["username"]}', 'success')
            return redirect(url_for('inventario'))
        else:
            conn.close()
            flash('Credenciales incorrectas', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logs')
@require_admin
def admin_logs():
    """Ver logs de operaciones de administrador"""
    conn = get_db_connection()
    
    # Obtener logs recientes (últimos 100)
    logs = conn.execute('''
        SELECT ol.*, au.username, p.descripcion as producto_nombre, u.codigo as ubicacion_codigo
        FROM operation_logs ol
        JOIN admin_users au ON ol.admin_user_id = au.id
        LEFT JOIN productos p ON ol.producto_id = p.id
        LEFT JOIN ubicaciones u ON ol.ubicacion_id = u.id
        ORDER BY ol.timestamp DESC
        LIMIT 100
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin_logs.html', logs=logs)

@app.route('/admin/logout')
def admin_logout():
    """Logout de administrador"""
    if 'admin_token' in session:
        conn = get_db_connection()
        conn.execute('DELETE FROM admin_sessions WHERE session_token = ?', (session['admin_token'],))
        conn.commit()
        conn.close()
    
    session.pop('admin_token', None)
    session.pop('admin_user_id', None)
    session.pop('admin_username', None)
    flash('Sesión de administrador cerrada', 'info')
    return redirect(url_for('inventario'))

@app.route('/admin/stock-alerts')
@require_admin
def admin_stock_alerts():
    """Panel de administración de alertas de stock"""
    # Obtener productos con stock bajo
    productos_stock_bajo = get_productos_stock_bajo()
    
    # Obtener configuración actual
    config_alertas = {
        'enabled': app.config.get('STOCK_ALERT_ENABLED', True),
        'recipients': app.config.get('STOCK_ALERT_RECIPIENTS', []),
        'frequency_hours': app.config.get('STOCK_ALERT_FREQUENCY_HOURS', 24),
        'mail_configured': bool(app.config.get('MAIL_USERNAME') and app.config.get('MAIL_PASSWORD'))
    }
    
    # Obtener historial de alertas recientes
    conn = get_db_connection()
    historial_alertas = conn.execute('''
        SELECT ol.*, au.username
        FROM operation_logs ol
        JOIN admin_users au ON ol.admin_user_id = au.id
        WHERE ol.operation_type = 'STOCK_ALERT'
        ORDER BY ol.timestamp DESC
        LIMIT 10
    ''').fetchall()
    conn.close()
    
    return render_template('admin_stock_alerts.html', 
                         productos_stock_bajo=productos_stock_bajo,
                         config_alertas=config_alertas,
                         historial_alertas=historial_alertas)

@app.route('/admin/send-stock-alert', methods=['POST'])
@require_admin
def admin_send_stock_alert():
    """Enviar alerta de stock manualmente"""
    try:
        # Obtener destinatarios del formulario o usar configuración por defecto
        destinatarios_form = request.form.get('destinatarios', '').strip()
        if destinatarios_form:
            destinatarios = [email.strip() for email in destinatarios_form.split(',') if email.strip()]
        else:
            destinatarios = app.config.get('STOCK_ALERT_RECIPIENTS', [])
        
        if not destinatarios:
            flash('No se especificaron destinatarios para la alerta', 'error')
            return redirect(url_for('admin_stock_alerts'))
        
        # Obtener productos con stock bajo
        productos_stock_bajo = get_productos_stock_bajo()
        
        if not productos_stock_bajo:
            flash('No hay productos con stock bajo en este momento', 'info')
            return redirect(url_for('admin_stock_alerts'))
        
        # Enviar alerta
        if enviar_alerta_stock_bajo(productos_stock_bajo, destinatarios):
            flash(f'Alerta de stock enviada exitosamente a {len(destinatarios)} destinatarios', 'success')
        else:
            flash('Error al enviar la alerta de stock. Revisa la configuración de correo.', 'error')
    
    except Exception as e:
        logging.error(f"Error enviando alerta manual: {e}")
        flash('Error interno al enviar la alerta', 'error')
    
    return redirect(url_for('admin_stock_alerts'))

@app.route('/admin/test-email', methods=['POST'])
@require_admin
def admin_test_email():
    """Enviar correo de prueba"""
    try:
        destinatario = request.form.get('email_prueba', '').strip()
        if not destinatario:
            flash('Especifica un email para la prueba', 'error')
            return redirect(url_for('admin_stock_alerts'))
        
        # Crear mensaje de prueba
        msg = Message(
            subject='Prueba de Configuración - Sistema de Inventario PPG',
            sender=app.config.get('MAIL_DEFAULT_SENDER'),
            recipients=[destinatario],
            body=f"""
Prueba de configuración de correo electrónico

Este es un mensaje de prueba del Sistema de Inventario PPG.
Si recibes este correo, la configuración está funcionando correctamente.

Fecha y hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Usuario administrador: {session.get('admin_username')}

Sistema de Inventario PPG
            """,
            html=f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #28a745;">✅ Prueba de Configuración Exitosa</h2>
                <p>Este es un mensaje de prueba del <strong>Sistema de Inventario PPG</strong>.</p>
                <p>Si recibes este correo, la configuración está funcionando correctamente.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; margin: 15px 0; border-left: 4px solid #28a745;">
                    <p><strong>Fecha y hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    <p><strong>Usuario administrador:</strong> {session.get('admin_username')}</p>
                </div>
                
                <hr>
                <p style="font-size: 12px; color: #666;">Sistema de Inventario PPG</p>
            </body>
            </html>
            """
        )
        
        mail.send(msg)
        
        # Registrar en logs
        log_admin_operation('EMAIL_TEST', f'Correo de prueba enviado a: {destinatario}')
        
        flash(f'Correo de prueba enviado exitosamente a: {destinatario}', 'success')
        
    except Exception as e:
        logging.error(f"Error enviando correo de prueba: {e}")
        flash(f'Error al enviar correo de prueba: {str(e)}', 'error')
    
    return redirect(url_for('admin_stock_alerts'))

@app.route('/api/productos/<int:producto_id>/stock-minimo', methods=['PUT'])
@require_admin
def update_stock_minimo(producto_id):
    """Actualizar stock mínimo de un producto"""
    try:
        data = request.get_json()
        nuevo_stock_minimo = int(data.get('stock_minimo', 0))
        
        if nuevo_stock_minimo < 0:
            return jsonify({'error': 'El stock mínimo no puede ser negativo'}), 400
        
        conn = get_db_connection()
        
        # Obtener stock mínimo actual
        producto_actual = conn.execute(
            'SELECT stock_minimo, descripcion FROM productos WHERE id = ?', 
            (producto_id,)
        ).fetchone()
        
        if not producto_actual:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        # Actualizar stock mínimo
        conn.execute(
            'UPDATE productos SET stock_minimo = ? WHERE id = ?',
            (nuevo_stock_minimo, producto_id)
        )
        conn.commit()
        
        # Registrar operación
        log_admin_operation(
            'STOCK_MINIMO_UPDATE',
            f'Stock mínimo actualizado: {producto_actual["descripcion"]} - {producto_actual["stock_minimo"]} → {nuevo_stock_minimo}',
            producto_id=producto_id,
            conn=conn
        )
        
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Stock mínimo actualizado correctamente',
            'nuevo_stock_minimo': nuevo_stock_minimo
        })
        
    except ValueError:
        return jsonify({'error': 'Valor de stock mínimo inválido'}), 400
    except Exception as e:
        logging.error(f"Error actualizando stock mínimo: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/')
def index():
    """Redirigir a productos como página principal"""
    return redirect(url_for('productos'))

@app.route('/productos')
def productos():
    """Lista de productos con filtros avanzados"""
    conn = get_db_connection()
    
    # Obtener todos los filtros posibles
    search = request.args.get('search', '').strip()
    categoria_filter = request.args.get('categoria', '')
    subcategoria_filter = request.args.get('subcategoria', '')
    marca_filter = request.args.get('marca', '')
    maquina_filter = request.args.get('maquina', '')
    codigo_filter = request.args.get('codigo', '').strip()
    stock_filter = request.args.get('stock', '')  # Nuevo filtro de stock
    
    # Construir query con filtros
    query = '''
        SELECT p.*, c.nombre as categoria, sc.nombre as subcategoria, 
               m.nombre as marca, mq.nombre as maquina,
               COALESCE(SUM(i.cantidad), 0) as stock_total
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        LEFT JOIN subcategorias sc ON p.subcategoria_id = sc.id
        LEFT JOIN marcas m ON p.marca_id = m.id
        LEFT JOIN maquinas mq ON p.maquina_id = mq.id
        LEFT JOIN inventario i ON p.id = i.producto_id
        WHERE 1=1
    '''
    
    params = []
    
    if search:
        query += ' AND (p.descripcion LIKE ? OR p.codigo LIKE ? OR p.notas LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param])
    
    if categoria_filter:
        query += ' AND c.nombre = ?'
        params.append(categoria_filter)
    
    if subcategoria_filter:
        query += ' AND sc.nombre = ?'
        params.append(subcategoria_filter)
    
    if marca_filter:
        query += ' AND m.nombre = ?'
        params.append(marca_filter)
    
    if maquina_filter:
        query += ' AND mq.nombre = ?'
        params.append(maquina_filter)
    
    if codigo_filter:
        query += ' AND p.codigo LIKE ?'
        params.append(f'%{codigo_filter}%')
    
    query += ' GROUP BY p.id'
    
    # Aplicar filtro de stock después del GROUP BY
    if stock_filter == 'sin_stock':
        query += ' HAVING stock_total = 0'
    elif stock_filter == 'con_stock':
        query += ' HAVING stock_total > 0'
    elif stock_filter == 'stock_bajo':
        query += ' HAVING stock_total > 0 AND stock_total < p.cantidad_requerida'
    
    query += ' ORDER BY p.descripcion'
    
    productos = conn.execute(query, params).fetchall()
    
    # Obtener listas para filtros
    categorias = conn.execute('SELECT DISTINCT nombre FROM categorias WHERE nombre IS NOT NULL ORDER BY nombre').fetchall()
    subcategorias = conn.execute('SELECT DISTINCT nombre FROM subcategorias WHERE nombre IS NOT NULL ORDER BY nombre').fetchall()
    marcas = conn.execute('SELECT DISTINCT nombre FROM marcas WHERE nombre IS NOT NULL ORDER BY nombre').fetchall()
    maquinas = conn.execute('SELECT DISTINCT nombre FROM maquinas WHERE nombre IS NOT NULL ORDER BY nombre').fetchall()
    
    conn.close()
    
    return render_template('productos.html', 
                         productos=productos, 
                         categorias=categorias,
                         subcategorias=subcategorias,
                         marcas=marcas, 
                         maquinas=maquinas,
                         filters={
                             'search': search,
                             'categoria': categoria_filter,
                             'subcategoria': subcategoria_filter,
                             'marca': marca_filter,
                             'maquina': maquina_filter,
                             'codigo': codigo_filter,
                             'stock': stock_filter
                         })

@app.route('/inventario')
def inventario():
    """Vista del inventario - lista simple de productos con stock > 0"""
    conn = get_db_connection()
    
    # Obtener filtros
    search = request.args.get('search', '').strip()
    categoria_filter = request.args.get('categoria', '')
    
    # Query para obtener solo productos con stock > 0 (para la tabla)
    query = '''
        SELECT p.*, c.nombre as categoria, sc.nombre as subcategoria, 
               m.nombre as marca,
               GROUP_CONCAT(mq.nombre, ', ') as maquinas,
               COALESCE(SUM(i.cantidad), 0) as stock_total,
               GROUP_CONCAT(u.codigo || ':' || i.cantidad, ', ') as ubicaciones_detalle
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        LEFT JOIN subcategorias sc ON p.subcategoria_id = sc.id
        LEFT JOIN marcas m ON p.marca_id = m.id
        LEFT JOIN producto_maquinas pm ON p.id = pm.producto_id
        LEFT JOIN maquinas mq ON pm.maquina_id = mq.id
        LEFT JOIN inventario i ON p.id = i.producto_id
        LEFT JOIN ubicaciones u ON i.ubicacion_id = u.id
        WHERE 1=1
    '''
    
    params = []
    
    if search:
        query += ' AND (p.descripcion LIKE ? OR p.codigo LIKE ? OR c.nombre LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param])
    
    if categoria_filter:
        query += ' AND c.nombre = ?'
        params.append(categoria_filter)
    
    query += ' GROUP BY p.id HAVING stock_total > 0 ORDER BY p.descripcion'
    
    productos_con_stock = conn.execute(query, params).fetchall()
    
    # Obtener TODOS los productos para el modal de entrada de material
    todos_productos = conn.execute('''
        SELECT p.id, p.descripcion, p.codigo
        FROM productos p
        ORDER BY p.descripcion
    ''').fetchall()
    
    # Obtener listas para filtros
    categorias = conn.execute('SELECT DISTINCT nombre FROM categorias WHERE nombre IS NOT NULL ORDER BY nombre').fetchall()
    
    # Obtener todas las ubicaciones para el selector de agregar stock
    ubicaciones = conn.execute('SELECT DISTINCT codigo FROM ubicaciones ORDER BY codigo').fetchall()
    
    conn.close()
    
    return render_template('inventario.html', 
                         productos=productos_con_stock,  # Para la tabla (solo con stock)
                         todos_productos=todos_productos,  # Para el modal de entrada (todos)
                         categorias=categorias,
                         ubicaciones=ubicaciones,
                         filters={
                             'search': search,
                             'categoria': categoria_filter
                         })

@app.route('/producto/nuevo')
def nuevo_producto():
    """Formulario para nuevo producto"""
    conn = get_db_connection()
    
    categorias = conn.execute('SELECT * FROM categorias ORDER BY nombre').fetchall()
    marcas = conn.execute('SELECT * FROM marcas ORDER BY nombre').fetchall()
    maquinas = conn.execute('SELECT * FROM maquinas ORDER BY nombre').fetchall()
    proveedores = conn.execute('SELECT * FROM proveedores ORDER BY nombre').fetchall()
    
    conn.close()
    return render_template('producto_form.html', categorias=categorias, marcas=marcas, maquinas=maquinas, proveedores=proveedores)

@app.route('/producto/editar/<int:id>')
def editar_producto(id):
    """Formulario para editar producto"""
    conn = get_db_connection()
    
    producto = conn.execute('''
        SELECT p.*, c.nombre as categoria, sc.nombre as subcategoria, 
               m.nombre as marca, mq.nombre as maquina, pr.nombre as proveedor
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        LEFT JOIN subcategorias sc ON p.subcategoria_id = sc.id
        LEFT JOIN marcas m ON p.marca_id = m.id
        LEFT JOIN maquinas mq ON p.maquina_id = mq.id
        LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
        WHERE p.id = ?
    ''', (id,)).fetchone()
    
    if not producto:
        flash('Producto no encontrado', 'error')
        return redirect(url_for('productos'))
    
    categorias = conn.execute('SELECT * FROM categorias ORDER BY nombre').fetchall()
    subcategorias = conn.execute('SELECT * FROM subcategorias WHERE categoria_id = ? ORDER BY nombre', 
                                (producto['categoria_id'],)).fetchall()
    marcas = conn.execute('SELECT * FROM marcas ORDER BY nombre').fetchall()
    maquinas = conn.execute('SELECT * FROM maquinas ORDER BY nombre').fetchall()
    proveedores = conn.execute('SELECT * FROM proveedores ORDER BY nombre').fetchall()
    
    conn.close()
    return render_template('producto_form.html', producto=producto, categorias=categorias, 
                         subcategorias=subcategorias, marcas=marcas, maquinas=maquinas, proveedores=proveedores)

@app.route('/producto/guardar', methods=['POST'])
def guardar_producto():
    """Guardar producto nuevo o editado"""
    conn = get_db_connection()
    
    try:
        descripcion = request.form['descripcion']
        codigo = request.form['codigo'] if request.form['codigo'] else None
        categoria_id = request.form['categoria_id'] if request.form['categoria_id'] else None
        subcategoria_id = request.form['subcategoria_id'] if request.form['subcategoria_id'] else None
        marca_id = request.form['marca_id'] if request.form['marca_id'] else None
        proveedor_id = request.form['proveedor_id'] if request.form['proveedor_id'] else None
        notas = request.form['notas']
        cantidad_requerida = int(request.form['cantidad_requerida']) if request.form['cantidad_requerida'] else 1
        stock_minimo = int(request.form['stock_minimo']) if request.form['stock_minimo'] else 5
        maquina_id = request.form['maquina_id'] if request.form['maquina_id'] else None
        
        producto_id = request.form.get('producto_id')
        
        if producto_id:  # Editar producto existente
            conn.execute('''
                UPDATE productos 
                SET descripcion=?, codigo=?, categoria_id=?, subcategoria_id=?, marca_id=?, 
                    proveedor_id=?, notas=?, cantidad_requerida=?, stock_minimo=?, maquina_id=?, fecha_actualizacion=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (descripcion, codigo, categoria_id, subcategoria_id, marca_id, 
                  proveedor_id, notas, cantidad_requerida, stock_minimo, maquina_id, producto_id))
            flash('Producto actualizado exitosamente', 'success')
        else:  # Crear nuevo producto
            conn.execute('''
                INSERT INTO productos (descripcion, codigo, categoria_id, subcategoria_id, marca_id, 
                                     proveedor_id, notas, cantidad_requerida, stock_minimo, maquina_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (descripcion, codigo, categoria_id, subcategoria_id, marca_id, 
                  proveedor_id, notas, cantidad_requerida, stock_minimo, maquina_id))
            flash('Producto creado exitosamente', 'success')
        
        conn.commit()
        
    except Exception as e:
        flash(f'Error al guardar producto: {str(e)}', 'error')
    
    conn.close()
    return redirect(url_for('productos'))

@app.route('/admin/actualizar-stock-rapido', methods=['POST'])
@require_admin
def actualizar_stock_rapido():
    """Actualización rápida de stock por administrador - OPTIMIZADA"""
    try:
        data = request.get_json()
        cambios = data.get('cambios', {})
        
        if not cambios:
            return jsonify({'success': False, 'error': 'No hay cambios para aplicar'})
        
        conn = get_db_connection()
        cambios_aplicados = 0
        
        try:
            # Iniciar transacción
            conn.execute('BEGIN TRANSACTION')
            
            # Preparar consultas para optimizar
            update_query = '''UPDATE inventario SET cantidad = ?, fecha_actualizacion = CURRENT_TIMESTAMP 
                             WHERE producto_id = ? AND ubicacion_id = ?'''
            insert_query = '''INSERT INTO inventario (producto_id, ubicacion_id, cantidad) VALUES (?, ?, ?)'''
            delete_query = '''DELETE FROM inventario WHERE producto_id = ? AND ubicacion_id = ?'''
            
            # Obtener información de productos y ubicaciones en lotes
            producto_ids = [cambio['producto_id'] for cambio in cambios.values()]
            ubicacion_ids = [cambio['ubicacion_id'] for cambio in cambios.values()]
            
            # Consulta optimizada para obtener info de productos
            productos_info = {}
            if producto_ids:
                placeholders = ','.join('?' * len(set(producto_ids)))
                productos_result = conn.execute(f'SELECT id, descripcion FROM productos WHERE id IN ({placeholders})', 
                                              list(set(producto_ids))).fetchall()
                productos_info = {p['id']: p['descripcion'] for p in productos_result}
            
            # Consulta optimizada para obtener info de ubicaciones
            ubicaciones_info = {}
            if ubicacion_ids:
                placeholders = ','.join('?' * len(set(ubicacion_ids)))
                ubicaciones_result = conn.execute(f'SELECT id, codigo FROM ubicaciones WHERE id IN ({placeholders})', 
                                                list(set(ubicacion_ids))).fetchall()
                ubicaciones_info = {u['id']: u['codigo'] for u in ubicaciones_result}
            
            # Procesar cambios
            log_entries = []
            
            for key, cambio in cambios.items():
                producto_id = cambio['producto_id']
                ubicacion_id = cambio['ubicacion_id']
                stock_actual = cambio['stock_actual']
                nuevo_stock = cambio['nuevo_stock']
                
                producto_desc = productos_info.get(producto_id, f'ID:{producto_id}')
                ubicacion_codigo = ubicaciones_info.get(ubicacion_id, f'ID:{ubicacion_id}')
                
                if nuevo_stock == 0:
                    # Eliminar registro si el stock es 0
                    conn.execute(delete_query, (producto_id, ubicacion_id))
                    descripcion = f"Eliminado stock de {producto_desc} en {ubicacion_codigo}"
                else:
                    # Verificar si existe el registro
                    existing = conn.execute('SELECT 1 FROM inventario WHERE producto_id = ? AND ubicacion_id = ?', 
                                          (producto_id, ubicacion_id)).fetchone()
                    
                    if existing:
                        conn.execute(update_query, (nuevo_stock, producto_id, ubicacion_id))
                    else:
                        conn.execute(insert_query, (producto_id, ubicacion_id, nuevo_stock))
                    
                    descripcion = f"Actualizado stock de {producto_desc} en {ubicacion_codigo}: {stock_actual} → {nuevo_stock}"
                
                # Preparar entrada de log (se insertará en lote)
                log_entries.append({
                    'operation_type': 'STOCK_EDIT',
                    'description': descripcion,
                    'producto_id': producto_id,
                    'ubicacion_id': ubicacion_id,
                    'old_quantity': stock_actual,
                    'new_quantity': nuevo_stock
                })
                
                cambios_aplicados += 1
            
            # Insertar logs en lote
            if log_entries:
                ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
                admin_user_id = session.get('admin_user_id')
                
                log_values = []
                for entry in log_entries:
                    log_values.append((
                        admin_user_id, entry['operation_type'], entry['producto_id'], 
                        entry['ubicacion_id'], entry['old_quantity'], entry['new_quantity'], 
                        entry['description'], ip_address
                    ))
                
                conn.executemany('''
                    INSERT INTO operation_logs (admin_user_id, operation_type, producto_id, ubicacion_id, 
                                              old_quantity, new_quantity, description, ip_address)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', log_values)
            
            # Confirmar transacción
            conn.commit()
            
            # Log consolidado en archivo
            logging.info(f"ADMIN_OP: {session.get('admin_username')} - BULK_STOCK_EDIT - {cambios_aplicados} cambios aplicados")
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
        
        return jsonify({
            'success': True, 
            'cambios_aplicados': cambios_aplicados,
            'message': f'{cambios_aplicados} cambio(s) aplicado(s) correctamente'
        })
        
    except Exception as e:
        logging.error(f"Error en actualización rápida de stock: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/inventario/agregar', methods=['POST'])
def agregar_stock():
    """Agregar producto a una ubicación"""
    conn = get_db_connection()
    
    try:
        producto_id = request.form['producto_id']
        ubicacion_codigo = request.form['ubicacion_codigo']
        cantidad = int(request.form['cantidad'])
        
        # Obtener o crear ubicación
        ubicacion = conn.execute('SELECT id FROM ubicaciones WHERE codigo = ?', (ubicacion_codigo,)).fetchone()
        if not ubicacion:
            cursor = conn.execute('INSERT INTO ubicaciones (codigo, nombre) VALUES (?, ?)', 
                        (ubicacion_codigo, ubicacion_codigo))
            ubicacion_id = cursor.lastrowid
        else:
            ubicacion_id = ubicacion['id']
        
        # Insertar o actualizar inventario
        existing = conn.execute('SELECT * FROM inventario WHERE producto_id = ? AND ubicacion_id = ?', 
                               (producto_id, ubicacion_id)).fetchone()
        
        if existing:
            nueva_cantidad = existing['cantidad'] + cantidad
            conn.execute('UPDATE inventario SET cantidad = ?, fecha_actualizacion = CURRENT_TIMESTAMP WHERE producto_id = ? AND ubicacion_id = ?', 
                        (nueva_cantidad, producto_id, ubicacion_id))
        else:
            conn.execute('INSERT INTO inventario (producto_id, ubicacion_id, cantidad) VALUES (?, ?, ?)', 
                        (producto_id, ubicacion_id, cantidad))
        
        conn.commit()
        flash('Stock agregado exitosamente', 'success')
        
    except Exception as e:
        flash(f'Error al agregar stock: {str(e)}', 'error')
    
    conn.close()
    return redirect(url_for('inventario'))

@app.route('/inventario/salida', methods=['POST'])
def salida_stock():
    """Registrar salida de material del inventario"""
    conn = get_db_connection()
    
    try:
        producto_id = request.form['producto_id']
        ubicacion_id = request.form['ubicacion_id']
        cantidad_salida = int(request.form['cantidad'])
        motivo = request.form['motivo']
        
        # Verificar stock disponible
        stock_actual = conn.execute('SELECT cantidad FROM inventario WHERE producto_id = ? AND ubicacion_id = ?', 
                                   (producto_id, ubicacion_id)).fetchone()
        
        if not stock_actual or stock_actual['cantidad'] < cantidad_salida:
            flash('Error: No hay suficiente stock disponible', 'error')
        else:
            nueva_cantidad = stock_actual['cantidad'] - cantidad_salida
            
            if nueva_cantidad == 0:
                # Si queda en 0, eliminar el registro
                conn.execute('DELETE FROM inventario WHERE producto_id = ? AND ubicacion_id = ?', 
                            (producto_id, ubicacion_id))
            else:
                # Actualizar cantidad
                conn.execute('UPDATE inventario SET cantidad = ?, fecha_actualizacion = CURRENT_TIMESTAMP WHERE producto_id = ? AND ubicacion_id = ?', 
                            (nueva_cantidad, producto_id, ubicacion_id))
            
            conn.commit()
            flash(f'Salida de material registrada exitosamente. Motivo: {motivo}', 'success')
        
    except Exception as e:
        flash(f'Error al registrar salida: {str(e)}', 'error')
    
    conn.close()
    return redirect(url_for('inventario'))

@app.route('/inventario/cambio-ubicacion', methods=['POST'])
def cambio_ubicacion():
    """Cambiar producto de una ubicación a otra"""
    conn = get_db_connection()
    
    try:
        producto_id = request.form['producto_id']
        ubicacion_origen_id = request.form['ubicacion_origen_id']
        ubicacion_destino_codigo = request.form['ubicacion_destino_id']
        cantidad_mover = int(request.form['cantidad'])
        motivo = request.form['motivo']
        
        # Obtener información del producto
        producto = conn.execute('SELECT descripcion FROM productos WHERE id = ?', (producto_id,)).fetchone()
        if not producto:
            flash('Producto no encontrado', 'error')
            return redirect(url_for('inventario'))
        
        # Verificar stock disponible en ubicación origen
        stock_origen = conn.execute('SELECT cantidad FROM inventario WHERE producto_id = ? AND ubicacion_id = ?', 
                                   (producto_id, ubicacion_origen_id)).fetchone()
        
        if not stock_origen or stock_origen['cantidad'] < cantidad_mover:
            flash('Error: No hay suficiente stock disponible en la ubicación origen', 'error')
            return redirect(url_for('inventario'))
        
        # Obtener información de ubicación origen
        ubicacion_origen = conn.execute('SELECT codigo FROM ubicaciones WHERE id = ?', (ubicacion_origen_id,)).fetchone()
        
        # Obtener o crear ubicación destino
        ubicacion_destino = conn.execute('SELECT id FROM ubicaciones WHERE codigo = ?', (ubicacion_destino_codigo,)).fetchone()
        if not ubicacion_destino:
            cursor = conn.execute('INSERT INTO ubicaciones (codigo, nombre) VALUES (?, ?)', 
                        (ubicacion_destino_codigo, ubicacion_destino_codigo))
            ubicacion_destino_id = cursor.lastrowid
        else:
            ubicacion_destino_id = ubicacion_destino['id']
        
        # Actualizar stock en ubicación origen
        nueva_cantidad_origen = stock_origen['cantidad'] - cantidad_mover
        if nueva_cantidad_origen == 0:
            # Si queda en 0, eliminar el registro
            conn.execute('DELETE FROM inventario WHERE producto_id = ? AND ubicacion_id = ?', 
                        (producto_id, ubicacion_origen_id))
        else:
            # Actualizar cantidad
            conn.execute('UPDATE inventario SET cantidad = ? WHERE producto_id = ? AND ubicacion_id = ?', 
                        (nueva_cantidad_origen, producto_id, ubicacion_origen_id))
        
        # Actualizar o insertar stock en ubicación destino
        stock_destino = conn.execute('SELECT cantidad FROM inventario WHERE producto_id = ? AND ubicacion_id = ?', 
                                   (producto_id, ubicacion_destino_id)).fetchone()
        
        if stock_destino:
            # Si ya existe stock en destino, sumar
            nueva_cantidad_destino = stock_destino['cantidad'] + cantidad_mover
            conn.execute('UPDATE inventario SET cantidad = ? WHERE producto_id = ? AND ubicacion_id = ?', 
                        (nueva_cantidad_destino, producto_id, ubicacion_destino_id))
        else:
            # Crear nuevo registro en destino
            conn.execute('INSERT INTO inventario (producto_id, ubicacion_id, cantidad) VALUES (?, ?, ?)', 
                        (producto_id, ubicacion_destino_id, cantidad_mover))
        
        conn.commit()
        
        # Mensaje de éxito
        flash(f'Cambio de ubicación exitoso: {cantidad_mover} unidades de "{producto["descripcion"]}" movidas de {ubicacion_origen["codigo"]} a {ubicacion_destino_codigo}. Motivo: {motivo}', 'success')
        
        # Log de administrador si está logueado
        if is_admin_logged_in():
            log_admin_operation(
                operation_type='LOCATION_CHANGE',
                description=f'Cambio de ubicación: {producto["descripcion"]} - {cantidad_mover} unidades de {ubicacion_origen["codigo"]} a {ubicacion_destino_codigo}',
                producto_id=producto_id,
                ubicacion_id=ubicacion_origen_id,
                old_quantity=stock_origen['cantidad'],
                new_quantity=nueva_cantidad_origen,
                conn=conn
            )
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al realizar cambio de ubicación: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('inventario'))

@app.route('/api/producto/<int:id>/ubicaciones-stock')
def api_ubicaciones_stock(id):
    """API para obtener ubicaciones con stock de un producto específico"""
    conn = get_db_connection()
    
    ubicaciones = conn.execute('''
        SELECT i.ubicacion_id, u.codigo, i.cantidad
        FROM inventario i
        JOIN ubicaciones u ON i.ubicacion_id = u.id
        WHERE i.producto_id = ? AND i.cantidad > 0
        ORDER BY u.codigo
    ''', (id,)).fetchall()
    
    conn.close()
    
    return jsonify({
        'ubicaciones': [dict(ub) for ub in ubicaciones]
    })

# APIs para AJAX
@app.route('/api/subcategorias/<int:categoria_id>')
def api_subcategorias(categoria_id):
    """API para obtener subcategorías por categoría"""
    conn = get_db_connection()
    subcategorias = conn.execute('SELECT * FROM subcategorias WHERE categoria_id = ? ORDER BY nombre', 
                                (categoria_id,)).fetchall()
    conn.close()
    return jsonify([dict(sc) for sc in subcategorias])

@app.route('/api/categoria/<int:id>')
def api_categoria(id):
    """API para obtener detalles de una categoría"""
    conn = get_db_connection()
    
    # Obtener información de la categoría
    categoria = conn.execute('''
        SELECT c.*, COUNT(DISTINCT sc.id) as subcategorias_count,
               COUNT(DISTINCT p.id) as productos_count
        FROM categorias c
        LEFT JOIN subcategorias sc ON c.id = sc.categoria_id
        LEFT JOIN productos p ON c.id = p.categoria_id
        WHERE c.id = ?
        GROUP BY c.id
    ''', (id,)).fetchone()
    
    if not categoria:
        conn.close()
        return jsonify({'error': 'Categoría no encontrada'}), 404
    
    # Obtener subcategorías de esta categoría
    subcategorias = conn.execute('''
        SELECT sc.id, sc.nombre, COUNT(DISTINCT p.id) as productos_count
        FROM subcategorias sc
        LEFT JOIN productos p ON sc.id = p.subcategoria_id
        WHERE sc.categoria_id = ?
        GROUP BY sc.id
        ORDER BY sc.nombre
    ''', (id,)).fetchall()
    
    conn.close()
    
    # Preparar respuesta
    resultado = dict(categoria)
    resultado['subcategorias'] = [dict(sc) for sc in subcategorias]
    
    return jsonify(resultado)

@app.route('/api/maquina/<int:id>')
def api_maquina(id):
    """API para obtener detalles de una máquina"""
    conn = get_db_connection()
    
    # Obtener información de la máquina
    maquina = conn.execute('''
        SELECT m.*, COUNT(DISTINCT pm.producto_id) as productos_count
        FROM maquinas m
        LEFT JOIN producto_maquinas pm ON m.id = pm.maquina_id
        WHERE m.id = ?
        GROUP BY m.id
    ''', (id,)).fetchone()
    
    if not maquina:
        conn.close()
        return jsonify({'error': 'Máquina no encontrada'}), 404
    
    # Obtener productos que usan esta máquina
    productos = conn.execute('''
        SELECT p.id, p.descripcion, p.codigo
        FROM productos p
        JOIN producto_maquinas pm ON p.id = pm.producto_id
        WHERE pm.maquina_id = ?
        ORDER BY p.descripcion
    ''', (id,)).fetchall()
    
    conn.close()
    
    # Preparar respuesta
    resultado = dict(maquina)
    resultado['productos'] = [dict(prod) for prod in productos]
    
    return jsonify(resultado)

@app.route('/exportar/categorias')
def exportar_categorias():
    """Exportar categorías y subcategorías a CSV"""
    conn = get_db_connection()
    
    # Obtener los mismos filtros que en la vista
    search = request.args.get('search', '').strip()
    
    # Query para categorías
    query_categorias = '''
        SELECT c.id, c.nombre, c.fecha_creacion,
               COUNT(DISTINCT sc.id) as subcategorias_count,
               COUNT(DISTINCT p.id) as productos_count
        FROM categorias c
        LEFT JOIN subcategorias sc ON c.id = sc.categoria_id
        LEFT JOIN productos p ON c.id = p.categoria_id
        WHERE 1=1
    '''
    
    params = []
    
    if search:
        query_categorias += ' AND c.nombre LIKE ?'
        params.append(f'%{search}%')
    
    query_categorias += ' GROUP BY c.id ORDER BY c.nombre'
    
    categorias = conn.execute(query_categorias, params).fetchall()
    
    # Query para subcategorías
    query_subcategorias = '''
        SELECT sc.id, sc.nombre, c.nombre as categoria_nombre,
               COUNT(DISTINCT p.id) as productos_count
        FROM subcategorias sc
        JOIN categorias c ON sc.categoria_id = c.id
        LEFT JOIN productos p ON sc.id = p.subcategoria_id
        WHERE 1=1
    '''
    
    if search:
        query_subcategorias += ' AND (sc.nombre LIKE ? OR c.nombre LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    
    query_subcategorias += ' GROUP BY sc.id ORDER BY c.nombre, sc.nombre'
    
    subcategorias = conn.execute(query_subcategorias, params).fetchall()
    
    conn.close()
    
    # Crear CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Sección de Categorías
    writer.writerow(['=== CATEGORÍAS ==='])
    writer.writerow(['ID', 'Nombre', 'Subcategorías', 'Productos', 'Fecha Creación'])
    
    for categoria in categorias:
        writer.writerow([
            categoria['id'],
            categoria['nombre'],
            categoria['subcategorias_count'],
            categoria['productos_count'],
            categoria['fecha_creacion'] or ''
        ])
    
    # Separador
    writer.writerow([])
    
    # Sección de Subcategorías
    writer.writerow(['=== SUBCATEGORÍAS ==='])
    writer.writerow(['ID', 'Nombre', 'Categoría', 'Productos'])
    
    for subcategoria in subcategorias:
        writer.writerow([
            subcategoria['id'],
            subcategoria['nombre'],
            subcategoria['categoria_nombre'],
            subcategoria['productos_count']
        ])
    
    # Preparar respuesta
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'categorias_{timestamp}.csv'
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

@app.route('/api/producto/<int:id>')
def api_producto(id):
    """API para obtener detalles de un producto con ubicaciones de stock"""
    conn = get_db_connection()
    
    # Obtener información del producto
    producto = conn.execute('''
        SELECT p.*, c.nombre as categoria, sc.nombre as subcategoria, 
               m.nombre as marca, mq.nombre as maquina, pr.nombre as proveedor,
               pr.contacto as proveedor_contacto, pr.telefono as proveedor_telefono,
               pr.email as proveedor_email, pr.pagina_web as proveedor_web
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        LEFT JOIN subcategorias sc ON p.subcategoria_id = sc.id
        LEFT JOIN marcas m ON p.marca_id = m.id
        LEFT JOIN maquinas mq ON p.maquina_id = mq.id
        LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
        WHERE p.id = ?
    ''', (id,)).fetchone()
    
    if not producto:
        conn.close()
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    # Obtener ubicaciones con stock del producto
    ubicaciones_stock = conn.execute('''
        SELECT u.codigo, u.nombre, i.cantidad, i.fecha_actualizacion
        FROM inventario i
        JOIN ubicaciones u ON i.ubicacion_id = u.id
        WHERE i.producto_id = ? AND i.cantidad > 0
        ORDER BY u.codigo
    ''', (id,)).fetchall()
    
    # Calcular stock total
    stock_total = conn.execute('''
        SELECT COALESCE(SUM(cantidad), 0) as total
        FROM inventario
        WHERE producto_id = ?
    ''', (id,)).fetchone()['total']
    
    conn.close()
    
    # Preparar respuesta
    resultado = dict(producto)
    resultado['stock_total'] = stock_total
    resultado['ubicaciones'] = [dict(ub) for ub in ubicaciones_stock]
    
    return jsonify(resultado)

@app.route('/ubicaciones')
def ubicaciones():
    """Vista de gestión de ubicaciones"""
    conn = get_db_connection()
    
    # Obtener filtros
    search = request.args.get('search', '').strip()
    
    # Query para obtener ubicaciones con información de stock
    query = '''
        SELECT u.id, u.codigo, u.nombre, u.fecha_creacion,
               COUNT(DISTINCT i.producto_id) as productos_count,
               COALESCE(SUM(i.cantidad), 0) as stock_total
        FROM ubicaciones u
        LEFT JOIN inventario i ON u.id = i.ubicacion_id
        WHERE 1=1
    '''
    
    params = []
    
    if search:
        query += ' AND (u.codigo LIKE ? OR u.nombre LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param])
    
    query += ' GROUP BY u.id ORDER BY u.codigo'
    
    ubicaciones = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('ubicaciones.html', 
                         ubicaciones=ubicaciones,
                         filters={'search': search})

@app.route('/categorias')
def categorias():
    """Vista de gestión de categorías y subcategorías"""
    conn = get_db_connection()
    
    # Obtener filtros
    search = request.args.get('search', '').strip()
    
    # Query para obtener categorías con información de subcategorías y productos
    query = '''
        SELECT c.id, c.nombre, c.fecha_creacion,
               COUNT(DISTINCT sc.id) as subcategorias_count,
               COUNT(DISTINCT p.id) as productos_count
        FROM categorias c
        LEFT JOIN subcategorias sc ON c.id = sc.categoria_id
        LEFT JOIN productos p ON c.id = p.categoria_id
        WHERE 1=1
    '''
    
    params = []
    
    if search:
        query += ' AND c.nombre LIKE ?'
        search_param = f'%{search}%'
        params.append(search_param)
    
    query += ' GROUP BY c.id ORDER BY c.nombre'
    
    categorias = conn.execute(query, params).fetchall()
    
    # Obtener todas las subcategorías para mostrar en la tabla
    subcategorias_query = '''
        SELECT sc.id, sc.nombre, sc.categoria_id, c.nombre as categoria_nombre,
               COUNT(DISTINCT p.id) as productos_count
        FROM subcategorias sc
        JOIN categorias c ON sc.categoria_id = c.id
        LEFT JOIN productos p ON sc.id = p.subcategoria_id
        WHERE 1=1
    '''
    
    if search:
        subcategorias_query += ' AND (sc.nombre LIKE ? OR c.nombre LIKE ?)'
        params.extend([search_param, search_param])
    
    subcategorias_query += ' GROUP BY sc.id ORDER BY c.nombre, sc.nombre'
    
    subcategorias = conn.execute(subcategorias_query, params).fetchall()
    
    conn.close()
    
    return render_template('categorias.html', 
                         categorias=categorias,
                         subcategorias=subcategorias,
                         filters={'search': search})

@app.route('/maquinas')
def maquinas():
    """Vista de gestión de máquinas"""
    conn = get_db_connection()
    
    # Obtener filtros
    search = request.args.get('search', '').strip()
    
    # Query para obtener máquinas con información de productos
    query = '''
        SELECT m.id, m.nombre, m.fecha_creacion,
               COUNT(DISTINCT pm.producto_id) as productos_count
        FROM maquinas m
        LEFT JOIN producto_maquinas pm ON m.id = pm.maquina_id
        WHERE 1=1
    '''
    
    params = []
    
    if search:
        query += ' AND m.nombre LIKE ?'
        search_param = f'%{search}%'
        params.append(search_param)
    
    query += ' GROUP BY m.id ORDER BY m.nombre'
    
    maquinas = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('maquinas.html', 
                         maquinas=maquinas,
                         filters={'search': search})

@app.route('/proveedores')
def proveedores():
    """Vista de gestión de proveedores"""
    conn = get_db_connection()
    
    # Obtener filtros
    search = request.args.get('search', '').strip()
    
    # Query para obtener proveedores con información de productos
    query = '''
        SELECT p.id, p.nombre, p.contacto, p.telefono, p.email, 
               p.pagina_web, p.fecha_creacion,
               COUNT(DISTINCT pr.id) as productos_count
        FROM proveedores p
        LEFT JOIN productos pr ON p.id = pr.proveedor_id
        WHERE 1=1
    '''
    
    params = []
    
    if search:
        query += ' AND (p.nombre LIKE ? OR p.contacto LIKE ? OR p.email LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param])
    
    query += ' GROUP BY p.id ORDER BY p.nombre'
    
    proveedores = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('proveedores.html', 
                         proveedores=proveedores,
                         filters={'search': search})

@app.route('/proveedor/nuevo')
def nuevo_proveedor():
    """Formulario para nuevo proveedor"""
    return render_template('proveedor_form.html')

@app.route('/proveedor/editar/<int:id>')
def editar_proveedor(id):
    """Formulario para editar proveedor"""
    conn = get_db_connection()
    
    proveedor = conn.execute('SELECT * FROM proveedores WHERE id = ?', (id,)).fetchone()
    
    if not proveedor:
        flash('Proveedor no encontrado', 'error')
        return redirect(url_for('proveedores'))
    
    # Obtener productos que usan este proveedor
    productos = conn.execute('''
        SELECT p.id, p.descripcion, p.codigo
        FROM productos p
        WHERE p.proveedor_id = ?
        ORDER BY p.descripcion
    ''', (id,)).fetchall()
    
    conn.close()
    return render_template('proveedor_form.html', proveedor=proveedor, productos=productos)

@app.route('/proveedor/guardar', methods=['POST'])
def guardar_proveedor():
    """Guardar proveedor nuevo o editado"""
    conn = get_db_connection()
    
    try:
        nombre = request.form['nombre'].strip()
        contacto = request.form.get('contacto', '').strip()
        telefono = request.form.get('telefono', '').strip()
        email = request.form.get('email', '').strip()
        pagina_web = request.form.get('pagina_web', '').strip()
        direccion = request.form.get('direccion', '').strip()
        notas = request.form.get('notas', '').strip()
        proveedor_id = request.form.get('proveedor_id')
        
        if not nombre:
            flash('El nombre del proveedor es requerido', 'error')
            return redirect(url_for('proveedores'))
        
        # Verificar que el nombre no esté en uso por otro proveedor
        existing = conn.execute('SELECT id FROM proveedores WHERE nombre = ? AND id != ?', 
                               (nombre, proveedor_id or 0)).fetchone()
        
        if existing:
            flash(f'El nombre "{nombre}" ya está en uso por otro proveedor', 'error')
            return redirect(url_for('proveedores'))
        
        if proveedor_id:  # Editar proveedor existente
            conn.execute('''
                UPDATE proveedores 
                SET nombre=?, contacto=?, telefono=?, email=?, pagina_web=?, 
                    direccion=?, notas=?, fecha_actualizacion=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (nombre, contacto or None, telefono or None, email or None, 
                  pagina_web or None, direccion or None, notas or None, proveedor_id))
            flash('Proveedor actualizado exitosamente', 'success')
            
            # Log de administrador si está logueado
            if is_admin_logged_in():
                log_admin_operation(
                    operation_type='SUPPLIER_EDIT',
                    description=f'Proveedor editado: {nombre}',
                    conn=conn
                )
        else:  # Crear nuevo proveedor
            cursor = conn.execute('''
                INSERT INTO proveedores (nombre, contacto, telefono, email, pagina_web, direccion, notas)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (nombre, contacto or None, telefono or None, email or None, 
                  pagina_web or None, direccion or None, notas or None))
            nuevo_proveedor_id = cursor.lastrowid
            flash('Proveedor creado exitosamente', 'success')
            
            # Log de administrador si está logueado
            if is_admin_logged_in():
                log_admin_operation(
                    operation_type='SUPPLIER_CREATE',
                    description=f'Nuevo proveedor creado: {nombre}',
                    conn=conn
                )
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al guardar proveedor: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('proveedores'))

@app.route('/proveedor/eliminar/<int:id>', methods=['POST'])
def eliminar_proveedor(id):
    """Eliminar proveedor (solo si no tiene productos)"""
    conn = get_db_connection()
    
    try:
        # Verificar que no tenga productos
        productos = conn.execute('SELECT COUNT(*) as count FROM productos WHERE proveedor_id = ?', (id,)).fetchone()
        
        if productos['count'] > 0:
            flash('No se puede eliminar un proveedor que tiene productos asignados', 'error')
        else:
            proveedor = conn.execute('SELECT nombre FROM proveedores WHERE id = ?', (id,)).fetchone()
            
            if proveedor:
                conn.execute('DELETE FROM proveedores WHERE id = ?', (id,))
                conn.commit()
                
                flash(f'Proveedor "{proveedor["nombre"]}" eliminado exitosamente', 'success')
                
                # Log de administrador si está logueado
                if is_admin_logged_in():
                    log_admin_operation(
                        operation_type='SUPPLIER_DELETE',
                        description=f'Proveedor eliminado: {proveedor["nombre"]}',
                        conn=conn
                    )
            else:
                flash('Proveedor no encontrado', 'error')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al eliminar proveedor: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('proveedores'))

@app.route('/api/proveedor/<int:id>')
def api_proveedor(id):
    """API para obtener detalles de un proveedor"""
    conn = get_db_connection()
    
    try:
        # Obtener información del proveedor
        proveedor = conn.execute('SELECT * FROM proveedores WHERE id = ?', (id,)).fetchone()
        
        if not proveedor:
            return jsonify({'error': 'Proveedor no encontrado'}), 404
        
        # Obtener productos que suministra este proveedor
        productos = conn.execute('''
            SELECT p.id, p.descripcion, p.codigo
            FROM productos p
            WHERE p.proveedor_id = ?
            ORDER BY p.descripcion
        ''', (id,)).fetchall()
        
        # Convertir a diccionario
        resultado = dict(proveedor)
        resultado['productos'] = [dict(p) for p in productos]
        resultado['productos_count'] = len(productos)
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/exportar/proveedores')
def exportar_proveedores():
    """Exportar proveedores filtrados a CSV"""
    conn = get_db_connection()
    
    try:
        # Obtener filtros (mismos que en la vista)
        search = request.args.get('search', '').strip()
        
        # Query para obtener proveedores con información de productos
        query = '''
            SELECT p.id, p.nombre, p.contacto, p.telefono, p.email, 
                   p.pagina_web, p.direccion, p.notas, p.fecha_creacion,
                   COUNT(DISTINCT pr.id) as productos_count
            FROM proveedores p
            LEFT JOIN productos pr ON p.id = pr.proveedor_id
            WHERE 1=1
        '''
        
        params = []
        
        if search:
            query += ' AND (p.nombre LIKE ? OR p.contacto LIKE ? OR p.email LIKE ?)'
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])
        
        query += ' GROUP BY p.id ORDER BY p.nombre'
        
        proveedores = conn.execute(query, params).fetchall()
        
        # Crear CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        writer.writerow([
            'ID', 'Nombre', 'Contacto', 'Teléfono', 'Email', 
            'Página Web', 'Dirección', 'Notas', 'Productos', 'Fecha Creación'
        ])
        
        # Datos
        for proveedor in proveedores:
            writer.writerow([
                proveedor['id'],
                proveedor['nombre'],
                proveedor['contacto'] or '',
                proveedor['telefono'] or '',
                proveedor['email'] or '',
                proveedor['pagina_web'] or '',
                proveedor['direccion'] or '',
                proveedor['notas'] or '',
                proveedor['productos_count'],
                proveedor['fecha_creacion'][:10] if proveedor['fecha_creacion'] else ''
            ])
        
        # Preparar respuesta
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'proveedores_{timestamp}.csv'
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
        
    except Exception as e:
        flash(f'Error al exportar proveedores: {str(e)}', 'error')
        return redirect(url_for('proveedores'))
    finally:
        conn.close()

@app.route('/maquina/nueva')
def nueva_maquina():
    """Formulario para nueva máquina"""
    return render_template('maquina_form.html')

@app.route('/maquina/editar/<int:id>')
def editar_maquina(id):
    """Formulario para editar máquina"""
    conn = get_db_connection()
    
    maquina = conn.execute('SELECT * FROM maquinas WHERE id = ?', (id,)).fetchone()
    
    if not maquina:
        flash('Máquina no encontrada', 'error')
        return redirect(url_for('maquinas'))
    
    # Obtener productos que usan esta máquina
    productos = conn.execute('''
        SELECT p.id, p.descripcion, p.codigo
        FROM productos p
        JOIN producto_maquinas pm ON p.id = pm.producto_id
        WHERE pm.maquina_id = ?
        ORDER BY p.descripcion
    ''', (id,)).fetchall()
    
    conn.close()
    return render_template('maquina_form.html', maquina=maquina, productos=productos)

@app.route('/maquina/guardar', methods=['POST'])
def guardar_maquina():
    """Guardar máquina nueva o editada"""
    conn = get_db_connection()
    
    try:
        nombre = request.form['nombre'].strip()
        descripcion = request.form.get('descripcion', '').strip()
        maquina_id = request.form.get('maquina_id')
        
        if not nombre:
            flash('El nombre de la máquina es requerido', 'error')
            return redirect(url_for('maquinas'))
        
        # Verificar que el nombre no esté en uso por otra máquina
        existing = conn.execute('SELECT id FROM maquinas WHERE nombre = ? AND id != ?', 
                               (nombre, maquina_id or 0)).fetchone()
        
        if existing:
            flash(f'El nombre "{nombre}" ya está en uso por otra máquina', 'error')
            return redirect(url_for('maquinas'))
        
        if maquina_id:  # Editar máquina existente
            if descripcion:
                conn.execute('UPDATE maquinas SET nombre=?, descripcion=? WHERE id=?', 
                           (nombre, descripcion, maquina_id))
            else:
                conn.execute('UPDATE maquinas SET nombre=? WHERE id=?', (nombre, maquina_id))
            flash('Máquina actualizada exitosamente', 'success')
            
            # Log de administrador si está logueado
            if is_admin_logged_in():
                log_admin_operation(
                    operation_type='MACHINE_EDIT',
                    description=f'Máquina editada: {nombre}',
                    conn=conn
                )
        else:  # Crear nueva máquina
            if descripcion:
                cursor = conn.execute('INSERT INTO maquinas (nombre, descripcion) VALUES (?, ?)', 
                                    (nombre, descripcion))
            else:
                cursor = conn.execute('INSERT INTO maquinas (nombre) VALUES (?)', (nombre,))
            nueva_maquina_id = cursor.lastrowid
            flash('Máquina creada exitosamente', 'success')
            
            # Log de administrador si está logueado
            if is_admin_logged_in():
                log_admin_operation(
                    operation_type='MACHINE_CREATE',
                    description=f'Nueva máquina creada: {nombre}',
                    conn=conn
                )
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al guardar máquina: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('maquinas'))

@app.route('/maquina/eliminar/<int:id>', methods=['POST'])
def eliminar_maquina(id):
    """Eliminar máquina (solo si no tiene productos)"""
    conn = get_db_connection()
    
    try:
        # Verificar que no tenga productos
        productos = conn.execute('SELECT COUNT(*) as count FROM producto_maquinas WHERE maquina_id = ?', (id,)).fetchone()
        
        if productos['count'] > 0:
            flash('No se puede eliminar una máquina que tiene productos asignados', 'error')
        else:
            maquina = conn.execute('SELECT nombre FROM maquinas WHERE id = ?', (id,)).fetchone()
            
            if maquina:
                conn.execute('DELETE FROM maquinas WHERE id = ?', (id,))
                conn.commit()
                
                flash(f'Máquina "{maquina["nombre"]}" eliminada exitosamente', 'success')
                
                # Log de administrador si está logueado
                if is_admin_logged_in():
                    log_admin_operation(
                        operation_type='MACHINE_DELETE',
                        description=f'Máquina eliminada: {maquina["nombre"]}',
                        conn=conn
                    )
            else:
                flash('Máquina no encontrada', 'error')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al eliminar máquina: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('maquinas'))

@app.route('/categoria/nueva')
def nueva_categoria():
    """Formulario para nueva categoría"""
    return render_template('categoria_form.html')

@app.route('/categoria/editar/<int:id>')
def editar_categoria(id):
    """Formulario para editar categoría"""
    conn = get_db_connection()
    
    categoria = conn.execute('SELECT * FROM categorias WHERE id = ?', (id,)).fetchone()
    
    if not categoria:
        flash('Categoría no encontrada', 'error')
        return redirect(url_for('categorias'))
    
    # Obtener subcategorías de esta categoría
    subcategorias = conn.execute('''
        SELECT sc.*, COUNT(DISTINCT p.id) as productos_count
        FROM subcategorias sc
        LEFT JOIN productos p ON sc.id = p.subcategoria_id
        WHERE sc.categoria_id = ?
        GROUP BY sc.id
        ORDER BY sc.nombre
    ''', (id,)).fetchall()
    
    conn.close()
    return render_template('categoria_form.html', categoria=categoria, subcategorias=subcategorias)

@app.route('/categoria/guardar', methods=['POST'])
def guardar_categoria():
    """Guardar categoría nueva o editada"""
    conn = get_db_connection()
    
    try:
        nombre = request.form['nombre'].strip()
        categoria_id = request.form.get('categoria_id')
        
        if not nombre:
            flash('El nombre de la categoría es requerido', 'error')
            return redirect(url_for('categorias'))
        
        # Verificar que el nombre no esté en uso por otra categoría
        existing = conn.execute('SELECT id FROM categorias WHERE nombre = ? AND id != ?', 
                               (nombre, categoria_id or 0)).fetchone()
        
        if existing:
            flash(f'El nombre "{nombre}" ya está en uso por otra categoría', 'error')
            return redirect(url_for('categorias'))
        
        if categoria_id:  # Editar categoría existente
            conn.execute('UPDATE categorias SET nombre=? WHERE id=?', (nombre, categoria_id))
            flash('Categoría actualizada exitosamente', 'success')
            
            # Log de administrador si está logueado
            if is_admin_logged_in():
                log_admin_operation(
                    operation_type='CATEGORY_EDIT',
                    description=f'Categoría editada: {nombre}',
                    conn=conn
                )
        else:  # Crear nueva categoría
            cursor = conn.execute('INSERT INTO categorias (nombre) VALUES (?)', (nombre,))
            nueva_categoria_id = cursor.lastrowid
            flash('Categoría creada exitosamente', 'success')
            
            # Log de administrador si está logueado
            if is_admin_logged_in():
                log_admin_operation(
                    operation_type='CATEGORY_CREATE',
                    description=f'Nueva categoría creada: {nombre}',
                    conn=conn
                )
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al guardar categoría: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('categorias'))

@app.route('/categoria/eliminar/<int:id>', methods=['POST'])
def eliminar_categoria(id):
    """Eliminar categoría (solo si no tiene productos o subcategorías)"""
    conn = get_db_connection()
    
    try:
        # Verificar que no tenga productos
        productos = conn.execute('SELECT COUNT(*) as count FROM productos WHERE categoria_id = ?', (id,)).fetchone()
        
        # Verificar que no tenga subcategorías
        subcategorias = conn.execute('SELECT COUNT(*) as count FROM subcategorias WHERE categoria_id = ?', (id,)).fetchone()
        
        if productos['count'] > 0:
            flash('No se puede eliminar una categoría que tiene productos asignados', 'error')
        elif subcategorias['count'] > 0:
            flash('No se puede eliminar una categoría que tiene subcategorías', 'error')
        else:
            categoria = conn.execute('SELECT nombre FROM categorias WHERE id = ?', (id,)).fetchone()
            
            if categoria:
                conn.execute('DELETE FROM categorias WHERE id = ?', (id,))
                conn.commit()
                
                flash(f'Categoría "{categoria["nombre"]}" eliminada exitosamente', 'success')
                
                # Log de administrador si está logueado
                if is_admin_logged_in():
                    log_admin_operation(
                        operation_type='CATEGORY_DELETE',
                        description=f'Categoría eliminada: {categoria["nombre"]}',
                        conn=conn
                    )
            else:
                flash('Categoría no encontrada', 'error')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al eliminar categoría: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('categorias'))

@app.route('/subcategoria/nueva')
def nueva_subcategoria():
    """Formulario para nueva subcategoría"""
    conn = get_db_connection()
    categorias = conn.execute('SELECT * FROM categorias ORDER BY nombre').fetchall()
    conn.close()
    return render_template('subcategoria_form.html', categorias=categorias)

@app.route('/subcategoria/editar/<int:id>')
def editar_subcategoria(id):
    """Formulario para editar subcategoría"""
    conn = get_db_connection()
    
    subcategoria = conn.execute('''
        SELECT sc.*, c.nombre as categoria_nombre
        FROM subcategorias sc
        JOIN categorias c ON sc.categoria_id = c.id
        WHERE sc.id = ?
    ''', (id,)).fetchone()
    
    if not subcategoria:
        flash('Subcategoría no encontrada', 'error')
        return redirect(url_for('categorias'))
    
    categorias = conn.execute('SELECT * FROM categorias ORDER BY nombre').fetchall()
    
    conn.close()
    return render_template('subcategoria_form.html', subcategoria=subcategoria, categorias=categorias)

@app.route('/subcategoria/guardar', methods=['POST'])
def guardar_subcategoria():
    """Guardar subcategoría nueva o editada"""
    conn = get_db_connection()
    
    try:
        nombre = request.form['nombre'].strip()
        categoria_id = request.form['categoria_id']
        subcategoria_id = request.form.get('subcategoria_id')
        
        if not nombre:
            flash('El nombre de la subcategoría es requerido', 'error')
            return redirect(url_for('categorias'))
        
        if not categoria_id:
            flash('Debe seleccionar una categoría', 'error')
            return redirect(url_for('categorias'))
        
        # Verificar que el nombre no esté en uso en la misma categoría
        existing = conn.execute('''
            SELECT id FROM subcategorias 
            WHERE nombre = ? AND categoria_id = ? AND id != ?
        ''', (nombre, categoria_id, subcategoria_id or 0)).fetchone()
        
        if existing:
            flash(f'El nombre "{nombre}" ya está en uso en esta categoría', 'error')
            return redirect(url_for('categorias'))
        
        # Obtener nombre de categoría para logs
        categoria_info = conn.execute('SELECT nombre FROM categorias WHERE id = ?', (categoria_id,)).fetchone()
        categoria_nombre = categoria_info['nombre'] if categoria_info else 'Desconocida'
        
        if subcategoria_id:  # Editar subcategoría existente
            conn.execute('''
                UPDATE subcategorias SET nombre=?, categoria_id=? WHERE id=?
            ''', (nombre, categoria_id, subcategoria_id))
            flash('Subcategoría actualizada exitosamente', 'success')
            
            # Log de administrador si está logueado
            if is_admin_logged_in():
                log_admin_operation(
                    operation_type='SUBCATEGORY_EDIT',
                    description=f'Subcategoría editada: {nombre} (Categoría: {categoria_nombre})',
                    conn=conn
                )
        else:  # Crear nueva subcategoría
            cursor = conn.execute('''
                INSERT INTO subcategorias (nombre, categoria_id) VALUES (?, ?)
            ''', (nombre, categoria_id))
            nueva_subcategoria_id = cursor.lastrowid
            flash('Subcategoría creada exitosamente', 'success')
            
            # Log de administrador si está logueado
            if is_admin_logged_in():
                log_admin_operation(
                    operation_type='SUBCATEGORY_CREATE',
                    description=f'Nueva subcategoría creada: {nombre} (Categoría: {categoria_nombre})',
                    conn=conn
                )
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al guardar subcategoría: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('categorias'))

@app.route('/subcategoria/eliminar/<int:id>', methods=['POST'])
def eliminar_subcategoria(id):
    """Eliminar subcategoría (solo si no tiene productos)"""
    conn = get_db_connection()
    
    try:
        # Verificar que no tenga productos
        productos = conn.execute('SELECT COUNT(*) as count FROM productos WHERE subcategoria_id = ?', (id,)).fetchone()
        
        if productos['count'] > 0:
            flash('No se puede eliminar una subcategoría que tiene productos asignados', 'error')
        else:
            subcategoria = conn.execute('''
                SELECT sc.nombre, c.nombre as categoria_nombre
                FROM subcategorias sc
                JOIN categorias c ON sc.categoria_id = c.id
                WHERE sc.id = ?
            ''', (id,)).fetchone()
            
            if subcategoria:
                conn.execute('DELETE FROM subcategorias WHERE id = ?', (id,))
                conn.commit()
                
                flash(f'Subcategoría "{subcategoria["nombre"]}" eliminada exitosamente', 'success')
                
                # Log de administrador si está logueado
                if is_admin_logged_in():
                    log_admin_operation(
                        operation_type='SUBCATEGORY_DELETE',
                        description=f'Subcategoría eliminada: {subcategoria["nombre"]} (Categoría: {subcategoria["categoria_nombre"]})',
                        conn=conn
                    )
            else:
                flash('Subcategoría no encontrada', 'error')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al eliminar subcategoría: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('categorias'))

@app.route('/ubicacion/nueva')
def nueva_ubicacion():
    """Formulario para nueva ubicación"""
    return render_template('ubicacion_form.html')

@app.route('/ubicacion/editar/<int:id>')
def editar_ubicacion(id):
    """Formulario para editar ubicación"""
    conn = get_db_connection()
    
    ubicacion = conn.execute('SELECT * FROM ubicaciones WHERE id = ?', (id,)).fetchone()
    
    if not ubicacion:
        flash('Ubicación no encontrada', 'error')
        return redirect(url_for('ubicaciones'))
    
    # Obtener productos en esta ubicación
    productos = conn.execute('''
        SELECT p.id, p.descripcion, p.codigo, i.cantidad
        FROM inventario i
        JOIN productos p ON i.producto_id = p.id
        WHERE i.ubicacion_id = ?
        ORDER BY p.descripcion
    ''', (id,)).fetchall()
    
    conn.close()
    return render_template('ubicacion_form.html', ubicacion=ubicacion, productos=productos)

@app.route('/ubicacion/guardar', methods=['POST'])
def guardar_ubicacion():
    """Guardar ubicación nueva o editada"""
    conn = get_db_connection()
    
    try:
        codigo = request.form['codigo'].strip()
        nombre = request.form['nombre'].strip()
        ubicacion_id = request.form.get('ubicacion_id')
        
        if not codigo:
            flash('El código de ubicación es requerido', 'error')
            return redirect(url_for('ubicaciones'))
        
        # Verificar que el código no esté en uso por otra ubicación
        existing = conn.execute('SELECT id FROM ubicaciones WHERE codigo = ? AND id != ?', 
                               (codigo, ubicacion_id or 0)).fetchone()
        
        if existing:
            flash(f'El código "{codigo}" ya está en uso por otra ubicación', 'error')
            return redirect(url_for('ubicaciones'))
        
        if ubicacion_id:  # Editar ubicación existente
            conn.execute('''
                UPDATE ubicaciones 
                SET codigo=?, nombre=?
                WHERE id=?
            ''', (codigo, nombre, ubicacion_id))
            flash('Ubicación actualizada exitosamente', 'success')
            
            # Log de administrador si está logueado
            if is_admin_logged_in():
                log_admin_operation(
                    operation_type='LOCATION_EDIT',
                    description=f'Ubicación editada: {codigo} - {nombre}',
                    ubicacion_id=ubicacion_id,
                    conn=conn
                )
        else:  # Crear nueva ubicación
            cursor = conn.execute('''
                INSERT INTO ubicaciones (codigo, nombre)
                VALUES (?, ?)
            ''', (codigo, nombre))
            nueva_ubicacion_id = cursor.lastrowid
            flash('Ubicación creada exitosamente', 'success')
            
            # Log de administrador si está logueado
            if is_admin_logged_in():
                log_admin_operation(
                    operation_type='LOCATION_CREATE',
                    description=f'Nueva ubicación creada: {codigo} - {nombre}',
                    ubicacion_id=nueva_ubicacion_id,
                    conn=conn
                )
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al guardar ubicación: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('ubicaciones'))

@app.route('/ubicacion/eliminar/<int:id>', methods=['POST'])
def eliminar_ubicacion(id):
    """Eliminar ubicación (solo si no tiene stock)"""
    conn = get_db_connection()
    
    try:
        # Verificar que no tenga stock
        stock = conn.execute('SELECT COUNT(*) as count FROM inventario WHERE ubicacion_id = ?', (id,)).fetchone()
        
        if stock['count'] > 0:
            flash('No se puede eliminar una ubicación que tiene productos en stock', 'error')
        else:
            ubicacion = conn.execute('SELECT codigo, nombre FROM ubicaciones WHERE id = ?', (id,)).fetchone()
            
            if ubicacion:
                conn.execute('DELETE FROM ubicaciones WHERE id = ?', (id,))
                conn.commit()
                
                flash(f'Ubicación "{ubicacion["codigo"]}" eliminada exitosamente', 'success')
                
                # Log de administrador si está logueado
                if is_admin_logged_in():
                    log_admin_operation(
                        operation_type='LOCATION_DELETE',
                        description=f'Ubicación eliminada: {ubicacion["codigo"]} - {ubicacion["nombre"]}',
                        ubicacion_id=id,
                        conn=conn
                    )
            else:
                flash('Ubicación no encontrada', 'error')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al eliminar ubicación: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('ubicaciones'))

@app.route('/admin/backup/descargar')
@require_admin
def descargar_backup():
    """Descargar backup de la base de datos"""
    try:
        # Crear nombre del archivo con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'inventario_backup_{timestamp}.db'
        
        # Crear copia temporal de la base de datos
        temp_dir = tempfile.gettempdir()
        temp_backup_path = os.path.join(temp_dir, backup_filename)
        
        # Copiar la base de datos actual
        shutil.copy2(DATABASE, temp_backup_path)
        
        # Log de la operación
        log_admin_operation(
            operation_type='BACKUP_DOWNLOAD',
            description=f'Backup descargado: {backup_filename}'
        )
        
        # Enviar archivo y eliminar temporal después
        def remove_file(response):
            try:
                os.remove(temp_backup_path)
            except Exception:
                pass
            return response
        
        return send_file(
            temp_backup_path,
            as_attachment=True,
            download_name=backup_filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        flash(f'Error al crear backup: {str(e)}', 'error')
        logging.error(f"Error creating backup: {str(e)}")
        return redirect(url_for('inventario'))

@app.route('/admin/backup/restaurar', methods=['POST'])
@require_admin
def restaurar_backup():
    """Restaurar base de datos desde backup"""
    try:
        # Verificar que se subió un archivo
        if 'backup_file' not in request.files:
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('inventario'))
        
        file = request.files['backup_file']
        motivo = request.form.get('motivo', 'Sin motivo especificado')
        
        if file.filename == '':
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('inventario'))
        
        # Verificar extensión del archivo
        if not file.filename.lower().endswith('.db'):
            flash('El archivo debe tener extensión .db', 'error')
            return redirect(url_for('inventario'))
        
        # Crear backup de seguridad antes de restaurar
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_before_restore = f'inventario_before_restore_{timestamp}.db'
        shutil.copy2(DATABASE, backup_before_restore)
        
        # Guardar archivo temporal
        temp_dir = tempfile.gettempdir()
        temp_filename = secure_filename(file.filename)
        temp_path = os.path.join(temp_dir, temp_filename)
        file.save(temp_path)
        
        # Verificar que el archivo es una base de datos SQLite válida
        try:
            test_conn = sqlite3.connect(temp_path)
            # Verificar que tiene las tablas principales
            cursor = test_conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='productos'")
            if not cursor.fetchone():
                raise Exception("El archivo no parece ser un backup válido del sistema")
            test_conn.close()
        except Exception as e:
            os.remove(temp_path)
            flash(f'El archivo no es un backup válido: {str(e)}', 'error')
            return redirect(url_for('inventario'))
        
        # Cerrar todas las conexiones existentes (importante para evitar locks)
        # Esto se hace reemplazando el archivo directamente
        
        # Reemplazar la base de datos actual
        shutil.copy2(temp_path, DATABASE)
        
        # Limpiar archivo temporal
        os.remove(temp_path)
        
        # Log de la operación (usando nueva base de datos)
        log_admin_operation(
            operation_type='BACKUP_RESTORE',
            description=f'Base de datos restaurada desde {file.filename}. Motivo: {motivo}. Backup previo guardado como: {backup_before_restore}'
        )
        
        flash(f'Base de datos restaurada exitosamente desde {file.filename}. Se creó un backup de seguridad: {backup_before_restore}', 'success')
        
    except Exception as e:
        flash(f'Error al restaurar backup: {str(e)}', 'error')
        logging.error(f"Error restoring backup: {str(e)}")
    
    return redirect(url_for('inventario'))

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    flash('El archivo es demasiado grande. Tamaño máximo permitido: 100MB', 'error')
    return redirect(url_for('inventario'))

@app.route('/exportar/productos')
def exportar_productos():
    """Exportar productos filtrados a CSV"""
    conn = get_db_connection()
    
    # Obtener los mismos filtros que en la vista de productos
    search = request.args.get('search', '').strip()
    categoria_filter = request.args.get('categoria', '')
    subcategoria_filter = request.args.get('subcategoria', '')
    marca_filter = request.args.get('marca', '')
    maquina_filter = request.args.get('maquina', '')
    codigo_filter = request.args.get('codigo', '').strip()
    stock_filter = request.args.get('stock', '')
    
    # Misma query que en productos()
    query = '''
        SELECT p.id, p.descripcion, p.codigo, c.nombre as categoria, sc.nombre as subcategoria, 
               m.nombre as marca, mq.nombre as maquina, p.cantidad_requerida, p.notas,
               COALESCE(SUM(i.cantidad), 0) as stock_total
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        LEFT JOIN subcategorias sc ON p.subcategoria_id = sc.id
        LEFT JOIN marcas m ON p.marca_id = m.id
        LEFT JOIN maquinas mq ON p.maquina_id = mq.id
        LEFT JOIN inventario i ON p.id = i.producto_id
        WHERE 1=1
    '''
    
    params = []
    
    if search:
        query += ' AND (p.descripcion LIKE ? OR p.codigo LIKE ? OR p.notas LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param])
    
    if categoria_filter:
        query += ' AND c.nombre = ?'
        params.append(categoria_filter)
    
    if subcategoria_filter:
        query += ' AND sc.nombre = ?'
        params.append(subcategoria_filter)
    
    if marca_filter:
        query += ' AND m.nombre = ?'
        params.append(marca_filter)
    
    if maquina_filter:
        query += ' AND mq.nombre = ?'
        params.append(maquina_filter)
    
    if codigo_filter:
        query += ' AND p.codigo LIKE ?'
        params.append(f'%{codigo_filter}%')
    
    query += ' GROUP BY p.id'
    
    if stock_filter == 'sin_stock':
        query += ' HAVING stock_total = 0'
    elif stock_filter == 'con_stock':
        query += ' HAVING stock_total > 0'
    elif stock_filter == 'stock_bajo':
        query += ' HAVING stock_total > 0 AND stock_total < p.cantidad_requerida'
    
    query += ' ORDER BY p.descripcion'
    
    productos = conn.execute(query, params).fetchall()
    conn.close()
    
    # Crear CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Encabezados
    writer.writerow([
        'ID', 'Descripción', 'Código', 'Categoría', 'Subcategoría', 
        'Marca', 'Máquina', 'Stock Total', 'Cantidad Requerida', 'Estado Stock', 'Notas'
    ])
    
    # Datos
    for producto in productos:
        estado_stock = 'Sin Stock'
        if producto['stock_total'] >= producto['cantidad_requerida']:
            estado_stock = 'Stock OK'
        elif producto['stock_total'] > 0:
            estado_stock = 'Stock Bajo'
        
        writer.writerow([
            producto['id'],
            producto['descripcion'],
            producto['codigo'] or '',
            producto['categoria'] or '',
            producto['subcategoria'] or '',
            producto['marca'] or '',
            producto['maquina'] or '',
            producto['stock_total'],
            producto['cantidad_requerida'],
            estado_stock,
            producto['notas'] or ''
        ])
    
    # Preparar respuesta
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'productos_{timestamp}.csv'
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

@app.route('/exportar/inventario')
def exportar_inventario():
    """Exportar inventario filtrado a CSV"""
    conn = get_db_connection()
    
    # Obtener los mismos filtros que en la vista de inventario
    search = request.args.get('search', '').strip()
    categoria_filter = request.args.get('categoria', '')
    
    # Misma query que en inventario() pero con más detalles para export
    query = '''
        SELECT p.id, p.descripcion, p.codigo, c.nombre as categoria, sc.nombre as subcategoria, 
               m.nombre as marca, mq.nombre as maquina, p.cantidad_requerida, p.notas,
               COALESCE(SUM(i.cantidad), 0) as stock_total,
               GROUP_CONCAT(u.codigo || ':' || i.cantidad, ', ') as ubicaciones_detalle
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        LEFT JOIN subcategorias sc ON p.subcategoria_id = sc.id
        LEFT JOIN marcas m ON p.marca_id = m.id
        LEFT JOIN maquinas mq ON p.maquina_id = mq.id
        LEFT JOIN inventario i ON p.id = i.producto_id
        LEFT JOIN ubicaciones u ON i.ubicacion_id = u.id
        WHERE 1=1
    '''
    
    params = []
    
    if search:
        query += ' AND (p.descripcion LIKE ? OR p.codigo LIKE ? OR c.nombre LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param])
    
    if categoria_filter:
        query += ' AND c.nombre = ?'
        params.append(categoria_filter)
    
    query += ' GROUP BY p.id HAVING stock_total > 0 ORDER BY p.descripcion'
    
    productos = conn.execute(query, params).fetchall()
    conn.close()
    
    # Crear CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Encabezados
    writer.writerow([
        'ID', 'Descripción', 'Código', 'Categoría', 'Subcategoría', 
        'Marca', 'Máquina', 'Stock Total', 'Cantidad Requerida', 'Estado Stock', 
        'Ubicaciones (Código:Cantidad)', 'Notas'
    ])
    
    # Datos
    for producto in productos:
        estado_stock = 'Sin Stock'
        if producto['stock_total'] >= producto['cantidad_requerida']:
            estado_stock = 'Stock OK'
        elif producto['stock_total'] > 0:
            estado_stock = 'Stock Bajo'
        
        writer.writerow([
            producto['id'],
            producto['descripcion'],
            producto['codigo'] or '',
            producto['categoria'] or '',
            producto['subcategoria'] or '',
            producto['marca'] or '',
            producto['maquina'] or '',
            producto['stock_total'],
            producto['cantidad_requerida'],
            estado_stock,
            producto['ubicaciones_detalle'] or '',
            producto['notas'] or ''
        ])
    
    # Preparar respuesta
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'inventario_{timestamp}.csv'
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

@app.route('/api/ubicacion/<int:id>')
def api_ubicacion(id):
    """API para obtener detalles de una ubicación"""
    conn = get_db_connection()
    
    # Obtener información de la ubicación
    ubicacion = conn.execute('''
        SELECT u.*, COUNT(DISTINCT i.producto_id) as productos_count,
               COALESCE(SUM(i.cantidad), 0) as stock_total
        FROM ubicaciones u
        LEFT JOIN inventario i ON u.id = i.ubicacion_id
        WHERE u.id = ?
        GROUP BY u.id
    ''', (id,)).fetchone()
    
    if not ubicacion:
        conn.close()
        return jsonify({'error': 'Ubicación no encontrada'}), 404
    
    # Obtener productos en esta ubicación
    productos = conn.execute('''
        SELECT p.id, p.descripcion, p.codigo, i.cantidad
        FROM inventario i
        JOIN productos p ON i.producto_id = p.id
        WHERE i.ubicacion_id = ?
        ORDER BY p.descripcion
    ''', (id,)).fetchall()
    
    conn.close()
    
    # Preparar respuesta
    resultado = dict(ubicacion)
    resultado['productos'] = [dict(prod) for prod in productos]
    resultado['fecha_creacion'] = ubicacion['fecha_creacion'] if ubicacion['fecha_creacion'] else None
    
    return jsonify(resultado)

@app.route('/exportar/ubicaciones')
def exportar_ubicaciones():
    """Exportar ubicaciones filtradas a CSV"""
    conn = get_db_connection()
    
    # Obtener los mismos filtros que en la vista de ubicaciones
    search = request.args.get('search', '').strip()
    
    # Misma query que en ubicaciones()
    query = '''
        SELECT u.id, u.codigo, u.nombre, u.fecha_creacion,
               COUNT(DISTINCT i.producto_id) as productos_count,
               COALESCE(SUM(i.cantidad), 0) as stock_total
        FROM ubicaciones u
        LEFT JOIN inventario i ON u.id = i.ubicacion_id
        WHERE 1=1
    '''
    
    params = []
    
    if search:
        query += ' AND (u.codigo LIKE ? OR u.nombre LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param])
    
    query += ' GROUP BY u.id ORDER BY u.codigo'
    
    ubicaciones = conn.execute(query, params).fetchall()
    conn.close()
    
    # Crear CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Encabezados
    writer.writerow([
        'ID', 'Código', 'Nombre', 'Productos', 'Stock Total', 'Fecha Creación'
    ])
    
    # Datos
    for ubicacion in ubicaciones:
        writer.writerow([
            ubicacion['id'],
            ubicacion['codigo'],
            ubicacion['nombre'] or '',
            ubicacion['productos_count'],
            ubicacion['stock_total'],
            ubicacion['fecha_creacion'] or ''
        ])
    
    # Preparar respuesta
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'ubicaciones_{timestamp}.csv'
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

# Servir imágenes estáticas
@app.route('/imagenes/<filename>')
def imagenes(filename):
    """Servir imágenes de productos"""
    from flask import send_from_directory
    return send_from_directory('imagenes', filename)

@app.route('/health')
def health_check():
    """Health check endpoint for Docker"""
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}, 200

@app.route('/exportar/maquinas')
def exportar_maquinas():
    """Exportar máquinas a CSV"""
    conn = get_db_connection()
    
    # Obtener los mismos filtros que en la vista
    search = request.args.get('search', '').strip()
    
    # Query para máquinas
    query = '''
        SELECT m.id, m.nombre, m.descripcion, m.fecha_creacion,
               COUNT(DISTINCT pm.producto_id) as productos_count
        FROM maquinas m
        LEFT JOIN producto_maquinas pm ON m.id = pm.maquina_id
        WHERE 1=1
    '''
    
    params = []
    
    if search:
        query += ' AND m.nombre LIKE ?'
        params.append(f'%{search}%')
    
    query += ' GROUP BY m.id ORDER BY m.nombre'
    
    maquinas = conn.execute(query, params).fetchall()
    
    # Obtener detalles de productos por máquina
    maquinas_con_productos = []
    for maquina in maquinas:
        productos = conn.execute('''
            SELECT p.descripcion, p.codigo
            FROM productos p
            JOIN producto_maquinas pm ON p.id = pm.producto_id
            WHERE pm.maquina_id = ?
            ORDER BY p.descripcion
        ''', (maquina['id'],)).fetchall()
        
        productos_str = '; '.join([f"{p['descripcion']} ({p['codigo']})" if p['codigo'] else p['descripcion'] for p in productos])
        
        maquinas_con_productos.append({
            'id': maquina['id'],
            'nombre': maquina['nombre'],
            'descripcion': maquina['descripcion'] or '',
            'productos_count': maquina['productos_count'],
            'productos_detalle': productos_str,
            'fecha_creacion': maquina['fecha_creacion'] or ''
        })
    
    conn.close()
    
    # Crear CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Encabezados
    writer.writerow(['ID', 'Nombre', 'Descripción', 'Productos (Cantidad)', 'Productos (Detalle)', 'Fecha Creación'])
    
    # Datos
    for maquina in maquinas_con_productos:
        writer.writerow([
            maquina['id'],
            maquina['nombre'],
            maquina['descripcion'],
            maquina['productos_count'],
            maquina['productos_detalle'],
            maquina['fecha_creacion']
        ])
    
    # Preparar respuesta
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'maquinas_{timestamp}.csv'
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)