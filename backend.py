from flask import Flask, render_template, request, jsonify, session
from datetime import datetime
import hashlib
from functools import wraps

app = Flask(__name__)
app.secret_key = "WALLY_SECRET_KEY_2026"

# Usuario admin fijo
USUARIO_ADMIN = "teamwally"
PASSWORD_HASH = hashlib.sha256("mamani159".encode()).hexdigest()

def admin_requerido(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session or session.get('rol') != 'admin':
            return jsonify({"error": "Acceso denegado"}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

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
    else:
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

@app.route('/api/dispositivos')
def obtener_dispositivos():
    # Datos de prueba
    dispositivos = [
        {'id': 'WALLY-1', 'nombre': 'WALLY-1', 'color': '#4CAF50', 'lat': -12.0464, 'lng': -77.0428, 'co': 85, 'pm': 32, 'mq135': 180, 'timestamp': datetime.now().isoformat()},
        {'id': 'WALLY-2', 'nombre': 'WALLY-2', 'color': '#2196F3', 'lat': -12.1210, 'lng': -77.0265, 'co': 145, 'pm': 68, 'mq135': 320, 'timestamp': datetime.now().isoformat()},
        {'id': 'WALLY-DEMO', 'nombre': 'WALLY-DEMO', 'color': '#FF9800', 'lat': -12.0960, 'lng': -77.0345, 'co': 220, 'pm': 95, 'mq135': 450, 'timestamp': datetime.now().isoformat()}
    ]
    return jsonify(dispositivos)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)