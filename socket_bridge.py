"""
Microservicio Puente - Flask
Actúa como intermediario entre el Frontend (React/Next.js) y el Servidor Socket
Traduce peticiones HTTP en comandos de socket
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import socket
import logging
import os
import subprocess
import sys
import threading
import time
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bridge.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuración del servidor socket
# IMPORTANTE: Usar 'localhost' para conectar, NO '0.0.0.0'
SOCKET_HOST = 'localhost'  # Siempre localhost para el cliente del bridge
SOCKET_PORT = int(os.getenv('SERVER_PORT', 5000))


class SocketBridge:
    """Puente para comunicarse con el servidor socket"""

    @staticmethod
    def send_command(comando):
        """Envía un comando al servidor socket y retorna la respuesta"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((SOCKET_HOST, SOCKET_PORT))

            # Recibir mensaje de bienvenida
            _ = sock.recv(1024)

            # Enviar comando
            sock.send(comando.encode('utf-8'))

            # Recibir respuesta
            respuesta = sock.recv(4096).decode('utf-8')
            sock.close()

            return respuesta

        except Exception as e:
            logging.error(f"❌ Error comunicándose con socket: {e}")
            return f"ERROR|Error de conexión: {str(e)}"

    @staticmethod
    def parsear_respuesta(respuesta):
        """Convierte la respuesta del socket en JSON"""
        partes = respuesta.split('|')

        if partes[0] == 'OK':
            if len(partes) == 4:  # CONSULTA
                return {
                    'success': True,
                    'action': 'consulta',
                    'data': {
                        'nombres': partes[1],
                        'apellidos': partes[2],
                        'saldo': float(partes[3])
                    }
                }

            elif len(partes) == 3 and partes[1] in ['Depósito exitoso', 'Retiro exitoso']:
                accion = 'deposito' if partes[1] == 'Depósito exitoso' else 'retiro'
                return {
                    'success': True,
                    'action': accion,
                    'data': {
                        'mensaje': partes[1],
                        'nuevo_saldo': float(partes[2])
                    }
                }

            elif 'Cliente creado' in respuesta:
                return {
                    'success': True,
                    'action': 'crear',
                    'data': {
                        'mensaje': 'Cliente creado exitosamente',
                        'saldo_inicial': float(partes[-1])
                    }
                }

            elif 'Sin transacciones' in respuesta:
                return {
                    'success': True,
                    'action': 'historial',
                    'data': {'transacciones': []}
                }

            elif 'Clientes conectados' in respuesta:
                return {
                    'success': True,
                    'action': 'stats',
                    'data': {
                        'clientes_conectados': int(partes[1].split(': ')[-1]),
                        'total_transacciones': int(partes[2].split(': ')[-1]),
                        'ips_activas': int(partes[3].split(': ')[-1])
                    }
                }

            else:  # HISTORIAL
                transacciones = []
                for i in range(1, len(partes), 4):
                    if i + 3 < len(partes):
                        transacciones.append({
                            'tipo': partes[i],
                            'monto': float(partes[i+1]),
                            'saldo_final': float(partes[i+2]),
                            'fecha': partes[i+3]
                        })

                return {
                    'success': True,
                    'action': 'historial',
                    'data': {'transacciones': transacciones}
                }

        else:  # ERROR
            return {
                'success': False,
                'error': partes[1] if len(partes) > 1 else respuesta,
                'detalles': partes[2] if len(partes) > 2 else None
            }


# ==================== RUTAS API ====================

@app.route('/health', methods=['GET'])
def health():
    """Verifica que el servicio esté corriendo"""
    return jsonify({
        'status': 'ok',
        'service': 'bridge',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/consulta', methods=['POST'])
def consulta():
    """Consulta información de un cliente"""
    try:
        data = request.get_json()
        cedula = data.get('cedula')

        if not cedula:
            return jsonify({'success': False, 'error': 'Cédula requerida'}), 400

        comando = f"CONSULTA {cedula}"
        logging.info(f"📥 Comando: {comando}")

        respuesta = SocketBridge.send_command(comando)
        resultado = SocketBridge.parsear_respuesta(respuesta)

        logging.info(f"📤 Respuesta: {respuesta}")
        return jsonify(resultado)

    except Exception as e:
        logging.error(f"❌ Error en /api/consulta: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/deposito', methods=['POST'])
def deposito():
    """Realiza un depósito (aumentar saldo)"""
    try:
        data = request.get_json()
        cedula = data.get('cedula')
        monto = data.get('monto')

        if not cedula or monto is None:
            return jsonify({'success': False, 'error': 'Cédula y monto requeridos'}), 400

        comando = f"AUMENTAR {cedula} {monto}"
        logging.info(f"📥 Comando: {comando}")

        respuesta = SocketBridge.send_command(comando)
        resultado = SocketBridge.parsear_respuesta(respuesta)

        logging.info(f"📤 Respuesta: {respuesta}")
        return jsonify(resultado)

    except Exception as e:
        logging.error(f"❌ Error en /api/deposito: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/retiro', methods=['POST'])
def retiro():
    """Realiza un retiro (disminuir saldo)"""
    try:
        data = request.get_json()
        cedula = data.get('cedula')
        monto = data.get('monto')

        if not cedula or monto is None:
            return jsonify({'success': False, 'error': 'Cédula y monto requeridos'}), 400

        comando = f"DISMINUIR {cedula} {monto}"
        logging.info(f"📥 Comando: {comando}")

        respuesta = SocketBridge.send_command(comando)
        resultado = SocketBridge.parsear_respuesta(respuesta)

        logging.info(f"📤 Respuesta: {respuesta}")
        return jsonify(resultado)

    except Exception as e:
        logging.error(f"❌ Error en /api/retiro: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cliente', methods=['POST'])
def crear_cliente():
    """Crea un nuevo cliente"""
    try:
        data = request.get_json()
        cedula = data.get('cedula')
        nombres = data.get('nombres')
        apellidos = data.get('apellidos')
        saldo = data.get('saldo', 0)

        if not cedula or not nombres or not apellidos:
            return jsonify({'success': False, 'error': 'Cédula, nombres y apellidos requeridos'}), 400

        comando = f"CREAR {cedula} {nombres} {apellidos} {saldo}"
        logging.info(f"📥 Comando: {comando}")

        respuesta = SocketBridge.send_command(comando)
        resultado = SocketBridge.parsear_respuesta(respuesta)

        logging.info(f"📤 Respuesta: {respuesta}")
        return jsonify(resultado)

    except Exception as e:
        logging.error(f"❌ Error en /api/cliente: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/historial/<cedula>', methods=['GET'])
def historial(cedula):
    """Obtiene el historial de transacciones de un cliente"""
    try:
        comando = f"HISTORIAL {cedula}"
        logging.info(f"📥 Comando: {comando}")

        respuesta = SocketBridge.send_command(comando)
        resultado = SocketBridge.parsear_respuesta(respuesta)

        logging.info(f"📤 Respuesta: {respuesta}")
        return jsonify(resultado)

    except Exception as e:
        logging.error(f"❌ Error en /api/historial: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def stats():
    """Obtiene las estadísticas del servidor"""
    try:
        comando = "STATS"
        logging.info(f"📥 Comando: {comando}")

        respuesta = SocketBridge.send_command(comando)
        resultado = SocketBridge.parsear_respuesta(respuesta)

        logging.info(f"📤 Respuesta: {respuesta}")
        return jsonify(resultado)

    except Exception as e:
        logging.error(f"❌ Error en /api/stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/simulate', methods=['POST'])
def simulate():
    """Ejecuta test_concurrency.py para demostrar concurrencia"""
    try:
        logging.info(f"🎯 Ejecutando pruebas de concurrencia...")
        
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        test_script = os.path.join(current_dir, 'test_concurrency.py')
        
        # Execute test_concurrency.py
        if sys.platform == 'win32':
            # Windows: Use start command to open in new console
            subprocess.Popen(
                f'start "Prueba de Concurrencia" cmd /k python "{test_script}"',
                shell=True,
                cwd=current_dir
            )
        else:
            # Unix/Linux: Use terminal emulator
            subprocess.Popen(
                [sys.executable, test_script],
                cwd=current_dir
            )
        
        logging.info(f"✅ Pruebas de concurrencia iniciadas correctamente")
        return jsonify({
            'success': True,
            'message': 'Pruebas de concurrencia iniciadas. Se ha abierto una nueva consola con los tests.'
        })

    except Exception as e:
        logging.error(f"❌ Error al ejecutar pruebas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Cliente conectado vía WebSocket"""
    logging.info(f"🔌 Cliente WebSocket conectado: {request.sid}")
    emit('connected', {'message': 'Conectado al servidor'})


@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado"""
    logging.info(f"🔌 Cliente WebSocket desconectado: {request.sid}")


@socketio.on('subscribe_balance')
def handle_subscribe_balance(data):
    """Cliente se suscribe a actualizaciones de saldo"""
    cedula = data.get('cedula')
    logging.info(f"📡 Cliente {request.sid} suscrito a cédula {cedula}")


def broadcast_balance_update(cedula, new_balance):
    """Broadcast actualización de saldo a todos los clientes conectados"""
    socketio.emit('balance_updated', {
        'cedula': cedula,
        'balance': new_balance
    }, broadcast=True)


def broadcast_stats():
    """Broadcast de estadísticas del servidor cada 3 segundos"""
    while True:
        try:
            time.sleep(3)
            comando = "STATS"
            respuesta = SocketBridge.send_command(comando)
            resultado = SocketBridge.parsear_respuesta(respuesta)
            
            if resultado.get('success'):
                socketio.emit('stats_updated', resultado, broadcast=True)
        except Exception as e:
            logging.error(f"Error broadcasting stats: {e}")


# Iniciar thread de broadcast de stats
stats_thread = threading.Thread(target=broadcast_stats, daemon=True)
stats_thread.start()


@app.errorhandler(404)
def not_found(error):
    """Maneja errores 404"""
    return jsonify({'success': False, 'error': 'Ruta no encontrada'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Maneja errores internos"""
    return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500


if __name__ == '__main__':
    logging.info(f"🚀 Iniciando bridge en port 5001")
    logging.info(f"🔗 Conectando a socket server en {SOCKET_HOST}:{SOCKET_PORT}")
    logging.info(f"🔌 WebSocket habilitado para actualizaciones en tiempo real")

    socketio.run(
        app,
        host='0.0.0.0',
        port=5001,
        debug=True,
        allow_unsafe_werkzeug=True
    )
