"""
Script para actualizar la base de datos con soporte de transferencias
"""
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def update_database():
    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'socketuser'),
            password=os.getenv('DB_PASSWORD', '12345'),
            database=os.getenv('DB_NAME', 'examen')
        )
        
        cursor = conn.cursor()
        
        print("🔄 Actualizando tabla transacciones...")
        
        # Modificar el ENUM para incluir transferencias
        alter_query = """
        ALTER TABLE transacciones 
        MODIFY COLUMN tipo ENUM(
            'DEPOSITO', 
            'RETIRO', 
            'TRANSFERENCIA_ENVIADA', 
            'TRANSFERENCIA_RECIBIDA'
        ) NOT NULL
        """
        
        cursor.execute(alter_query)
        conn.commit()
        
        print("✅ Tabla transacciones actualizada exitosamente")
        
        # Verificar la estructura
        cursor.execute("DESCRIBE transacciones")
        print("\n📊 Estructura actual de la tabla transacciones:")
        print("-" * 80)
        for row in cursor.fetchall():
            print(f"  {row[0]:<15} {row[1]:<50} {row[2]:<5} {row[3]:<5} {row[4] or '':<10} {row[5] or '':<20}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Base de datos actualizada correctamente")
        print("🚀 Ahora puedes usar las funcionalidades de transferencia")
        
    except mysql.connector.Error as e:
        print(f"❌ Error al actualizar la base de datos: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 80)
    print("🔧 Actualización de Base de Datos - Sistema Bancario")
    print("=" * 80)
    print()
    
    success = update_database()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ ACTUALIZACIÓN COMPLETADA")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ ERROR EN LA ACTUALIZACIÓN")
        print("=" * 80)
