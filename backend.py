from flask import Flask, render_template, request, jsonify, session
from datetime import datetime
import hashlib
from functools import wraps
from database import (
    inicializar_base_datos,
    guardar_medicion,
    registrar_o_actualizar_dispositivo,
    obtener_todos_los_dispositivos,
    obtener_ultima_medicion,
    obtener_historial,
    actualizar_nombre_robot
)

app = Flask(__name__)
app.secret_key = "WALLY_SECRET_KEY_2026"

USUARIO_ADMIN = "teamwally"
PASSWORD_HASH = hashlib.sha256("mamani159".encode()).hexdigest()

# Inicializar BD al arrancar
inicializar_base_datos()

def admin_requerido(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session or session.get('rol') != 'admin':
            return jsonify({"error": "Acceso denegado"}), 403
        return f(*args, **kwargs)
    return decorated_function

# ── Páginas ──
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

# ── Auth ──
@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    password_check = hashlib.sha256(password.encode()).hexdigest()
    if username == USUARIO_ADMIN and password_check == PASSWORD_HASH:
        session['usuario'] = username
        session['rol'] = 'admin'
        return jsonify({"success": True, "rol": "admin"})
    return jsonify({"success": False, "error": "Usuario o contraseña incorrectos"}), 401

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.clear()
    return jsonify({"success": True})

@app.route('/admin/status')
def admin_status():
    if 'usuario' in session and session.get('rol') == 'admin':
        return jsonify({"is_admin": True, "usuario": session['usuario']})
    return jsonify({"is_admin": False})

# ── API: recibir datos del ESP32 ──
# co    = MQ-7  (monóxido de carbono)
# pm    = Sharp (polvo, ug/m3)
# mq135 = MQ-135 (otros gases)
@app.route('/api/datos', methods=['POST'])
def recibir_datos():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Sin datos"}), 400

    device_id = data.get('device_id', 'WALLY-1')
    co        = data.get('co', 0)
    pm        = data.get('pm', 0)
    mq135     = data.get('mq135', 0)
    lat       = data.get('lat', 0)
    lng       = data.get('lng', 0)

    registrar_o_actualizar_dispositivo(device_id)
    guardar_medicion(
        device_id,
        co    = co,
        pm    = pm,
        mq135 = mq135,
        lat   = lat,
        lng   = lng
    )
    return jsonify({"success": True}), 200

# ── API: obtener dispositivos con datos reales ──
@app.route('/api/dispositivos')
def obtener_dispositivos():
    dispositivos_raw = obtener_todos_los_dispositivos()
    resultado = []
    colores = ['#00e5a0', '#2196F3', '#FF9800', '#E91E63', '#9C27B0']

    for i, d in enumerate(dispositivos_raw):
        ultima = obtener_ultima_medicion(d['id'])
        resultado.append({
            'id':        d['id'],
            'nombre':    d['nombre'],
            'color':     d.get('color') or colores[i % len(colores)],
            'lat':       ultima['lat']       if ultima else 0,
            'lng':       ultima['lng']       if ultima else 0,
            'co':        ultima['co']        if ultima else 0,
            'pm':        ultima['pm']        if ultima else 0,
            'mq135':     ultima['mq135']     if ultima else 0,
            'timestamp': ultima['timestamp'] if ultima else datetime.now().isoformat()
        })

    return jsonify(resultado)

# ── API: historial de un dispositivo ──
@app.route('/api/historial/<device_id>')
def historial(device_id):
    datos = obtener_historial(device_id, limite=50)
    return jsonify(datos)

# ── API: renombrar robot (admin) ──
@app.route('/api/dispositivos/<device_id>/nombre', methods=['PUT'])
@admin_requerido
def cambiar_nombre(device_id):
    data = request.get_json()
    nuevo = data.get('nombre', '').strip()
    if not nuevo:
        return jsonify({"error": "Nombre vacío"}), 400
    actualizar_nombre_robot(device_id, nuevo)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
