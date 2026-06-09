"""
database.py - Manejo de la base de datos SQLite para WALLY
"""
import sqlite3
import hashlib
from datetime import datetime

DB_NAME = 'wally.db'

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def crear_tablas():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dispositivos (
            id TEXT PRIMARY KEY,
            nombre TEXT,
            color TEXT DEFAULT '#00e5a0',
            correo_alerta TEXT,
            acceso_publico BOOLEAN DEFAULT 1,
            activo BOOLEAN DEFAULT 1,
            ultima_conexion TIMESTAMP,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            rol TEXT DEFAULT 'user'
        )
    ''')

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

def registrar_o_actualizar_dispositivo(device_id, nombre=None, lat=None, lng=None):
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
        nombre_usar = nombre if nombre else f"WALLY-{device_id[-1:]}"
        cursor.execute('''
            INSERT INTO dispositivos (id, nombre, ultima_conexion, fecha_registro)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (device_id, nombre_usar))
    conn.commit()
    conn.close()
    return True

def guardar_medicion(device_id, co, pm, mq135, lat, lng):
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
    return dict(resultado) if resultado else None

def obtener_todos_los_dispositivos():
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE dispositivos SET nombre = ? WHERE id = ?', (nuevo_nombre, device_id))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

def actualizar_color_robot(device_id, nuevo_color):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE dispositivos SET color = ? WHERE id = ?', (nuevo_color, device_id))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

def obtener_historial(device_id, limite=100):
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

def crear_usuario(username, password, rol='user'):
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

def registrar_log(usuario, accion, ip=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO logs (usuario, accion, ip) VALUES (?, ?, ?)', (usuario, accion, ip))
    conn.commit()
    conn.close()

def inicializar_base_datos():
    crear_tablas()
    admin = verificar_usuario('teamwally', 'mamani159')
    if not admin:
        crear_usuario('teamwally', 'mamani159', 'admin')
        print("✅ Usuario admin creado")

if __name__ == '__main__':
    inicializar_base_datos()
    print("🎉 Base de datos lista!")
