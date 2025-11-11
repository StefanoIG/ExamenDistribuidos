"""
Cliente Socket para probar el Servidor Bancario Distribuido
Envía comandos y recibe respuestas del servidor
"""

import socket
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)


class SocketClient:
    """Cliente socket para comunicarse con el servidor bancario"""

    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        """Conecta con el servidor"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            logging.info(f"✅ Conectado a {self.host}:{self.port}")

            # Recibir mensaje de bienvenida
            welcome = self.socket.recv(1024).decode('utf-8')
            print(f"\n{welcome}")
            return True

        except Exception as e:
            logging.error(f"❌ Error conectando: {e}")
            return False

    def send_command(self, comando):
        """Envía un comando al servidor y recibe la respuesta"""
        try:
            self.socket.send(comando.encode('utf-8'))
            response = self.socket.recv(4096).decode('utf-8')
            return response
        except Exception as e:
            logging.error(f"❌ Error enviando comando: {e}")
            return f"ERROR|{str(e)}"

    def close(self):
        """Cierra la conexión"""
        if self.socket:
            self.socket.close()
            logging.info("Desconectado del servidor")

    def interactive_shell(self):
        """Inicia un shell interactivo para enviar comandos"""
        print("\n" + "=" * 70)
        print("🏦 CLIENTE DEL SISTEMA BANCARIO DISTRIBUIDO")
        print("=" * 70)
        print("\nComandos disponibles:")
        print("  • CONSULTA <cedula>")
        print("  • AUMENTAR <cedula> <monto>")
        print("  • DISMINUIR <cedula> <monto>")
        print("  • CREAR <cedula> <nombres> <apellidos> <saldo>")
        print("  • HISTORIAL <cedula>")
        print("  • STATS")
        print("  • SALIR")
        print("=" * 70 + "\n")

        while True:
            try:
                comando = input("📥 Ingresa comando: ").strip()

                if not comando:
                    continue

                print(f"\n📤 Enviando: {comando}")
                respuesta = self.send_command(comando)

                # Parsear y mostrar respuesta
                self.mostrar_respuesta(respuesta)

                if comando.upper() == 'SALIR':
                    break

            except KeyboardInterrupt:
                print("\n\n⚠️ Interrupción del usuario")
                self.send_command('SALIR')
                break
            except Exception as e:
                logging.error(f"❌ Error: {e}")

    def mostrar_respuesta(self, respuesta):
        """Formatea y muestra la respuesta del servidor"""
        partes = respuesta.split('|')

        if partes[0] == 'OK':
            print(f"✅ Operación exitosa")

            if len(partes) > 1:
                if len(partes) == 4:  # CONSULTA
                    print(f"   Nombres: {partes[1]}")
                    print(f"   Apellidos: {partes[2]}")
                    print(f"   Saldo: ${partes[3]}")

                elif len(partes) == 3 and partes[1] in ['Depósito exitoso', 'Retiro exitoso']:
                    print(f"   {partes[1]}")
                    print(f"   Nuevo saldo: ${partes[2]}")

                elif len(partes) == 4 and partes[2] == 'Cliente creado exitosamente':
                    print(f"   {partes[2]}")
                    print(f"   Saldo inicial: ${partes[3]}")

                elif partes[1] == 'Sin transacciones':
                    print(f"   Sin transacciones registradas")

                elif 'Clientes conectados' in respuesta:
                    for parte in partes[1:]:
                        print(f"   {parte}")

                else:
                    # HISTORIAL o múltiples partes
                    print(f"   Historial de transacciones:")
                    print(f"   {'Tipo':<10} {'Monto':<12} {'Saldo Final':<12} {'Fecha':<20}")
                    print(f"   {'-'*54}")
                    for i in range(1, len(partes), 4):
                        if i + 3 < len(partes):
                            print(f"   {partes[i]:<10} ${partes[i+1]:<11} ${partes[i+2]:<11} {partes[i+3]:<20}")

        else:  # ERROR
            print(f"❌ Error: {partes[1] if len(partes) > 1 else respuesta}")
            if len(partes) > 2:
                print(f"   Detalles: {partes[2]}")

        print()


def test_automatico(client):
    """Ejecuta una serie de pruebas automáticas"""
    print("\n" + "=" * 70)
    print("🧪 PRUEBAS AUTOMÁTICAS")
    print("=" * 70 + "\n")

    pruebas = [
        ("CONSULTA 1315151515", "Consultar cliente existente"),
        ("CONSULTA 9999999999", "Consultar cliente inexistente"),
        ("AUMENTAR 1315151515 100", "Depósito a cliente"),
        ("DISMINUIR 1315151515 50", "Retiro de cliente"),
        ("DISMINUIR 1315151515 10000", "Retiro sin saldo suficiente"),
        ("CREAR 1234567890 Juan Pérez 500", "Crear nuevo cliente"),
        ("CONSULTA 1234567890", "Consultar nuevo cliente"),
        ("HISTORIAL 1315151515", "Ver historial de transacciones"),
        ("STATS", "Ver estadísticas del servidor"),
    ]

    for comando, descripcion in pruebas:
        print(f"🔹 {descripcion}")
        print(f"   Comando: {comando}")
        respuesta = client.send_command(comando)
        client.mostrar_respuesta(respuesta)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Cliente del Sistema Bancario')
    parser.add_argument('--host', default='localhost', help='Host del servidor')
    parser.add_argument('--port', type=int, default=5000, help='Puerto del servidor')
    parser.add_argument('--test', action='store_true', help='Ejecutar pruebas automáticas')

    args = parser.parse_args()

    client = SocketClient(args.host, args.port)

    if client.connect():
        if args.test:
            test_automatico(client)
        else:
            client.interactive_shell()
        client.close()
    else:
        print("\n❌ No se pudo conectar al servidor")
        sys.exit(1)
