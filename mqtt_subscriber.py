"""
MQTT Subscriber - Sistema Bancario
Suscriptor de ejemplo para monitorear eventos en tiempo real
"""

import paho.mqtt.client as mqtt
import json
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MQTTSubscriber:
    """Suscriptor MQTT para monitorear eventos bancarios"""

    def __init__(self):
        self.broker_host = os.getenv('MQTT_BROKER_HOST', 'localhost')
        self.broker_port = int(os.getenv('MQTT_BROKER_PORT', 1883))
        self.client_id = f"banco_subscriber_{os.getpid()}"
        self.client = None

    def on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback cuando se conecta al broker (API v2)"""
        if reason_code == 0:
            logger.info("✅ Conectado a broker MQTT")
            
            # Suscribirse a todos los tópicos bancarios
            topics = [
                ("banco/transacciones", 1),      # QoS 1
                ("banco/depositos", 1),
                ("banco/retiros", 1),
                ("banco/transferencias", 1),     # Transferencias entre cuentas
                ("banco/saldo/#", 1),            # Wildcard para todos los saldos
                ("banco/estadisticas", 0),       # QoS 0 (best effort)
                ("banco/alertas", 2)             # QoS 2 (exactly once)
            ]
            
            for topic, qos in topics:
                client.subscribe(topic, qos)
                logger.info(f"📡 Suscrito a: {topic} (QoS {qos})")
        else:
            logger.error(f"❌ Falló conexión MQTT. Code: {reason_code}")

    def on_message(self, client, userdata, msg):
        """Callback cuando llega un mensaje"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))
            
            # Procesar según el tópico
            if topic == "banco/transacciones":
                self.handle_transaction(payload)
            elif topic == "banco/depositos":
                self.handle_deposit(payload)
            elif topic == "banco/retiros":
                self.handle_withdrawal(payload)
            elif topic == "banco/transferencias":
                self.handle_transfer(payload)
            elif topic.startswith("banco/saldo/"):
                self.handle_balance_update(payload, topic)
            elif topic == "banco/estadisticas":
                self.handle_stats(payload)
            elif topic == "banco/alertas":
                self.handle_alert(payload)
            else:
                logger.info(f"📨 [{topic}] {payload}")
                
        except json.JSONDecodeError:
            logger.warning(f"⚠️ Mensaje no JSON en {msg.topic}: {msg.payload}")
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}")

    def handle_transaction(self, payload):
        """Procesar evento de transacción"""
        logger.info(
            f"💳 TRANSACCIÓN: {payload['tipo']} "
            f"${payload['monto']:.2f} - "
            f"Cédula: {payload['cedula']} - "
            f"Saldo: ${payload['saldo_nuevo']:.2f}"
        )

    def handle_deposit(self, payload):
        """Procesar depósito"""
        logger.info(
            f"💰 DEPÓSITO: ${payload['monto']:.2f} - "
            f"Cédula: {payload['cedula']} - "
            f"Nuevo saldo: ${payload['saldo_nuevo']:.2f}"
        )

    def handle_withdrawal(self, payload):
        """Procesar retiro"""
        logger.info(
            f"💸 RETIRO: ${payload['monto']:.2f} - "
            f"Cédula: {payload['cedula']} - "
            f"Nuevo saldo: ${payload['saldo_nuevo']:.2f}"
        )

    def handle_transfer(self, payload):
        """Procesar transferencia"""
        logger.info(
            f"🔄 TRANSFERENCIA: ${payload['monto']:.2f} - "
            f"De: {payload['cedula_origen']} → A: {payload['cedula_destino']} - "
            f"Saldo origen: ${payload['saldo_origen']:.2f} | "
            f"Saldo destino: ${payload['saldo_destino']:.2f}"
        )

    def handle_balance_update(self, payload, topic):
        """Procesar actualización de saldo"""
        cedula = topic.split('/')[-1]
        saldo_anterior = payload.get('saldo_anterior', 'N/A')
        logger.info(
            f"💵 SALDO ACTUALIZADO - Cédula: {cedula} - "
            f"${saldo_anterior} → ${payload['saldo_nuevo']:.2f}"
        )

    def handle_stats(self, payload):
        """Procesar estadísticas"""
        logger.info(
            f"📊 STATS: Conectados: {payload.get('clientes_conectados', 0)} | "
            f"Transacciones: {payload.get('total_transacciones', 0)} | "
            f"IPs activas: {payload.get('ips_activas', 0)}"
        )

    def handle_alert(self, payload):
        """Procesar alertas"""
        logger.warning(
            f"🚨 ALERTA [{payload['type']}]: {payload['message']} "
            f"(Cédula: {payload.get('cedula', 'N/A')})"
        )

    def on_disconnect(self, client, userdata, rc):
        """Callback cuando se desconecta del broker"""
        if rc != 0:
            logger.warning(f"⚠️ Desconexión inesperada de MQTT. Code: {rc}")

    def start(self):
        """Iniciar suscriptor"""
        try:
            # Usar callback_api_version para evitar deprecation warning
            self.client = mqtt.Client(
                client_id=self.client_id,
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2
            )
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect

            logger.info(f"🔗 Conectando a {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            
            # Blocking loop (mantiene el subscriber corriendo)
            logger.info("👂 Escuchando eventos MQTT... (Ctrl+C para salir)")
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            logger.info("\n⏹️ Deteniendo subscriber...")
            self.stop()
        except ConnectionRefusedError:
            logger.error(f"❌ No se pudo conectar a MQTT broker en {self.broker_host}:{self.broker_port}")
            logger.error(f"   Asegúrate de que Mosquitto esté corriendo: docker-compose up mosquitto")
        except Exception as e:
            logger.error(f"❌ Error en subscriber: {e}")

    def stop(self):
        """Detener suscriptor"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("🔌 Subscriber desconectado")


if __name__ == "__main__":
    print("=" * 60)
    print("🏦 Sistema Bancario - Monitor MQTT")
    print("=" * 60)
    
    subscriber = MQTTSubscriber()
    subscriber.start()
