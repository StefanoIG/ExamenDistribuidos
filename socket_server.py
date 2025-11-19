"""
Servidor de Sockets - Sistema Bancario Distribuido
Características Pro:
- Threading para múltiples clientes concurrentes
- Lock por cédula para sincronización
- Logging detallado de operaciones
- Tabla de transacciones (historial)
- Protocolo de comandos estructurado
- Control de errores robusto
"""

import socket
import threading
import logging
from datetime import datetime
from decimal import Decimal
from db_connection import DatabaseManager
import os

# Importar MQTT de forma opcional
try:
    from mqtt_publisher import MQTTPublisher
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logging.warning("⚠️ paho-mqtt no disponible. Sistema funcionará sin MQTT.")

# Configuración de logging avanzado
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class SocketServer:
    """Servidor de sockets con control de concurrencia avanzado"""

    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.server_socket = None
        self.db_manager = None
        self.mqtt_publisher = None  # Publisher MQTT
        self.running = False

        # Control de concurrencia: un lock por cada cédula
        self.client_locks = {}
        self.locks_mutex = threading.Lock()  # Protege el diccionario de locks

        # Estadísticas del servidor
        self.stats = {
            'clientes_conectados': 0,
            'total_transacciones': 0,
            'clientes_activos': set()
        }
        self.stats_lock = threading.Lock()

    def get_client_lock(self, cedula):
        """Obtiene o crea un lock para una cédula específica"""
        with self.locks_mutex:
            if cedula not in self.client_locks:
                self.client_locks[cedula] = threading.Lock()
                logging.debug(f"Lock creado para cédula: {cedula}")
            return self.client_locks[cedula]

    def initialize_database(self, db_config):
        """Inicializa el gestor de base de datos"""
        self.db_manager = DatabaseManager(db_config)
        logging.info("✅ Gestor de base de datos inicializado")
        
        # Inicializar MQTT Publisher (solo si está disponible)
        if MQTT_AVAILABLE:
            try:
                self.mqtt_publisher = MQTTPublisher()
                if self.mqtt_publisher.connect():
                    logging.info("✅ MQTT Publisher conectado")
                else:
                    logging.warning("⚠️ MQTT no disponible, continuando sin publicación MQTT")
                    self.mqtt_publisher = None
            except Exception as e:
                logging.warning(f"⚠️ Error conectando MQTT: {e}. Sistema funcionará sin MQTT.")
                self.mqtt_publisher = None
        else:
            logging.info("ℹ️ MQTT deshabilitado (paho-mqtt no instalado)")
            self.mqtt_publisher = None

    def start(self):
        """Inicia el servidor de sockets"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)

            self.running = True
            logging.info(f"🚀 Servidor escuchando en {self.host}:{self.port}")
            logging.info(f"📊 Esperando conexiones de clientes...")

            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()

                    # Actualizar estadísticas
                    with self.stats_lock:
                        self.stats['clientes_conectados'] += 1
                        self.stats['clientes_activos'].add(client_address[0])

                    logging.info(f"✅ Cliente conectado desde {client_address}")

                    # Crear hilo para manejar al cliente
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()

                except Exception as e:
                    if self.running:
                        logging.error(f"❌ Error aceptando conexión: {e}")

        except Exception as e:
            logging.error(f"❌ Error iniciando servidor: {e}")
        finally:
            self.stop()

    def handle_client(self, conn, addr):
        """Maneja las peticiones de un cliente en un hilo separado"""
        client_id = f"{addr[0]}:{addr[1]}"
        logging.info(f"🔵 [Thread-{threading.current_thread().name}] Atendiendo cliente {client_id}")

        try:
            # Enviar mensaje de bienvenida
            welcome_msg = "BIENVENIDO|Sistema Bancario Distribuido v1.0\n"
            conn.send(welcome_msg.encode('utf-8'))

            while True:
                # Recibir mensaje del cliente
                data = conn.recv(4096).decode('utf-8').strip()

                if not data:
                    logging.info(f"⚠️ Cliente {client_id} desconectado (sin datos)")
                    break

                logging.info(f"📥 Cliente {client_id} -> {data}")

                # Procesar comando
                response = self.procesar_comando(data, client_id)

                # Enviar respuesta
                conn.send(response.encode('utf-8'))
                logging.info(f"📤 Respuesta a {client_id} -> {response}")

                # Si el comando es SALIR, cerrar conexión
                if data.upper().startswith('SALIR'):
                    break

        except ConnectionResetError:
            logging.warning(f"⚠️ Cliente {client_id} cerró la conexión abruptamente")
        except Exception as e:
            logging.error(f"❌ Error manejando cliente {client_id}: {e}")
        finally:
            conn.close()
            with self.stats_lock:
                self.stats['clientes_activos'].discard(addr[0])
            logging.info(f"🔴 Conexión cerrada con {client_id}")

    def procesar_comando(self, mensaje, client_id):
        """Procesa comandos del cliente y retorna respuesta"""
        try:
            partes = mensaje.split()
            if not partes:
                return "ERROR|Comando vacío"

            comando = partes[0].upper()

            # Comandos disponibles
            if comando == 'CONSULTA' and len(partes) >= 2:
                cedula = partes[1]
                return self.cmd_consulta(cedula, client_id)

            elif comando == 'AUMENTAR' and len(partes) >= 3:
                cedula = partes[1]
                monto = float(partes[2])
                return self.cmd_aumentar(cedula, monto, client_id)

            elif comando == 'DISMINUIR' and len(partes) >= 3:
                cedula = partes[1]
                monto = float(partes[2])
                return self.cmd_disminuir(cedula, monto, client_id)

            elif comando == 'CREAR' and len(partes) >= 3:
                cedula = partes[1]
                nombre_completo = ' '.join(partes[2:])
                return self.cmd_crear(cedula, nombre_completo, client_id)

            elif comando == 'TRANSFERIR' and len(partes) >= 4:
                cedula_origen = partes[1]
                cedula_destino = partes[2]
                monto = float(partes[3])
                return self.cmd_transferir(cedula_origen, cedula_destino, monto, client_id)

            elif comando == 'HISTORIAL' and len(partes) >= 2:
                cedula = partes[1]
                return self.cmd_historial(cedula, client_id)

            elif comando == 'SALIR':
                return "OK|Hasta pronto"

            elif comando == 'STATS':
                return self.cmd_stats()

            else:
                return "ERROR|Comando no reconocido o parámetros incorrectos"

        except ValueError:
            return "ERROR|Formato de monto inválido"
        except Exception as e:
            logging.error(f"❌ Error procesando comando: {e}")
            return f"ERROR|{str(e)}"

    def cmd_consulta(self, cedula, client_id):
        """Consulta información de un cliente"""
        try:
            cliente = self.db_manager.consultar_cliente(cedula)

            if cliente:
                # Formato: OK|NOMBRES|APELLIDOS|SALDO
                return f"OK|{cliente['nombres']}|{cliente['apellidos']}|{cliente['saldo']:.2f}"
            else:
                return "ERROR|Cliente no encontrado"

        except Exception as e:
            logging.error(f"❌ Error en CONSULTA: {e}")
            return f"ERROR|{str(e)}"

    def cmd_aumentar(self, cedula, monto, client_id):
        """Aumenta el saldo de un cliente con control de concurrencia"""
        if monto <= 0:
            return "ERROR|El monto debe ser positivo"

        # Control de concurrencia: lock por cédula
        lock = self.get_client_lock(cedula)

        with lock:
            try:
                logging.info(f"🔒 Lock adquirido para cédula {cedula} - Operación DEPOSITO")

                # Consultar cliente
                cliente = self.db_manager.consultar_cliente(cedula)
                if not cliente:
                    return "ERROR|Cliente no encontrado"

                saldo_anterior = Decimal(str(cliente['saldo']))
                nuevo_saldo = saldo_anterior + Decimal(str(monto))

                # Actualizar saldo
                self.db_manager.actualizar_saldo(cedula, float(nuevo_saldo))

                # Registrar transacción
                self.db_manager.insertar_transaccion(
                    cedula=cedula,
                    tipo='DEPOSITO',
                    monto=monto,
                    saldo_final=nuevo_saldo
                )

                # Actualizar estadísticas
                with self.stats_lock:
                    self.stats['total_transacciones'] += 1

                # 🆕 Publicar evento MQTT
                if self.mqtt_publisher and self.mqtt_publisher.connected:
                    self.mqtt_publisher.publish_transaction(
                        cedula=cedula,
                        tipo='DEPOSITO',
                        monto=float(monto),
                        saldo_nuevo=float(nuevo_saldo)
                    )
                    self.mqtt_publisher.publish_balance_update(
                        cedula=cedula,
                        saldo_nuevo=float(nuevo_saldo),
                        saldo_anterior=float(saldo_anterior)
                    )

                logging.info(
                    f"💰 DEPOSITO exitoso - Cédula: {cedula}, "
                    f"Monto: ${monto:.2f}, "
                    f"Saldo: ${float(saldo_anterior):.2f} -> ${float(nuevo_saldo):.2f}"
                )

                return f"OK|Depósito exitoso|{float(nuevo_saldo):.2f}"

            except Exception as e:
                logging.error(f"❌ Error en AUMENTAR: {e}")
                return f"ERROR|{str(e)}"
            finally:
                logging.info(f"🔓 Lock liberado para cédula {cedula}")

    def cmd_disminuir(self, cedula, monto, client_id):
        """Disminuye el saldo de un cliente con control de concurrencia"""
        if monto <= 0:
            return "ERROR|El monto debe ser positivo"

        # Control de concurrencia: lock por cédula
        lock = self.get_client_lock(cedula)

        with lock:
            try:
                logging.info(f"🔒 Lock adquirido para cédula {cedula} - Operación RETIRO")

                # Consultar cliente
                cliente = self.db_manager.consultar_cliente(cedula)
                if not cliente:
                    return "ERROR|Cliente no encontrado"

                saldo_anterior = Decimal(str(cliente['saldo']))

                # Verificar saldo suficiente
                if saldo_anterior < Decimal(str(monto)):
                    logging.warning(
                        f"⚠️ Saldo insuficiente - Cédula: {cedula}, "
                        f"Saldo: ${float(saldo_anterior):.2f}, Retiro: ${monto:.2f}"
                    )
                    return f"ERROR|Saldo insuficiente|{float(saldo_anterior):.2f}"

                nuevo_saldo = saldo_anterior - Decimal(str(monto))

                # Actualizar saldo
                self.db_manager.actualizar_saldo(cedula, float(nuevo_saldo))

                # Registrar transacción
                self.db_manager.insertar_transaccion(
                    cedula=cedula,
                    tipo='RETIRO',
                    monto=monto,
                    saldo_final=nuevo_saldo
                )

                # Actualizar estadísticas
                with self.stats_lock:
                    self.stats['total_transacciones'] += 1

                # 🆕 Publicar evento MQTT
                if self.mqtt_publisher and self.mqtt_publisher.connected:
                    self.mqtt_publisher.publish_transaction(
                        cedula=cedula,
                        tipo='RETIRO',
                        monto=float(monto),
                        saldo_nuevo=float(nuevo_saldo)
                    )
                    self.mqtt_publisher.publish_balance_update(
                        cedula=cedula,
                        saldo_nuevo=float(nuevo_saldo),
                        saldo_anterior=float(saldo_anterior)
                    )
                    
                    # Publicar alerta si saldo bajo
                    if nuevo_saldo < Decimal('100.00'):
                        self.mqtt_publisher.publish_alert(
                            alert_type='LOW_BALANCE',
                            message=f'Saldo bajo: ${float(nuevo_saldo):.2f}',
                            cedula=cedula,
                            data={'saldo': float(nuevo_saldo)}
                        )

                logging.info(
                    f"💸 RETIRO exitoso - Cédula: {cedula}, "
                    f"Monto: ${monto:.2f}, "
                    f"Saldo: ${float(saldo_anterior):.2f} -> ${float(nuevo_saldo):.2f}"
                )

                return f"OK|Retiro exitoso|{float(nuevo_saldo):.2f}"

            except Exception as e:
                logging.error(f"❌ Error en DISMINUIR: {e}")
                return f"ERROR|{str(e)}"
            finally:
                logging.info(f"🔓 Lock liberado para cédula {cedula}")

    def cmd_crear(self, cedula, nombre_completo, client_id):
        """Crea un nuevo cliente con saldo inicial de 0"""
        try:
            # Validar formato de cédula (debe comenzar con 0)
            if not cedula.startswith('0'):
                return "ERROR|La cédula debe comenzar con 0"

            # Verificar si ya existe
            if self.db_manager.consultar_cliente(cedula):
                return "ERROR|Cliente ya existe"

            # Separar nombres y apellidos del nombre completo
            partes_nombre = nombre_completo.split()
            if len(partes_nombre) < 2:
                return "ERROR|Debe proporcionar al menos nombre y apellido"
            
            # Asumir que la primera mitad son nombres y la segunda apellidos
            mitad = len(partes_nombre) // 2
            nombres = ' '.join(partes_nombre[:mitad])
            apellidos = ' '.join(partes_nombre[mitad:])

            # Crear cliente con saldo inicial 0
            saldo_inicial = 0.0
            self.db_manager.crear_cliente(cedula, nombres, apellidos, saldo_inicial)

            logging.info(
                f"👤 Cliente creado - Cédula: {cedula}, "
                f"Nombre: {nombre_completo}, Saldo: ${saldo_inicial:.2f}"
            )

            return f"OK|Cliente creado exitosamente|{nombres}|{apellidos}|0.00"

        except Exception as e:
            logging.error(f"❌ Error en CREAR: {e}")
            return f"ERROR|{str(e)}"

    def cmd_transferir(self, cedula_origen, cedula_destino, monto, client_id):
        """Transfiere dinero entre dos cuentas"""
        # Lock de ambas cédulas en orden para evitar deadlocks
        cedulas_ordenadas = sorted([cedula_origen, cedula_destino])
        lock1 = self.get_client_lock(cedulas_ordenadas[0])
        lock2 = self.get_client_lock(cedulas_ordenadas[1])

        try:
            with lock1:
                with lock2:
                    # Verificar que ambas cuentas existan
                    cliente_origen = self.db_manager.consultar_cliente(cedula_origen)
                    if not cliente_origen:
                        return "ERROR|Cuenta origen no existe"

                    cliente_destino = self.db_manager.consultar_cliente(cedula_destino)
                    if not cliente_destino:
                        return "ERROR|Cuenta destino no existe"

                    # Verificar saldo suficiente
                    saldo_origen = float(cliente_origen['saldo'])
                    if saldo_origen < monto:
                        return "ERROR|Saldo insuficiente en cuenta origen"

                    # Realizar transferencia
                    nuevo_saldo_origen = saldo_origen - monto
                    nuevo_saldo_destino = float(cliente_destino['saldo']) + monto

                    # Actualizar saldos
                    self.db_manager.actualizar_saldo(cedula_origen, nuevo_saldo_origen)
                    self.db_manager.actualizar_saldo(cedula_destino, nuevo_saldo_destino)

                    # Registrar transacciones
                    self.db_manager.insertar_transaccion(cedula_origen, 'TRANSFERENCIA_ENVIADA', monto, nuevo_saldo_origen)
                    self.db_manager.insertar_transaccion(cedula_destino, 'TRANSFERENCIA_RECIBIDA', monto, nuevo_saldo_destino)

                    # Actualizar estadísticas
                    with self.stats_lock:
                        self.stats['total_transacciones'] += 2

                    # Publicar a MQTT
                    if self.mqtt_publisher and self.mqtt_publisher.connected:
                        self.mqtt_publisher.publish_transfer(
                            cedula_origen, cedula_destino, monto,
                            nuevo_saldo_origen, nuevo_saldo_destino
                        )
                        self.mqtt_publisher.publish_balance_update(cedula_origen, nuevo_saldo_origen, saldo_origen)
                        self.mqtt_publisher.publish_balance_update(cedula_destino, nuevo_saldo_destino, cliente_destino['saldo'])

                    logging.info(
                        f"🔄 TRANSFERENCIA: ${monto:.2f} de {cedula_origen} a {cedula_destino} | "
                        f"Cliente {client_id}"
                    )

                    return f"OK|Transferencia exitosa|{nuevo_saldo_origen:.2f}|{nuevo_saldo_destino:.2f}"

        except Exception as e:
            logging.error(f"❌ Error en TRANSFERIR: {e}")
            return f"ERROR|{str(e)}"

    def cmd_historial(self, cedula, client_id):
        """Obtiene el historial de transacciones de un cliente"""
        try:
            transacciones = self.db_manager.obtener_historial(cedula, limite=10)

            if not transacciones:
                return "OK|Sin transacciones"

            # Formato: OK|TIPO|MONTO|SALDO_FINAL|FECHA;TIPO|MONTO|SALDO_FINAL|FECHA;...
            resultado = "OK"
            for tx in transacciones:
                resultado += f"|{tx['tipo']}|{tx['monto']:.2f}|{tx['saldo_final']:.2f}|{tx['fecha']}"

            return resultado

        except Exception as e:
            logging.error(f"❌ Error en HISTORIAL: {e}")
            return f"ERROR|{str(e)}"

    def cmd_stats(self):
        """Retorna estadísticas del servidor"""
        with self.stats_lock:
            stats_data = {
                'clientes_conectados': self.stats['clientes_conectados'],
                'total_transacciones': self.stats['total_transacciones'],
                'ips_activas': len(self.stats['clientes_activos'])
            }
            
            # 🆕 Publicar estadísticas a MQTT
            if self.mqtt_publisher and self.mqtt_publisher.connected:
                self.mqtt_publisher.publish_stats(stats_data)
            
            return (
                f"OK|Clientes conectados: {self.stats['clientes_conectados']}|"
                f"Transacciones: {self.stats['total_transacciones']}|"
                f"IPs activas: {len(self.stats['clientes_activos'])}"
            )

    def stop(self):
        """Detiene el servidor"""
        logging.info("🛑 Deteniendo servidor...")
        self.running = False

        # Desconectar MQTT
        if self.mqtt_publisher:
            self.mqtt_publisher.disconnect()

        if self.server_socket:
            self.server_socket.close()

        if self.db_manager:
            self.db_manager.close()

        logging.info("✅ Servidor detenido correctamente")


if __name__ == "__main__":
    from dotenv import load_dotenv

    # Cargar configuración desde archivo .env
    load_dotenv()

    # Configuración desde variables de entorno
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'database': os.getenv('DB_NAME', 'examen'),
        'user': os.getenv('DB_USER', 'socketuser'),
        'password': os.getenv('DB_PASSWORD', '12345')
    }

    server_host = os.getenv('SERVER_HOST', '0.0.0.0')
    server_port = int(os.getenv('SERVER_PORT', 5000))

    # Crear e iniciar servidor
    server = SocketServer(server_host, server_port)
    server.initialize_database(db_config)

    try:
        server.start()
    except KeyboardInterrupt:
        logging.info("\n⚠️ Interrupción por teclado recibida")
        server.stop()