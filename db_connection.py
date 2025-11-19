"""
Módulo de Conexión a Base de Datos
Gestiona todas las operaciones con MySQL/MariaDB
Incluye tabla de transacciones para historial
"""

import mysql.connector
from mysql.connector import pooling
import logging
from contextlib import contextmanager


class DatabaseManager:
    """Gestiona conexiones y operaciones con MySQL/MariaDB"""

    def __init__(self, config):
        """
        Inicializa el pool de conexiones

        Args:
            config: dict con host, port, database, user, password
        """
        self.config = config
        try:
            self.connection_pool = pooling.MySQLConnectionPool(
                pool_name="sistema_bancario_pool",
                pool_size=5,
                pool_reset_session=True,
                host=config['host'],
                port=config.get('port', 3306),
                database=config['database'],
                user=config['user'],
                password=config['password'],
                autocommit=False
            )
            logging.info("✅ Pool de conexiones a BD creado exitosamente")
        except Exception as e:
            logging.error(f"❌ Error creando pool de conexiones: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager para obtener y liberar conexiones del pool"""
        conn = self.connection_pool.get_connection()
        try:
            yield conn
        finally:
            conn.close()

    def consultar_cliente(self, cedula):
        """
        Consulta un cliente por cédula

        Returns:
            dict con datos del cliente o None si no existe
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT cedula, nombres, apellidos, saldo, fecha_registro
                FROM clientes
                WHERE cedula = %s
            """
            cursor.execute(query, (cedula,))
            result = cursor.fetchone()
            cursor.close()

            # Convertir Decimal a float para JSON serialización
            if result and 'saldo' in result:
                result['saldo'] = float(result['saldo'])

            return result

    def actualizar_saldo(self, cedula, nuevo_saldo):
        """
        Actualiza el saldo de un cliente

        Args:
            cedula: cédula del cliente
            nuevo_saldo: nuevo saldo a establecer
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                UPDATE clientes
                SET saldo = %s
                WHERE cedula = %s
            """
            cursor.execute(query, (nuevo_saldo, cedula))
            conn.commit()
            cursor.close()

    def insertar_transaccion(self, cedula, tipo, monto, saldo_final):
        """
        Registra una transacción en el historial

        Args:
            cedula: cédula del cliente
            tipo: 'DEPOSITO' o 'RETIRO'
            monto: monto de la transacción
            saldo_final: saldo después de la transacción
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                INSERT INTO transacciones (cedula, tipo, monto, saldo_final)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (cedula, tipo, monto, saldo_final))
            conn.commit()
            cursor.close()

    def crear_cliente(self, cedula, nombres, apellidos, saldo_inicial):
        """
        Crea un nuevo cliente en la base de datos

        Args:
            cedula: cédula del cliente
            nombres: nombres del cliente
            apellidos: apellidos del cliente
            saldo_inicial: saldo inicial
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                INSERT INTO clientes (cedula, nombres, apellidos, saldo)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (cedula, nombres, apellidos, saldo_inicial))
            conn.commit()
            cursor.close()

    def obtener_historial(self, cedula, limite=10):
        """
        Obtiene el historial de transacciones de un cliente

        Args:
            cedula: cédula del cliente
            limite: número máximo de transacciones a retornar

        Returns:
            lista de diccionarios con las transacciones
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT tipo, monto, saldo_final, 
                       DATE_FORMAT(fecha, '%Y-%m-%d %H:%i:%S') as fecha
                FROM transacciones
                WHERE cedula = %s
                ORDER BY fecha DESC
                LIMIT %s
            """
            cursor.execute(query, (cedula, limite))
            results = cursor.fetchall()
            cursor.close()

            # Convertir Decimal a float para JSON serialización
            for row in results:
                if 'monto' in row:
                    row['monto'] = float(row['monto'])
                if 'saldo_final' in row:
                    row['saldo_final'] = float(row['saldo_final'])

            return results

    def close(self):
        """Cierra todas las conexiones del pool"""
        if self.connection_pool:
            logging.info("🔒 Cerrando pool de conexiones...")
