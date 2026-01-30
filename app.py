from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import sqlite3
import os
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

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
    """Obtener conexión a la base de datos"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
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

def log_admin_operation(operation_type, description, producto_id=None, ubicacion_id=None, old_quantity=None, new_quantity=None):
    """Registrar operación de administrador en logs"""
    if not is_admin_logged_in():
        return
    
    conn = get_db_connection()
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    
    conn.execute('''
        INSERT INTO operation_logs (admin_user_id, operation_type, producto_id, ubicacion_id, 
                                  old_quantity, new_quantity, description, ip_address)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (session.get('admin_user_id'), operation_type, producto_id, ubicacion_id, 
          old_quantity, new_quantity, description, ip_address))
    conn.commit()
    conn.close()
    
    # Log también en archivo
    logging.info(f"ADMIN_OP: {session.get('admin_username')} - {operation_type} - {description}")

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
    
    query += ' GROUP BY p.id ORDER BY p.descripcion'
    
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
                             'codigo': codigo_filter
                         })

@app.route('/inventario')
def inventario():
    """Vista del inventario - lista simple de todos los productos"""
    conn = get_db_connection()
    
    # Obtener filtros
    search = request.args.get('search', '').strip()
    categoria_filter = request.args.get('categoria', '')
    
    # Query para obtener todos los productos con su stock total
    query = '''
        SELECT p.*, c.nombre as categoria, sc.nombre as subcategoria, 
               m.nombre as marca, mq.nombre as maquina,
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
    
    query += ' GROUP BY p.id ORDER BY p.descripcion'
    
    productos = conn.execute(query, params).fetchall()
    
    # Obtener listas para filtros
    categorias = conn.execute('SELECT DISTINCT nombre FROM categorias WHERE nombre IS NOT NULL ORDER BY nombre').fetchall()
    
    # Obtener todas las ubicaciones para el selector de agregar stock
    ubicaciones = conn.execute('SELECT DISTINCT codigo FROM ubicaciones ORDER BY codigo').fetchall()
    
    conn.close()
    
    return render_template('inventario.html', 
                         productos=productos,
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
    
    conn.close()
    return render_template('producto_form.html', categorias=categorias, marcas=marcas, maquinas=maquinas)

@app.route('/producto/editar/<int:id>')
def editar_producto(id):
    """Formulario para editar producto"""
    conn = get_db_connection()
    
    producto = conn.execute('''
        SELECT p.*, c.nombre as categoria, sc.nombre as subcategoria, 
               m.nombre as marca, mq.nombre as maquina
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        LEFT JOIN subcategorias sc ON p.subcategoria_id = sc.id
        LEFT JOIN marcas m ON p.marca_id = m.id
        LEFT JOIN maquinas mq ON p.maquina_id = mq.id
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
    
    conn.close()
    return render_template('producto_form.html', producto=producto, categorias=categorias, 
                         subcategorias=subcategorias, marcas=marcas, maquinas=maquinas)

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
        notas = request.form['notas']
        cantidad_requerida = int(request.form['cantidad_requerida']) if request.form['cantidad_requerida'] else 1
        maquina_id = request.form['maquina_id'] if request.form['maquina_id'] else None
        
        producto_id = request.form.get('producto_id')
        
        if producto_id:  # Editar producto existente
            conn.execute('''
                UPDATE productos 
                SET descripcion=?, codigo=?, categoria_id=?, subcategoria_id=?, marca_id=?, 
                    notas=?, cantidad_requerida=?, maquina_id=?, fecha_actualizacion=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (descripcion, codigo, categoria_id, subcategoria_id, marca_id, 
                  notas, cantidad_requerida, maquina_id, producto_id))
            flash('Producto actualizado exitosamente', 'success')
        else:  # Crear nuevo producto
            conn.execute('''
                INSERT INTO productos (descripcion, codigo, categoria_id, subcategoria_id, marca_id, 
                                     notas, cantidad_requerida, maquina_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (descripcion, codigo, categoria_id, subcategoria_id, marca_id, 
                  notas, cantidad_requerida, maquina_id))
            flash('Producto creado exitosamente', 'success')
        
        conn.commit()
        
    except Exception as e:
        flash(f'Error al guardar producto: {str(e)}', 'error')
    
    conn.close()
    return redirect(url_for('productos'))

@app.route('/admin/actualizar-stock-rapido', methods=['POST'])
@require_admin
def actualizar_stock_rapido():
    """Actualización rápida de stock por administrador"""
    try:
        data = request.get_json()
        cambios = data.get('cambios', {})
        
        if not cambios:
            return jsonify({'success': False, 'error': 'No hay cambios para aplicar'})
        
        conn = get_db_connection()
        cambios_aplicados = 0
        
        for key, cambio in cambios.items():
            producto_id = cambio['producto_id']
            ubicacion_id = cambio['ubicacion_id']
            stock_actual = cambio['stock_actual']
            nuevo_stock = cambio['nuevo_stock']
            
            # Obtener información del producto y ubicación para logs
            producto_info = conn.execute('SELECT descripcion FROM productos WHERE id = ?', (producto_id,)).fetchone()
            ubicacion_info = conn.execute('SELECT codigo FROM ubicaciones WHERE id = ?', (ubicacion_id,)).fetchone()
            
            if nuevo_stock == 0:
                # Eliminar registro si el stock es 0
                conn.execute('DELETE FROM inventario WHERE producto_id = ? AND ubicacion_id = ?', 
                           (producto_id, ubicacion_id))
                descripcion = f"Eliminado stock de {producto_info['descripcion']} en {ubicacion_info['codigo']}"
            else:
                # Actualizar o insertar stock
                existing = conn.execute('SELECT * FROM inventario WHERE producto_id = ? AND ubicacion_id = ?', 
                                      (producto_id, ubicacion_id)).fetchone()
                
                if existing:
                    conn.execute('''UPDATE inventario SET cantidad = ?, fecha_actualizacion = CURRENT_TIMESTAMP 
                                   WHERE producto_id = ? AND ubicacion_id = ?''', 
                               (nuevo_stock, producto_id, ubicacion_id))
                else:
                    conn.execute('INSERT INTO inventario (producto_id, ubicacion_id, cantidad) VALUES (?, ?, ?)', 
                               (producto_id, ubicacion_id, nuevo_stock))
                
                descripcion = f"Actualizado stock de {producto_info['descripcion']} en {ubicacion_info['codigo']}: {stock_actual} → {nuevo_stock}"
            
            # Registrar en logs
            log_admin_operation(
                operation_type='STOCK_EDIT',
                description=descripcion,
                producto_id=producto_id,
                ubicacion_id=ubicacion_id,
                old_quantity=stock_actual,
                new_quantity=nuevo_stock
            )
            
            cambios_aplicados += 1
        
        conn.commit()
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
            conn.execute('INSERT INTO ubicaciones (codigo, nombre) VALUES (?, ?)', 
                        (ubicacion_codigo, ubicacion_codigo))
            ubicacion_id = conn.lastrowid
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

@app.route('/api/producto/<int:id>')
def api_producto(id):
    """API para obtener detalles de un producto con ubicaciones de stock"""
    conn = get_db_connection()
    
    # Obtener información del producto
    producto = conn.execute('''
        SELECT p.*, c.nombre as categoria, sc.nombre as subcategoria, 
               m.nombre as marca, mq.nombre as maquina
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        LEFT JOIN subcategorias sc ON p.subcategoria_id = sc.id
        LEFT JOIN marcas m ON p.marca_id = m.id
        LEFT JOIN maquinas mq ON p.maquina_id = mq.id
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

# Servir imágenes estáticas
@app.route('/imagenes/<filename>')
def imagenes(filename):
    """Servir imágenes de productos"""
    from flask import send_from_directory
    return send_from_directory('imagenes', filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)