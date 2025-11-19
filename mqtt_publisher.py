"""
MQTT Publisher - Sistema Bancario
Publica eventos de transacciones a broker MQTT
"""

import paho.mqtt.client as mqtt
import json
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class MQTTPublisher:
    """Publicador MQTT para eventos bancarios"""

    def __init__(self):
        self.broker_host = os.getenv('MQTT_BROKER_HOST', 'localhost')
        self.broker_port = int(os.getenv('MQTT_BROKER_PORT', 1883))
        self.username = os.getenv('MQTT_USERNAME')
        self.password = os.getenv('MQTT_PASSWORD')
        self.client_id = f"banco_publisher_{os.getpid()}"
        self.client = None
        self.connected = False

        # Tópicos MQTT
        self.TOPIC_TRANSACTIONS = "banco/transacciones"  # Todas las transacciones
        self.TOPIC_DEPOSITS = "banco/depositos"          # Solo depósitos
        self.TOPIC_WITHDRAWALS = "banco/retiros"         # Solo retiros
        self.TOPIC_TRANSFERS = "banco/transferencias"    # Transferencias
        self.TOPIC_BALANCE = "banco/saldo"               # Cambios de saldo
        self.TOPIC_STATS = "banco/estadisticas"          # Estadísticas del servidor
        self.TOPIC_ALERTS = "banco/alertas"              # Alertas (saldo bajo, etc)

    def connect(self):
        """Conectar al broker MQTT"""
        try:
            self.client = mqtt.Client(
                client_id=self.client_id,
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2
            )
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect

            # Configurar credenciales si están definidas
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # Configurar TLS para HiveMQ Cloud (puerto 8883)
            if self.broker_port == 8883:
                import ssl
                self.client.tls_set(
                    ca_certs=None,
                    certfile=None,
                    keyfile=None,
                    cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLS,
                    ciphers=None
                )
                self.client.tls_insecure_set(False)  # Validar certificado

            # Configurar will message (en caso de desconexión inesperada)
            will_payload = json.dumps({
                'event': 'publisher_disconnected',
                'client_id': self.client_id,
                'timestamp': datetime.now().isoformat()
            })
            self.client.will_set(self.TOPIC_ALERTS, will_payload, qos=1, retain=False)

            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_start()  # Non-blocking loop
            logger.info(f"🔗 Conectando a broker MQTT {self.broker_host}:{self.broker_port}")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando a MQTT broker: {e}")
            return False

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback cuando se conecta al broker (API v2)"""
        if reason_code == 0:
            self.connected = True
            logger.info("✅ Conectado a broker MQTT")
        else:
            logger.error(f"❌ Falló conexión MQTT. Code: {reason_code}")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        """Callback cuando se desconecta del broker (API v2)"""
        self.connected = False
        if reason_code != 0:
            logger.warning(f"⚠️ Desconexión inesperada de MQTT. Code: {reason_code}")

    def publish_transaction(self, cedula, tipo, monto, saldo_nuevo, timestamp=None):
        """Publicar evento de transacción"""
        if not self.connected:
            logger.warning("MQTT no conectado. Saltando publicación.")
            return False

        timestamp = timestamp or datetime.now().isoformat()

        payload = {
            'cedula': cedula,
            'tipo': tipo,
            'monto': monto,
            'saldo_nuevo': saldo_nuevo,
            'timestamp': timestamp
        }

        # Publicar en tópico general de transacciones
        self.client.publish(
            self.TOPIC_TRANSACTIONS,
            json.dumps(payload),
            qos=1,  # Al menos una vez
            retain=False
        )

        # Publicar en tópico específico según tipo
        topic = self.TOPIC_DEPOSITS if tipo == 'DEPOSITO' else self.TOPIC_WITHDRAWALS
        self.client.publish(topic, json.dumps(payload), qos=1, retain=False)

        logger.info(f"📤 MQTT: {tipo} ${monto} para cédula {cedula}")
        return True

    def publish_transfer(self, cedula_origen, cedula_destino, monto, saldo_origen, saldo_destino, timestamp=None):
        """Publicar evento de transferencia"""
        if not self.connected:
            logger.warning("MQTT no conectado. Saltando publicación.")
            return False

        timestamp = timestamp or datetime.now().isoformat()

        payload = {
            'cedula_origen': cedula_origen,
            'cedula_destino': cedula_destino,
            'monto': monto,
            'saldo_origen': saldo_origen,
            'saldo_destino': saldo_destino,
            'timestamp': timestamp
        }

        # Publicar en tópico de transferencias
        self.client.publish(
            self.TOPIC_TRANSFERS,
            json.dumps(payload),
            qos=1,
            retain=False
        )

        logger.info(f"📤 MQTT: TRANSFERENCIA ${monto} de {cedula_origen} a {cedula_destino}")
        return True

    def publish_balance_update(self, cedula, saldo_nuevo, saldo_anterior=None):
        """Publicar actualización de saldo"""
        if not self.connected:
            return False

        payload = {
            'cedula': cedula,
            'saldo_nuevo': saldo_nuevo,
            'saldo_anterior': saldo_anterior,
            'timestamp': datetime.now().isoformat()
        }

        # Usar tópico específico por cédula para filtrado eficiente
        topic = f"{self.TOPIC_BALANCE}/{cedula}"
        self.client.publish(topic, json.dumps(payload), qos=1, retain=True)  # Retain last balance

        return True

    def publish_stats(self, stats_data):
        """Publicar estadísticas del servidor"""
        if not self.connected:
            return False

        payload = {
            **stats_data,
            'timestamp': datetime.now().isoformat()
        }

        self.client.publish(
            self.TOPIC_STATS,
            json.dumps(payload),
            qos=0,  # Best effort para stats
            retain=True  # Mantener último valor
        )
        return True

    def publish_alert(self, alert_type, message, cedula=None, data=None):
        """Publicar alerta (saldo bajo, transacción rechazada, etc)"""
        if not self.connected:
            return False

        payload = {
            'type': alert_type,
            'message': message,
            'cedula': cedula,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

        self.client.publish(
            self.TOPIC_ALERTS,
            json.dumps(payload),
            qos=2,  # Exactly once para alertas
            retain=False
        )

        logger.warning(f"🚨 Alerta MQTT: {alert_type} - {message}")
        return True

    def disconnect(self):
        """Desconectar del broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("🔌 Desconectado de broker MQTT")
