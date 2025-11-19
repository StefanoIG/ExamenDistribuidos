-- Script para actualizar la base de datos y agregar soporte de transferencias
-- Ejecutar este script si ya tienes la base de datos creada

USE examen;

-- Modificar el ENUM de la tabla transacciones para incluir transferencias
ALTER TABLE transacciones 
MODIFY COLUMN tipo ENUM('DEPOSITO', 'RETIRO', 'TRANSFERENCIA_ENVIADA', 'TRANSFERENCIA_RECIBIDA') NOT NULL;

-- Verificar el cambio
DESCRIBE transacciones;

SELECT 'Base de datos actualizada exitosamente. Ahora soporta transferencias.' AS Mensaje;
