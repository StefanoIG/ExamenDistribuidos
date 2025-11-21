"""
Prueba de Concurrencia del Sistema Bancario Distribuido
Este script demuestra cómo múltiples clientes pueden realizar operaciones
simultáneas (depósitos y retiros) sin conflictos gracias al sistema de locks.
"""

import socket
import threading
import time
import random
from datetime import datetime
import sys
from typing import Dict, Any, List

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class ConcurrencyTester:
    """Prueba de concurrencia con múltiples threads"""
    
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.resultados: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        
    def send_command(self, comando):
        """Envía un comando al servidor y retorna la respuesta"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            
            # Recibir bienvenida
            sock.recv(1024)
            
            # Enviar comando
            sock.send(comando.encode('utf-8'))
            response = sock.recv(4096).decode('utf-8')
            
            sock.close()
            return response
        except Exception as e:
            return f"ERROR|{str(e)}"
    
    def operacion_cliente(self, thread_id, cedula, operaciones):
        """Simula un cliente realizando múltiples operaciones"""
        nombre_thread = f"Thread-{thread_id}"
        
        for i, (tipo_op, monto) in enumerate(operaciones, 1):
            try:
                # Consultar saldo antes
                consulta_antes = self.send_command(f"CONSULTA {cedula}")
                
                # Realizar operación
                if tipo_op == "DEPOSITO":
                    comando = f"AUMENTAR {cedula} {monto}"
                    color = Colors.OKGREEN
                    simbolo = "💰"
                else:  # RETIRO
                    comando = f"DISMINUIR {cedula} {monto}"
                    color = Colors.WARNING
                    simbolo = "💸"
                
                inicio = time.time()
                respuesta = self.send_command(comando)
                duracion = (time.time() - inicio) * 1000  # en ms
                
                # Consultar saldo después
                consulta_despues = self.send_command(f"CONSULTA {cedula}")
                
                # Guardar resultado
                with self.lock:
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    self.resultados.append({
                        'thread': nombre_thread,
                        'cedula': cedula,
                        'operacion': tipo_op,
                        'monto': monto,
                        'timestamp': timestamp,
                        'duracion_ms': duracion,
                        'respuesta': respuesta
                    })
                    
                    print(f"{color}{simbolo} [{timestamp}] {nombre_thread} - "
                          f"{tipo_op} ${monto:.2f} en cédula {cedula} "
                          f"({duracion:.1f}ms){Colors.ENDC}")
                
                # Pequeña pausa aleatoria entre operaciones
                time.sleep(random.uniform(0.1, 0.3))
                
            except Exception as e:
                print(f"{Colors.FAIL}❌ Error en {nombre_thread}: {e}{Colors.ENDC}")
    
    def test_depositos_simultaneos(self):
        """Test 1: Múltiples depósitos simultáneos a la misma cuenta"""
        print(f"\n{Colors.HEADER}{'='*80}")
        print("🧪 TEST 1: DEPÓSITOS SIMULTÁNEOS A LA MISMA CUENTA")
        print(f"{'='*80}{Colors.ENDC}\n")
        
        cedula = "1315151515"  # Ana Torres
        num_threads = 5
        threads = []
        
        # Consultar saldo inicial
        print(f"{Colors.OKCYAN}📊 Consultando saldo inicial...{Colors.ENDC}")
        saldo_inicial = self.send_command(f"CONSULTA {cedula}")
        print(f"   {saldo_inicial}\n")
        
        print(f"{Colors.BOLD}🚀 Iniciando {num_threads} threads simultáneos...{Colors.ENDC}\n")
        
        # Cada thread hará 3 depósitos
        operaciones_por_thread = [("DEPOSITO", 50.00) for _ in range(3)]
        
        inicio_total = time.time()
        
        for i in range(num_threads):
            t = threading.Thread(
                target=self.operacion_cliente,
                args=(i+1, cedula, operaciones_por_thread)
            )
            threads.append(t)
            t.start()
        
        # Esperar a que todos terminen
        for t in threads:
            t.join()
        
        duracion_total = time.time() - inicio_total
        
        # Consultar saldo final
        print(f"\n{Colors.OKCYAN}📊 Consultando saldo final...{Colors.ENDC}")
        saldo_final = self.send_command(f"CONSULTA {cedula}")
        print(f"   {saldo_final}")
        
        total_depositado = num_threads * len(operaciones_por_thread) * 50.00
        print(f"\n{Colors.OKGREEN}✅ Test completado en {duracion_total:.2f}s")
        print(f"   Total depositado esperado: ${total_depositado:.2f}{Colors.ENDC}")
    
    def test_operaciones_mixtas(self):
        """Test 2: Depósitos y retiros simultáneos"""
        print(f"\n{Colors.HEADER}{'='*80}")
        print("🧪 TEST 2: OPERACIONES MIXTAS SIMULTÁNEAS (DEPÓSITOS + RETIROS)")
        print(f"{'='*80}{Colors.ENDC}\n")
        
        cedula = "1350509525"  # Stefano Aguilar (Admin)
        num_threads = 6
        threads = []
        
        # Consultar saldo inicial
        print(f"{Colors.OKCYAN}📊 Consultando saldo inicial...{Colors.ENDC}")
        saldo_inicial = self.send_command(f"CONSULTA {cedula}")
        print(f"   {saldo_inicial}\n")
        
        print(f"{Colors.BOLD}🚀 Iniciando {num_threads} threads simultáneos...{Colors.ENDC}\n")
        
        inicio_total = time.time()
        
        # Threads con depósitos
        for i in range(3):
            operaciones = [("DEPOSITO", random.uniform(20, 100)) for _ in range(2)]
            t = threading.Thread(
                target=self.operacion_cliente,
                args=(i+1, cedula, operaciones)
            )
            threads.append(t)
            t.start()
        
        # Threads con retiros
        for i in range(3):
            operaciones = [("RETIRO", random.uniform(10, 50)) for _ in range(2)]
            t = threading.Thread(
                target=self.operacion_cliente,
                args=(i+4, cedula, operaciones)
            )
            threads.append(t)
            t.start()
        
        # Esperar a que todos terminen
        for t in threads:
            t.join()
        
        duracion_total = time.time() - inicio_total
        
        # Consultar saldo final
        print(f"\n{Colors.OKCYAN}📊 Consultando saldo final...{Colors.ENDC}")
        saldo_final = self.send_command(f"CONSULTA {cedula}")
        print(f"   {saldo_final}")
        
        print(f"\n{Colors.OKGREEN}✅ Test completado en {duracion_total:.2f}s{Colors.ENDC}")
    
    def test_multiples_cuentas(self):
        """Test 3: Operaciones simultáneas en múltiples cuentas diferentes"""
        print(f"\n{Colors.HEADER}{'='*80}")
        print("🧪 TEST 3: OPERACIONES SIMULTÁNEAS EN MÚLTIPLES CUENTAS")
        print(f"{'='*80}{Colors.ENDC}\n")
        
        cuentas = [
            "1315151515",  # Ana Torres
            "1350509525",  # Stefano Aguilar (Admin)
            "1214141414",  # Carlos Rodríguez
            "1416161616",  # Laura Sánchez
        ]
        
        threads = []
        
        print(f"{Colors.OKCYAN}📊 Consultando saldos iniciales...{Colors.ENDC}")
        for cedula in cuentas:
            saldo = self.send_command(f"CONSULTA {cedula}")
            print(f"   {saldo}")
        
        print(f"\n{Colors.BOLD}🚀 Iniciando operaciones en {len(cuentas)} cuentas simultáneamente...{Colors.ENDC}\n")
        
        inicio_total = time.time()
        
        thread_id = 1
        for cedula in cuentas:
            # Cada cuenta tendrá 2 threads: uno depositando y otro retirando
            
            # Thread de depósitos
            operaciones_dep = [("DEPOSITO", random.uniform(30, 100)) for _ in range(3)]
            t_dep = threading.Thread(
                target=self.operacion_cliente,
                args=(thread_id, cedula, operaciones_dep)
            )
            threads.append(t_dep)
            t_dep.start()
            thread_id += 1
            
            # Thread de retiros
            operaciones_ret = [("RETIRO", random.uniform(10, 40)) for _ in range(2)]
            t_ret = threading.Thread(
                target=self.operacion_cliente,
                args=(thread_id, cedula, operaciones_ret)
            )
            threads.append(t_ret)
            t_ret.start()
            thread_id += 1
        
        # Esperar a que todos terminen
        for t in threads:
            t.join()
        
        duracion_total = time.time() - inicio_total
        
        # Consultar saldos finales
        print(f"\n{Colors.OKCYAN}📊 Consultando saldos finales...{Colors.ENDC}")
        for cedula in cuentas:
            saldo = self.send_command(f"CONSULTA {cedula}")
            print(f"   {saldo}")
        
        print(f"\n{Colors.OKGREEN}✅ Test completado en {duracion_total:.2f}s")
        print(f"   Total de threads: {len(threads)}{Colors.ENDC}")
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Calcula un resumen estadístico de las operaciones registradas."""
        if not self.resultados:
            return {
                'total_operaciones': 0,
                'depositos': 0,
                'retiros': 0,
                'tiempos_ms': {
                    'promedio': 0.0,
                    'minimo': 0.0,
                    'maximo': 0.0,
                },
                'errores': 0,
            }

        total_ops = len(self.resultados)
        depositos = sum(1 for r in self.resultados if r['operacion'] == 'DEPOSITO')
        retiros = total_ops - depositos

        tiempos = [r['duracion_ms'] for r in self.resultados]
        tiempo_promedio = sum(tiempos) / len(tiempos)
        tiempo_min = min(tiempos)
        tiempo_max = max(tiempos)

        errores = sum(1 for r in self.resultados if 'ERROR' in r['respuesta'])

        return {
            'total_operaciones': total_ops,
            'depositos': depositos,
            'retiros': retiros,
            'tiempos_ms': {
                'promedio': tiempo_promedio,
                'minimo': tiempo_min,
                'maximo': tiempo_max,
            },
            'errores': errores,
        }

    def mostrar_estadisticas(self):
        """Muestra estadísticas de las pruebas"""
        print(f"\n{Colors.HEADER}{'='*80}")
        print("📈 ESTADÍSTICAS DE CONCURRENCIA")
        print(f"{'='*80}{Colors.ENDC}\n")

        stats = self.obtener_estadisticas()
        if stats['total_operaciones'] == 0:
            print("No hay resultados para mostrar")
            return

        print(f"{Colors.OKBLUE}📊 Resumen de Operaciones:{Colors.ENDC}")
        print(f"   Total de operaciones: {stats['total_operaciones']}")
        print(f"   Depósitos: {stats['depositos']}")
        print(f"   Retiros: {stats['retiros']}")

        tiempos = stats['tiempos_ms']
        print(f"\n{Colors.OKBLUE}⏱️  Tiempos de Respuesta:{Colors.ENDC}")
        print(f"   Promedio: {tiempos['promedio']:.2f}ms")
        print(f"   Mínimo: {tiempos['minimo']:.2f}ms")
        print(f"   Máximo: {tiempos['maximo']:.2f}ms")

        if stats['errores'] == 0:
            print(f"\n{Colors.OKGREEN}✅ Todas las operaciones se completaron sin errores{Colors.ENDC}")
        else:
            print(f"\n{Colors.FAIL}❌ {stats['errores']} operaciones fallaron{Colors.ENDC}")


def run_concurrency_demo() -> Dict[str, Any]:
    """Ejecuta la demostración de concurrencia y retorna los resultados en un diccionario."""
    tester = ConcurrencyTester()

    try:
        test_response = tester.send_command("STATS")
        if not test_response or not test_response.startswith("OK"):
            return {
                'success': False,
                'error': f'No se pudo conectar al servidor de sockets: {test_response}',
            }

        tester.test_depositos_simultaneos()
        time.sleep(1)

        tester.test_operaciones_mixtas()
        time.sleep(1)

        tester.test_multiples_cuentas()
        time.sleep(1)

        tester.mostrar_estadisticas()
        summary = tester.obtener_estadisticas()

        return {
            'success': True,
            'summary': summary,
            'operations': tester.resultados,
        }

    except Exception as exc:  # pylint: disable=broad-except
        return {
            'success': False,
            'error': str(exc),
        }


def main():
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("╔═══════════════════════════════════════════════════════════════════════════╗")
    print("║         PRUEBA DE CONCURRENCIA - SISTEMA BANCARIO DISTRIBUIDO            ║")
    print("╚═══════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    
    tester = ConcurrencyTester()
    
    try:
        # Verificar conexión
        print(f"{Colors.OKCYAN}🔍 Verificando conexión con el servidor...{Colors.ENDC}")
        test_response = tester.send_command("STATS")
        if "ERROR" in test_response:
            print(f"{Colors.FAIL}❌ No se pudo conectar al servidor en localhost:5000{Colors.ENDC}")
            print(f"   Asegúrate de que el servidor esté ejecutándose")
            sys.exit(1)
        print(f"{Colors.OKGREEN}✅ Conexión exitosa{Colors.ENDC}")
        
        # Ejecutar tests
        tester.test_depositos_simultaneos()
        time.sleep(1)
        
        tester.test_operaciones_mixtas()
        time.sleep(1)
        
        tester.test_multiples_cuentas()
        time.sleep(1)
        
        # Mostrar estadísticas finales
        tester.mostrar_estadisticas()
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}{'='*80}")
        print("✅ TODAS LAS PRUEBAS DE CONCURRENCIA COMPLETADAS")
        print(f"{'='*80}{Colors.ENDC}\n")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}⚠️  Pruebas interrumpidas por el usuario{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Error durante las pruebas: {e}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
