"""
database.py - Manejo de la base de datos SQLite para WALLY
"""

import sqlite3
import hashlib
from datetime import datetime

# Nombre del archivo de la base de datos
DB_NAME = 'wally.db'

# ============================================
# CONEXIÓN A LA BASE DE DATOS
# ============================================

def get_connection():
    """Crea y devuelve una conexión a la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================
# CREACIÓN DE TABLAS
# ============================================

def crear_tablas():
    """Crea todas las tablas necesarias si no existen"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla 1: Dispositivos (robots)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dispositivos (
            id TEXT PRIMARY KEY,
            nombre TEXT,
            color TEXT DEFAULT '#4CAF50',
            correo_alerta TEXT,
            acceso_publico BOOLEAN DEFAULT 1,
            activo BOOLEAN DEFAULT 1,
            ultima_conexion TIMESTAMP,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla 2: Mediciones (historial de datos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mediciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dispositivo_id TEXT,
            co INTEGER,
            pm INTEGER,
            mq135 INTEGER,
            lat REAL,
            lng REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dispositivo_id) REFERENCES dispositivos(id)
        )
    ''')
    
    # Tabla 3: Usuarios (administradores)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            rol TEXT DEFAULT 'user'
        )
    ''')
    
    # Tabla 4: Logs (registro de acciones)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            accion TEXT,
            ip TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Tablas creadas correctamente")

# ============================================
# FUNCIONES PARA DISPOSITIVOS
# ============================================

def registrar_o_actualizar_dispositivo(device_id, nombre=None, lat=None, lng=None):
    """Registra un nuevo dispositivo o actualiza su última conexión"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM dispositivos WHERE id = ?", (device_id,))
    existe = cursor.fetchone()
    
    if existe:
        cursor.execute('''
            UPDATE dispositivos 
            SET ultima_conexion = CURRENT_TIMESTAMP, activo = 1
            WHERE id = ?
        ''', (device_id,))
    else:
        nombre_usar = nombre if nombre else f"Robot-{device_id[-4:]}"
        cursor.execute('''
            INSERT INTO dispositivos (id, nombre, ultima_conexion, fecha_registro)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (device_id, nombre_usar))
    
    conn.commit()
    conn.close()
    return True

def guardar_medicion(device_id, co, pm, mq135, lat, lng):
    """Guarda una medición en el historial"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO mediciones (dispositivo_id, co, pm, mq135, lat, lng)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (device_id, co, pm, mq135, lat, lng))
    
    cursor.execute('''
        UPDATE dispositivos 
        SET ultima_conexion = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (device_id,))
    
    conn.commit()
    conn.close()
    return cursor.lastrowid

def obtener_ultima_medicion(device_id):
    """Obtiene la última medición de un dispositivo"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM mediciones 
        WHERE dispositivo_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
    ''', (device_id,))
    
    resultado = cursor.fetchone()
    conn.close()
    
    if resultado:
        return dict(resultado)
    return None

def obtener_todos_los_dispositivos():
    """Obtiene la lista de todos los dispositivos activos"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, nombre, color, correo_alerta, acceso_publico, activo, 
               ultima_conexion, fecha_registro
        FROM dispositivos 
        WHERE activo = 1
        ORDER BY ultima_conexion DESC
    ''')
    
    resultados = cursor.fetchall()
    conn.close()
    return [dict(row) for row in resultados]

def actualizar_nombre_robot(device_id, nuevo_nombre):
    """Cambia el nombre de un robot"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE dispositivos 
        SET nombre = ? 
        WHERE id = ?
    ''', (nuevo_nombre, device_id))
    
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

def actualizar_color_robot(device_id, nuevo_color):
    """Cambia el color de un robot"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE dispositivos 
        SET color = ? 
        WHERE id = ?
    ''', (nuevo_color, device_id))
    
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

def obtener_historial(device_id, limite=100):
    """Obtiene el historial de mediciones de un dispositivo"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM mediciones 
        WHERE dispositivo_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (device_id, limite))
    
    resultados = cursor.fetchall()
    conn.close()
    return [dict(row) for row in resultados]

# ============================================
# FUNCIONES PARA USUARIOS
# ============================================

def crear_usuario(username, password, rol='user'):
    """Crea un nuevo usuario administrador"""
    conn = get_connection()
    cursor = conn.cursor()
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        cursor.execute('''
            INSERT INTO usuarios (username, password_hash, rol)
            VALUES (?, ?, ?)
        ''', (username, password_hash, rol))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def verificar_usuario(username, password):
    """Verifica credenciales de usuario"""
    conn = get_connection()
    cursor = conn.cursor()
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    cursor.execute('''
        SELECT * FROM usuarios 
        WHERE username = ? AND password_hash = ?
    ''', (username, password_hash))
    
    resultado = cursor.fetchone()
    conn.close()
    
    return dict(resultado) if resultado else None

# ============================================
# FUNCIONES PARA LOGS
# ============================================

def registrar_log(usuario, accion, ip=None):
    """Registra una acción importante para auditoría"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO logs (usuario, accion, ip)
        VALUES (?, ?, ?)
    ''', (usuario, accion, ip))
    
    conn.commit()
    conn.close()

# ============================================
# INICIALIZACIÓN
# ============================================

def inicializar_base_datos():
    """Crea tablas y usuario admin por defecto"""
    crear_tablas()
    
    # Crear usuario admin con las nuevas credenciales
    admin = verificar_usuario('teamwally', 'mamani159')
    if not admin:
        crear_usuario('teamwally', 'mamani159', 'admin')
        print("✅ Usuario admin creado (teamwally/mamani159)")
    
    # Crear un dispositivo de ejemplo para pruebas
    registrar_o_actualizar_dispositivo('WALLY-DEMO', 'Robot Demostración')
    print("✅ Dispositivo de demostración creado")

if __name__ == '__main__':
    inicializar_base_datos()
    print("🎉 Base de datos lista para usar!")