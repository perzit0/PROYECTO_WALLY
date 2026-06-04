from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime
import hashlib
import secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = "WALLY_SECRET_KEY_2026_CAMBIA_ESTA_CLAVE"  # Cambia esto por una clave secreta

# ============================================
# BASE DE DATOS SIMULADA (en memoria)
# ============================================

# Usuarios: {usuario: {password_hash, rol}}
usuarios = {
    "admin": {
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "rol": "admin"
    },
    "invitado": {
        "password": hashlib.sha256("invitado".encode()).hexdigest(),
        "rol": "user"
    }
}

# Datos del robot
robot_data = {
    "nombre": "WALLY-1",
    "color": "#4CAF50"
}

# Última medición
ultima_medicion = {
    'co': 0,
    'pm': 0,
    'mq135': 0,
    'lat': -12.0464,
    'lng': -77.0428,
    'timestamp': None
}

historial = []

# ============================================
# DECORADOR PARA RUTAS PROTEGIDAS (solo admin)
# ============================================

def login_requerido(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_requerido(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        if session.get('rol') != 'admin':
            return jsonify({"error": "Acceso denegado. Se requieren permisos de administrador."}), 403
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# RUTAS DE AUTENTICACIÓN
# ============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya está logueado, redirigir al mapa
    if 'usuario' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        
        # Verificar credenciales
        if usuario in usuarios:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if usuarios[usuario]["password"] == password_hash:
                session['usuario'] = usuario
                session['rol'] = usuarios[usuario]["rol"]
                return redirect(url_for('index'))
        
        return render_template('login.html', error="Usuario o contraseña incorrectos")
    
    return render_template('login.html', error=None)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ============================================
# RUTAS DEL MAPA Y DATOS DEL ROBOT
# ============================================

@app.route('/')
def index():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', 
                          usuario=session['usuario'], 
                          rol=session['rol'],
                          robot_nombre=robot_data['nombre'],
                          robot_color=robot_data['color'])

@app.route('/api/datos-robot', methods=['GET'])
def obtener_datos_robot():
    """Devuelve los datos actuales del robot (nombre y color)"""
    return jsonify(robot_data)

@app.route('/api/datos-robot', methods=['POST'])
@admin_requerido
def actualizar_datos_robot():
    """Actualiza los datos del robot (solo admin)"""
    global robot_data
    try:
        datos = request.get_json()
        if 'nombre' in datos:
            robot_data['nombre'] = datos['nombre']
        if 'color' in datos:
            robot_data['color'] = datos['color']
        return jsonify({"status": "ok", "robot": robot_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# API PARA DATOS DE SENSORES
# ============================================

@app.route('/api/datos', methods=['POST'])
def recibir_datos():
    global ultima_medicion, historial
    try:
        datos = request.get_json()
        
        required_fields = ['co', 'pm', 'mq135', 'lat', 'lng']
        for field in required_fields:
            if field not in datos:
                return jsonify({'error': f'Falta el campo {field}'}), 400
        
        registro = {
            'co': datos['co'],
            'pm': datos['pm'],
            'mq135': datos['mq135'],
            'lat': datos['lat'],
            'lng': datos['lng'],
            'timestamp': datetime.now().isoformat()
        }
        
        ultima_medicion = registro
        historial.append(registro)
        if len(historial) > 100:
            historial.pop(0)
        
        print(f"✅ Datos recibidos - CO: {datos['co']}, Lat: {datos['lat']}")
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ultima-medicion')
def obtener_ultima_medicion():
    return jsonify(ultima_medicion)

@app.route('/api/historial')
def obtener_historial():
    return jsonify(historial)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)