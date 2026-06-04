from flask import Flask, render_template, request, jsonify
from datetime import datetime

# Crear la aplicación Flask
app = Flask(__name__)

# Diccionario para almacenar la última medición recibida
# Datos de ejemplo para mostrar algo antes de que llegue el ESP32
ultima_medicion = {
    'co': 150,
    'pm': 35,
    'mq135': 200,
    'lat': -12.0464,   # Lima - Centro
    'lng': -77.0428,
    'timestamp': None
}

# Variable para almacenar todo el historial (opcional, para debug)
historial = []


# ============================================
# RUTAS DEL FRONTEND (Páginas web)
# ============================================

@app.route('/')
def index():
    """Sirve la página principal con el mapa"""
    return render_template('index.html')


# ============================================
# API PARA EL ESP32 (Recepción de datos)
# ============================================

@app.route('/api/datos', methods=['POST'])
def recibir_datos():
    """
    Endpoint que el ESP32 llamará para enviar los datos.
    Espera un JSON como:
    {
        "co": 450,
        "pm": 120,
        "mq135": 380,
        "lat": -12.1234,
        "lng": -77.5678
    }
    """
    global ultima_medicion, historial
    
    try:
        # Obtener los datos JSON que envió el ESP32
        datos = request.get_json()
        
        # Validar que llegaron todos los campos necesarios
        required_fields = ['co', 'pm', 'mq135', 'lat', 'lng']
        for field in required_fields:
            if field not in datos:
                return jsonify({'error': f'Falta el campo {field}'}), 400
        
        # Crear el registro completo con timestamp
        registro = {
            'co': datos['co'],
            'pm': datos['pm'],
            'mq135': datos['mq135'],
            'lat': datos['lat'],
            'lng': datos['lng'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Guardar como última medición
        ultima_medicion = registro
        
        # Opcional: guardar en historial (máximo 100 registros)
        historial.append(registro)
        if len(historial) > 100:
            historial.pop(0)
        
        # Imprimir en consola para debug (Render lo muestra en logs)
        print(f"✅ Datos recibidos - CO: {datos['co']}, Lat: {datos['lat']}, Lng: {datos['lng']}")
        
        return jsonify({'status': 'ok', 'message': 'Datos recibidos correctamente'}), 200
        
    except Exception as e:
        print(f"❌ Error al procesar datos: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================
# API PARA EL FRONTEND (Obtener datos para el mapa)
# ============================================

@app.route('/api/ultima-medicion')
def obtener_ultima_medicion():
    """Devuelve la última medición en formato JSON para el mapa"""
    return jsonify(ultima_medicion)


@app.route('/api/historial')
def obtener_historial():
    """Devuelve todo el historial (útil para pruebas)"""
    return jsonify(historial)


# ============================================
# PUNTO DE ENTRADA
# ============================================

if __name__ == '__main__':
    # Para desarrollo local
    app.run(debug=True, host='0.0.0.0', port=5000)