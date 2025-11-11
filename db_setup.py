"""
Script de Configuración de Base de Datos
Crea BD, tablas (clientes + transacciones), índices y datos de ejemplo
Soporta MySQL 8.0+ y MariaDB 10.5+
"""

import mysql.connector
from mysql.connector import Error
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('setup.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class DatabaseSetup:
    """Configura la base de datos completa del sistema"""

    def __init__(self, host='localhost', port=3306, user='root', password='010304'):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db_name = 'examen'

    def get_connection(self, database=None):
        """Obtiene una conexión a MySQL"""
        try:
            config = {
                'host': self.host,
                'port': self.port,
                'user': self.user,
                'password': self.password,
                'autocommit': False
            }
            if database:
                config['database'] = database

            return mysql.connector.connect(**config)
        except Error as e:
            logging.error(f"❌ Error de conexión: {e}")
            raise

    def create_database(self):
        """Crea la base de datos si no existe"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Crear base de datos
            create_db_query = f"""
                CREATE DATABASE IF NOT EXISTS {self.db_name}
                CHARACTER SET utf8mb4
                COLLATE utf8mb4_unicode_ci
            """
            cursor.execute(create_db_query)
            logging.info(f"✅ Base de datos '{self.db_name}' lista")

            cursor.close()
            conn.close()

        except Error as e:
            logging.error(f"❌ Error creando base de datos: {e}")
            raise

    def create_tables(self):
        """Crea tablas clientes y transacciones con sus relaciones"""
        try:
            conn = self.get_connection(self.db_name)
            cursor = conn.cursor()

            # Tabla de clientes
            create_clientes = """
            CREATE TABLE IF NOT EXISTS clientes (
                cedula VARCHAR(15) PRIMARY KEY,
                nombres VARCHAR(100) NOT NULL,
                apellidos VARCHAR(100) NOT NULL,
                saldo DECIMAL(10, 2) DEFAULT 0.00 CHECK (saldo >= 0),
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_cedula (cedula),
                INDEX idx_saldo (saldo)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """

            # Tabla de transacciones
            create_transacciones = """
            CREATE TABLE IF NOT EXISTS transacciones (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cedula VARCHAR(15) NOT NULL,
                tipo ENUM('DEPOSITO', 'RETIRO') NOT NULL,
                monto DECIMAL(10, 2) NOT NULL CHECK (monto > 0),
                saldo_final DECIMAL(10, 2) NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cedula) REFERENCES clientes(cedula) ON DELETE CASCADE,
                INDEX idx_cedula (cedula),
                INDEX idx_fecha (fecha DESC),
                INDEX idx_tipo (tipo)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """

            cursor.execute(create_clientes)
            logging.info("✅ Tabla 'clientes' creada")

            cursor.execute(create_transacciones)
            logging.info("✅ Tabla 'transacciones' creada")

            conn.commit()
            cursor.close()
            conn.close()

        except Error as e:
            logging.error(f"❌ Error creando tablas: {e}")
            raise

    def insert_sample_data(self):
        """Inserta datos de ejemplo con transacciones"""
        try:
            conn = self.get_connection(self.db_name)
            cursor = conn.cursor()

            # Clientes de ejemplo
            sample_clients = [
                ('1315151515', 'Juan', 'Pérez García', 1500.00),
                ('1720304050', 'María Elena', 'Rodríguez López', 2350.75),
                ('0987654321', 'Pedro José', 'Martínez Silva', 890.50),
                ('1104567890', 'Ana María', 'González Torres', 3200.00),
                ('0912345678', 'Luis Alberto', 'Fernández Ruiz', 450.25),
                ('1350509525', 'Stefano', 'Aguilar', 5000.00),  # Administrador
            ]

            insert_client_query = """
                INSERT IGNORE INTO clientes (cedula, nombres, apellidos, saldo)
                VALUES (%s, %s, %s, %s)
            """

            cursor.executemany(insert_client_query, sample_clients)
            rows_inserted = cursor.rowcount
            logging.info(f"✅ {rows_inserted} clientes insertados")

            # Transacciones de ejemplo para algunos clientes
            sample_transactions = [
                ('1315151515', 'DEPOSITO', 500.00, 1500.00),
                ('1315151515', 'RETIRO', 200.00, 1300.00),
                ('1315151515', 'DEPOSITO', 200.00, 1500.00),
                ('1720304050', 'DEPOSITO', 1000.00, 2350.75),
                ('0987654321', 'RETIRO', 100.00, 790.50),
                ('1104567890', 'DEPOSITO', 3200.00, 3200.00),
            ]

            insert_tx_query = """
                INSERT INTO transacciones (cedula, tipo, monto, saldo_final)
                VALUES (%s, %s, %s, %s)
            """

            cursor.executemany(insert_tx_query, sample_transactions)
            tx_inserted = cursor.rowcount
            logging.info(f"✅ {tx_inserted} transacciones de ejemplo insertadas")

            conn.commit()
            cursor.close()
            conn.close()

        except Error as e:
            logging.error(f"❌ Error insertando datos de ejemplo: {e}")
            raise

    def show_sample_data(self):
        """Muestra los datos de ejemplo creados"""
        try:
            conn = self.get_connection(self.db_name)
            cursor = conn.cursor(dictionary=True)

            print("\n" + "=" * 80)
            print("📊 CLIENTES EN LA BASE DE DATOS")
            print("=" * 80)

            cursor.execute("""
                SELECT cedula, nombres, apellidos, saldo, 
                       DATE_FORMAT(fecha_registro, '%Y-%m-%d %H:%i:%S') as fecha
                FROM clientes
                ORDER BY cedula
            """)

            clientes = cursor.fetchall()

            for cliente in clientes:
                print(f"Cédula: {cliente['cedula']}")
                print(f"  Nombre: {cliente['nombres']} {cliente['apellidos']}")
                print(f"  Saldo: ${cliente['saldo']:,.2f}")
                print(f"  Registrado: {cliente['fecha']}")
                print("-" * 80)

            # Mostrar total de transacciones
            cursor.execute("SELECT COUNT(*) as total FROM transacciones")
            total_tx = cursor.fetchone()['total']
            print(f"\n📝 Total de transacciones registradas: {total_tx}")

            # Mostrar últimas transacciones
            print("\n" + "=" * 80)
            print("📋 ÚLTIMAS TRANSACCIONES")
            print("=" * 80)

            cursor.execute("""
                SELECT cedula, tipo, monto, saldo_final,
                       DATE_FORMAT(fecha, '%Y-%m-%d %H:%i:%S') as fecha
                FROM transacciones
                ORDER BY fecha DESC
                LIMIT 10
            """)

            transacciones = cursor.fetchall()
            for tx in transacciones:
                print(f"[{tx['fecha']}] {tx['tipo']:8} - ${tx['monto']:8.2f} | Saldo final: ${tx['saldo_final']:.2f} | Cédula: {tx['cedula']}")

            cursor.close()
            conn.close()

        except Error as e:
            logging.error(f"❌ Error mostrando datos: {e}")

    def test_connection(self):
        """Prueba la conexión y muestra estadísticas"""
        try:
            conn = self.get_connection(self.db_name)
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT COUNT(*) as total FROM clientes")
            count_clients = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as total FROM transacciones")
            count_tx = cursor.fetchone()['total']

            logging.info(f"✅ Conexión exitosa")
            logging.info(f"📊 Clientes: {count_clients} | Transacciones: {count_tx}")

            cursor.close()
            conn.close()
            return True

        except Error as e:
            logging.error(f"❌ Error probando conexión: {e}")
            return False

    def setup(self, insert_samples=True):
        """Ejecuta el setup completo"""
        print("\n" + "=" * 80)
        print("🚀 CONFIGURACIÓN DE BASE DE DATOS - SISTEMA BANCARIO DISTRIBUIDO")
        print("=" * 80 + "\n")

        print("📦 Creando base de datos...")
        self.create_database()

        print("📋 Creando tablas...")
        self.create_tables()

        if insert_samples:
            print("📝 Insertando datos de ejemplo...")
            self.insert_sample_data()
            self.show_sample_data()

        print("\n" + "=" * 80)
        print("✅ CONFIGURACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    # Cargar configuración desde .env si existe
    load_dotenv()

    print("=" * 80)
    print("CONFIGURACIÓN DE BASE DE DATOS - MYSQL")
    print("=" * 80 + "\n")

    # Obtener configuración
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # Si no hay password en .env, solicitarla
    if not DB_PASSWORD:
        import getpass
        DB_PASSWORD = getpass.getpass("Ingresa la contraseña de MySQL (Enter para sin contraseña): ")

    setup = DatabaseSetup(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD
    )

    try:
        # Ejecutar setup completo
        setup.setup(insert_samples=True)

        # Probar conexión
        print("\n🔍 Verificando conexión...")
        if setup.test_connection():
            print("\n✅ Todo listo para iniciar el servidor\n")
            print("📋 Comandos disponibles para el cliente:")
            print("   • CONSULTA <cedula>")
            print("   • AUMENTAR <cedula> <monto>")
            print("   • DISMINUIR <cedula> <monto>")
            print("   • CREAR <cedula> <nombres> <apellidos> <saldo>")
            print("   • HISTORIAL <cedula>")
            print("   • STATS")
            print("   • SALIR\n")

    except Exception as e:
        print(f"\n❌ Error durante el setup: {e}")
        print("\n💡 Verifica que MySQL esté instalado y ejecutándose")