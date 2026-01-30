from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3
import os
from datetime import datetime
import csv

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

# Configuración de la base de datos
DATABASE = 'inventario.db'

def init_db():
    """Inicializar la base de datos con las tablas necesarias"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Tabla de categorías
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            descripcion TEXT
        )
    ''')
    
    # Tabla de subcategorías
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subcategorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria_id INTEGER,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id)
        )
    ''')
    
    # Tabla de marcas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS marcas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Tabla de máquinas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maquinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            descripcion TEXT
        )
    ''')
    
    # Tabla de ubicaciones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ubicaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            empresa TEXT DEFAULT 'PPG',
            area TEXT DEFAULT 'Oficinas',
            nivel TEXT DEFAULT 'Planta Alta',
            seccion TEXT DEFAULT 'Anaquel Refacciones Maq Cepillo'
        )
    ''')
    
    # Tabla principal de productos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            codigo TEXT UNIQUE,
            categoria_id INTEGER,
            subcategoria_id INTEGER,
            marca_id INTEGER,
            notas TEXT,
            imagen_ruta TEXT,
            cantidad_requerida INTEGER DEFAULT 1,
            maquina_id INTEGER,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id),
            FOREIGN KEY (subcategoria_id) REFERENCES subcategorias (id),
            FOREIGN KEY (marca_id) REFERENCES marcas (id),
            FOREIGN KEY (maquina_id) REFERENCES maquinas (id)
        )
    ''')
    
    # Tabla de inventario (stock por ubicación)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            ubicacion_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL DEFAULT 0,
            fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (producto_id) REFERENCES productos (id),
            FOREIGN KEY (ubicacion_id) REFERENCES ubicaciones (id),
            UNIQUE(producto_id, ubicacion_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Obtener conexión a la base de datos"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Página principal - Dashboard"""
    conn = get_db_connection()
    
    # Estadísticas generales
    stats = {}
    stats['total_productos'] = conn.execute('SELECT COUNT(*) FROM productos').fetchone()[0]
    stats['total_categorias'] = conn.execute('SELECT COUNT(*) FROM categorias').fetchone()[0]
    stats['total_ubicaciones'] = conn.execute('SELECT COUNT(*) FROM ubicaciones').fetchone()[0]
    stats['total_stock'] = conn.execute('SELECT COALESCE(SUM(cantidad), 0) FROM inventario').fetchone()[0]
    
    # Productos con stock bajo (menos de cantidad requerida)
    productos_bajo_stock = conn.execute('''
        SELECT p.descripcion, p.codigo, COALESCE(SUM(i.cantidad), 0) as stock_actual, 
               p.cantidad_requerida, m.nombre as maquina
        FROM productos p
        LEFT JOIN inventario i ON p.id = i.producto_id
        LEFT JOIN maquinas m ON p.maquina_id = m.id
        GROUP BY p.id
        HAVING stock_actual < p.cantidad_requerida
        ORDER BY (p.cantidad_requerida - stock_actual) DESC
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    return render_template('dashboard.html', stats=stats, productos_bajo_stock=productos_bajo_stock)

@app.route('/productos')
def productos():
    """Lista de productos"""
    conn = get_db_connection()
    
    # Obtener filtros
    categoria_filter = request.args.get('categoria', '')
    marca_filter = request.args.get('marca', '')
    search = request.args.get('search', '')
    
    # Construir query
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
    if categoria_filter:
        query += ' AND c.nombre = ?'
        params.append(categoria_filter)
    if marca_filter:
        query += ' AND m.nombre = ?'
        params.append(marca_filter)
    if search:
        query += ' AND (p.descripcion LIKE ? OR p.codigo LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    
    query += ' GROUP BY p.id ORDER BY p.descripcion'
    
    productos = conn.execute(query, params).fetchall()
    
    # Obtener listas para filtros
    categorias = conn.execute('SELECT DISTINCT nombre FROM categorias ORDER BY nombre').fetchall()
    marcas = conn.execute('SELECT DISTINCT nombre FROM marcas ORDER BY nombre').fetchall()
    
    conn.close()
    return render_template('productos.html', productos=productos, categorias=categorias, 
                         marcas=marcas, categoria_filter=categoria_filter, 
                         marca_filter=marca_filter, search=search)

@app.route('/producto/nuevo')
def nuevo_producto():
    """Formulario para nuevo producto"""
    conn = get_db_connection()
    
    categorias = conn.execute('SELECT * FROM categorias ORDER BY nombre').fetchall()
    marcas = conn.execute('SELECT * FROM marcas ORDER BY nombre').fetchall()
    maquinas = conn.execute('SELECT * FROM maquinas ORDER BY nombre').fetchall()
    
    conn.close()
    return render_template('producto_form.html', categorias=categorias, marcas=marcas, maquinas=maquinas)

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
        imagen_ruta = request.form['imagen_ruta']
        cantidad_requerida = int(request.form['cantidad_requerida']) if request.form['cantidad_requerida'] else 1
        maquina_id = request.form['maquina_id'] if request.form['maquina_id'] else None
        
        producto_id = request.form.get('producto_id')
        
        if producto_id:  # Editar
            conn.execute('''
                UPDATE productos 
                SET descripcion=?, codigo=?, categoria_id=?, subcategoria_id=?, marca_id=?, 
                    notas=?, imagen_ruta=?, cantidad_requerida=?, maquina_id=?, 
                    fecha_actualizacion=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (descripcion, codigo, categoria_id, subcategoria_id, marca_id, 
                  notas, imagen_ruta, cantidad_requerida, maquina_id, producto_id))
            flash('Producto actualizado exitosamente', 'success')
        else:  # Nuevo
            conn.execute('''
                INSERT INTO productos (descripcion, codigo, categoria_id, subcategoria_id, marca_id, 
                                     notas, imagen_ruta, cantidad_requerida, maquina_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (descripcion, codigo, categoria_id, subcategoria_id, marca_id, 
                  notas, imagen_ruta, cantidad_requerida, maquina_id))
            flash('Producto creado exitosamente', 'success')
        
        conn.commit()
        
    except Exception as e:
        flash(f'Error al guardar producto: {str(e)}', 'error')
    
    conn.close()
    return redirect(url_for('productos'))

@app.route('/inventario')
def inventario():
    """Vista del inventario por ubicaciones"""
    conn = get_db_connection()
    
    # Obtener inventario con detalles
    inventario_data = conn.execute('''
        SELECT i.*, p.descripcion, p.codigo, p.cantidad_requerida,
               u.codigo as ubicacion_codigo, u.nombre as ubicacion_nombre,
               c.nombre as categoria, m.nombre as marca
        FROM inventario i
        JOIN productos p ON i.producto_id = p.id
        JOIN ubicaciones u ON i.ubicacion_id = u.id
        LEFT JOIN categorias c ON p.categoria_id = c.id
        LEFT JOIN marcas m ON p.marca_id = m.id
        WHERE i.cantidad > 0
        ORDER BY u.codigo, p.descripcion
    ''').fetchall()
    
    # Agrupar por ubicación
    inventario_por_ubicacion = {}
    for item in inventario_data:
        ubicacion = item['ubicacion_codigo']
        if ubicacion not in inventario_por_ubicacion:
            inventario_por_ubicacion[ubicacion] = {
                'nombre': item['ubicacion_nombre'],
                'productos': []
            }
        inventario_por_ubicacion[ubicacion]['productos'].append(item)
    
    conn.close()
    return render_template('inventario.html', inventario_por_ubicacion=inventario_por_ubicacion)

@app.route('/ubicaciones')
def ubicaciones():
    """Gestión de ubicaciones"""
    conn = get_db_connection()
    ubicaciones = conn.execute('SELECT * FROM ubicaciones ORDER BY codigo').fetchall()
    conn.close()
    return render_template('ubicaciones.html', ubicaciones=ubicaciones)

@app.route('/configuracion')
def configuracion():
    """Página de configuración"""
    conn = get_db_connection()
    
    categorias = conn.execute('SELECT * FROM categorias ORDER BY nombre').fetchall()
    marcas = conn.execute('SELECT * FROM marcas ORDER BY nombre').fetchall()
    maquinas = conn.execute('SELECT * FROM maquinas ORDER BY nombre').fetchall()
    
    conn.close()
    return render_template('configuracion.html', categorias=categorias, marcas=marcas, maquinas=maquinas)

# Rutas adicionales
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

@app.route('/ubicacion/nueva')
def nueva_ubicacion():
    """Formulario para nueva ubicación"""
    return render_template('ubicacion_form.html')

@app.route('/ubicacion/guardar', methods=['POST'])
def guardar_ubicacion():
    """Guardar ubicación nueva o editada"""
    conn = get_db_connection()
    
    try:
        codigo = request.form['codigo']
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        empresa = request.form['empresa']
        area = request.form['area']
        nivel = request.form['nivel']
        seccion = request.form['seccion']
        
        ubicacion_id = request.form.get('ubicacion_id')
        
        if ubicacion_id:  # Editar
            conn.execute('''
                UPDATE ubicaciones 
                SET codigo=?, nombre=?, descripcion=?, empresa=?, area=?, nivel=?, seccion=?
                WHERE id=?
            ''', (codigo, nombre, descripcion, empresa, area, nivel, seccion, ubicacion_id))
            flash('Ubicación actualizada exitosamente', 'success')
        else:  # Nueva
            conn.execute('''
                INSERT INTO ubicaciones (codigo, nombre, descripcion, empresa, area, nivel, seccion)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (codigo, nombre, descripcion, empresa, area, nivel, seccion))
            flash('Ubicación creada exitosamente', 'success')
        
        conn.commit()
        
    except Exception as e:
        flash(f'Error al guardar ubicación: {str(e)}', 'error')
    
    conn.close()
    return redirect(url_for('ubicaciones'))

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
    """API para obtener detalles de un producto"""
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
    conn.close()
    
    if producto:
        return jsonify(dict(producto))
    else:
        return jsonify({'error': 'Producto no encontrado'}), 404

@app.route('/api/producto/<int:id>/stock')
def api_producto_stock(id):
    """API para obtener información de stock de un producto"""
    conn = get_db_connection()
    
    producto = conn.execute('SELECT * FROM productos WHERE id = ?', (id,)).fetchone()
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    stock = conn.execute('''
        SELECT i.*, u.codigo as ubicacion_codigo, u.nombre as ubicacion_nombre
        FROM inventario i
        JOIN ubicaciones u ON i.ubicacion_id = u.id
        WHERE i.producto_id = ?
    ''', (id,)).fetchall()
    
    ubicaciones = conn.execute('SELECT * FROM ubicaciones ORDER BY codigo').fetchall()
    
    conn.close()
    
    return jsonify({
        'producto': dict(producto),
        'stock': [dict(s) for s in stock],
        'ubicaciones': [dict(u) for u in ubicaciones]
    })

# Servir imágenes estáticas
@app.route('/imagenes/<filename>')
def imagenes(filename):
    """Servir imágenes de productos"""
    from flask import send_from_directory
    return send_from_directory('imagenes', filename)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)