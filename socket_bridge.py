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
                # Formato: OK|Cliente creado exitosamente|nombres|apellidos|saldo
                return {
                    'success': True,
                    'action': 'crear',
                    'data': {
                        'mensaje': 'Cliente creado exitosamente',
                        'nombres': partes[2] if len(partes) > 2 else '',
                        'apellidos': partes[3] if len(partes) > 3 else '',
                        'saldo_inicial': float(partes[4]) if len(partes) > 4 else 0.0
                    }
                }

            elif 'Transferencia exitosa' in respuesta:
                # Formato: OK|Transferencia exitosa|saldo_origen|saldo_destino
                return {
                    'success': True,
                    'action': 'transferir',
                    'data': {
                        'mensaje': 'Transferencia exitosa',
                        'saldo_origen': float(partes[2]) if len(partes) > 2 else 0.0,
                        'saldo_destino': float(partes[3]) if len(partes) > 3 else 0.0
                    }
                }

            elif 'Sin transacciones' in respuesta:
                return {
                    'success': True,
                    'action': 'historial',
                    'data': {'transacciones': []}
                }

            elif 'Clientes conectados' in respuesta:
                # Formato: OK|Clientes conectados: X|Transacciones: Y|IPs activas: Z
                try:
                    clientes_activos = int(partes[1].split(': ')[-1])
                    operaciones_simultaneas = int(partes[2].split(': ')[-1])
                    conexiones_activas = int(partes[3].split(': ')[-1])
                except (ValueError, IndexError) as e:
                    logging.warning(f"Error parseando stats: {e}, respuesta: {respuesta}")
                    clientes_activos = 0
                    operaciones_simultaneas = 0
                    conexiones_activas = 0
                
                return {
                    'success': True,
                    'action': 'stats',
                    'estadisticas': {
                        'clientes_activos': clientes_activos,
                        'operaciones_simultaneas': operaciones_simultaneas,
                        'conexiones_activas': conexiones_activas
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

        # Emitir actualización de balance por WebSocket
        if resultado.get('success') and resultado.get('data', {}).get('nuevo_saldo'):
            nuevo_saldo = resultado['data']['nuevo_saldo']
            broadcast_balance_update(cedula, nuevo_saldo)

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

        # Emitir actualización de balance por WebSocket
        if resultado.get('success') and resultado.get('data', {}).get('nuevo_saldo'):
            nuevo_saldo = resultado['data']['nuevo_saldo']
            broadcast_balance_update(cedula, nuevo_saldo)

        logging.info(f"📤 Respuesta: {respuesta}")
        return jsonify(resultado)

    except Exception as e:
        logging.error(f"❌ Error en /api/retiro: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/crear', methods=['POST'])
def crear_cliente():
    """Crea un nuevo cliente con saldo inicial 0"""
    try:
        data = request.get_json()
        cedula = data.get('cedula')
        nombre = data.get('nombre')

        if not cedula or not nombre:
            return jsonify({'success': False, 'error': 'Cédula y nombre completo requeridos'}), 400

        # Validar que cédula comience con 0
        if not cedula.startswith('0'):
            return jsonify({'success': False, 'error': 'La cédula debe comenzar con 0'}), 400

        comando = f"CREAR {cedula} {nombre}"
        logging.info(f"📥 Comando: {comando}")

        respuesta = SocketBridge.send_command(comando)
        resultado = SocketBridge.parsear_respuesta(respuesta)

        logging.info(f"📤 Respuesta: {respuesta}")
        return jsonify(resultado)

    except Exception as e:
        logging.error(f"❌ Error en /api/crear: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/transferir', methods=['POST'])
def transferir():
    """Realiza una transferencia entre cuentas"""
    try:
        data = request.get_json()
        cedula_origen = data.get('cedula_origen')
        cedula_destino = data.get('cedula_destino')
        monto = data.get('monto')

        if not cedula_origen or not cedula_destino or monto is None:
            return jsonify({'success': False, 'error': 'Cédula origen, destino y monto requeridos'}), 400

        comando = f"TRANSFERIR {cedula_origen} {cedula_destino} {monto}"
        logging.info(f"📥 Comando: {comando}")

        respuesta = SocketBridge.send_command(comando)
        resultado = SocketBridge.parsear_respuesta(respuesta)

        # Emitir actualización de balance para ambas cuentas
        if resultado.get('success'):
            data_parts = resultado.get('data', {})
            if 'saldo_origen' in data_parts:
                broadcast_balance_update(cedula_origen, data_parts['saldo_origen'])
            if 'saldo_destino' in data_parts:
                broadcast_balance_update(cedula_destino, data_parts['saldo_destino'])

        logging.info(f"📤 Respuesta: {respuesta}")
        return jsonify(resultado)

    except Exception as e:
        logging.error(f"❌ Error en /api/transferir: {e}")
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


# Mantener registro de clientes suscritos por cédula
active_subscriptions = {}  # {cedula: [sid1, sid2, ...]}
subscriptions_lock = threading.Lock()

@socketio.on('connect')
def handle_connect():
    """Cliente WebSocket conectado"""
    logging.info(f"🔌 Cliente WebSocket conectado: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Cliente WebSocket desconectado"""
    # Remover de todas las suscripciones
    with subscriptions_lock:
        for cedula in list(active_subscriptions.keys()):
            if request.sid in active_subscriptions[cedula]:
                active_subscriptions[cedula].remove(request.sid)
                if not active_subscriptions[cedula]:
                    del active_subscriptions[cedula]
    logging.info(f"🔌 Cliente WebSocket desconectado: {request.sid}")

@socketio.on('subscribe_balance')
def handle_subscribe_balance(data):
    """Cliente se suscribe a actualizaciones de saldo e historial"""
    cedula = data.get('cedula')
    with subscriptions_lock:
        if cedula not in active_subscriptions:
            active_subscriptions[cedula] = []
        if request.sid not in active_subscriptions[cedula]:
            active_subscriptions[cedula].append(request.sid)
    logging.info(f"📡 Cliente {request.sid} suscrito a cédula {cedula}")
    
    # Enviar historial inicial inmediatamente
    try:
        comando = f"HISTORIAL {cedula}"
        respuesta = SocketBridge.send_command(comando)
        resultado = SocketBridge.parsear_respuesta(respuesta)
        
        if resultado.get('success') and resultado.get('data', {}).get('transacciones'):
            emit('transactions_updated', {
                'cedula': cedula,
                'transactions': resultado['data']['transacciones']
            })
    except Exception as e:
        logging.error(f"Error enviando historial inicial: {e}")


def broadcast_balance_update(cedula, new_balance):
    """Broadcast actualización de saldo y historial a todos los clientes conectados"""
    # Emitir actualización de balance
    socketio.emit('balance_updated', {
        'cedula': cedula,
        'balance': new_balance
    })
    
    # Obtener historial actualizado y emitirlo
    try:
        comando = f"HISTORIAL {cedula}"
        respuesta = SocketBridge.send_command(comando)
        resultado = SocketBridge.parsear_respuesta(respuesta)
        
        if resultado.get('success') and resultado.get('data', {}).get('transacciones'):
            socketio.emit('transactions_updated', {
                'cedula': cedula,
                'transactions': resultado['data']['transacciones']
            })
    except Exception as e:
        logging.error(f"Error obteniendo historial actualizado: {e}")


def broadcast_stats():
    """Broadcast de estadísticas del servidor cada 3 segundos"""
    while True:
        try:
            time.sleep(3)
            comando = "STATS"
            respuesta = SocketBridge.send_command(comando)
            resultado = SocketBridge.parsear_respuesta(respuesta)
            
            if resultado.get('success'):
                socketio.emit('stats_updated', resultado)
        except Exception as e:
            logging.error(f"Error broadcasting stats: {e}")


def broadcast_transactions():
    """Broadcast de historial de transacciones para cédulas activas cada 5 segundos"""
    while True:
        try:
            time.sleep(5)
            # Obtener lista de cédulas activas
            with subscriptions_lock:
                cedulas_activas = list(active_subscriptions.keys())
            
            # Broadcast historial para cada cédula activa
            for cedula in cedulas_activas:
                try:
                    comando = f"HISTORIAL {cedula}"
                    respuesta = SocketBridge.send_command(comando)
                    resultado = SocketBridge.parsear_respuesta(respuesta)
                    
                    if resultado.get('success') and resultado.get('data', {}).get('transacciones'):
                        socketio.emit('transactions_updated', {
                            'cedula': cedula,
                            'transactions': resultado['data']['transacciones']
                        })
                except Exception as e:
                    logging.error(f"Error broadcasting transactions para {cedula}: {e}")
        except Exception as e:
            logging.error(f"Error en broadcast_transactions: {e}")


# Iniciar threads de broadcast
stats_thread = threading.Thread(target=broadcast_stats, daemon=True)
stats_thread.start()

transactions_thread = threading.Thread(target=broadcast_transactions, daemon=True)
transactions_thread.start()


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
