# Configuración de Seguridad - VM Frontend
## IP Pública: 20.163.61.241

## Reglas de Entrada (Inbound) Necesarias

### Regla 1: SSH (Puerto 22)
- **Nombre:** Allow-SSH
- **Prioridad:** 300
- **Puerto:** 22
- **Protocolo:** TCP
- **Origen:** IP de tu casa/trabajo (para seguridad) o * (menos seguro)
- **Destino:** * 
- **Acción:** Permitir
- **Descripción:** Acceso SSH para administración

### Regla 2: HTTP (Puerto 80)
- **Nombre:** Allow-HTTP
- **Prioridad:** 310
- **Puerto:** 80
- **Protocolo:** TCP
- **Origen:** Internet (*) o "Service Tag: Internet"
- **Destino:** *
- **Acción:** Permitir
- **Descripción:** Acceso HTTP para usuarios del frontend

### Regla 3: HTTPS (Puerto 443) - Opcional para futuro
- **Nombre:** Allow-HTTPS
- **Prioridad:** 320
- **Puerto:** 443
- **Protocolo:** TCP
- **Origen:** Internet (*)
- **Destino:** *
- **Acción:** Permitir
- **Descripción:** Acceso HTTPS para futuro con SSL

## Reglas de Salida (Outbound) Necesarias

### Regla 1: HTTP al Backend (Puerto 80)
- **Nombre:** Allow-Backend-HTTP
- **Prioridad:** 300
- **Puerto:** 80
- **Protocolo:** TCP
- **Origen:** *
- **Destino:** 135.234.27.161/32
- **Acción:** Permitir
- **Descripción:** Comunicación con VM Backend

### Regla 2: Internet (Puertos 80, 443)
- **Nombre:** Allow-Internet
- **Prioridad:** 310
- **Puerto:** 80,443
- **Protocolo:** TCP
- **Origen:** *
- **Destino:** Internet
- **Acción:** Permitir
- **Descripción:** Descargas de npm, pnpm, actualizaciones

### Regla 3: DNS (Puerto 53) - Ya viene por defecto
- **Nombre:** Allow-DNS
- **Prioridad:** 320
- **Puerto:** 53
- **Protocolo:** UDP
- **Origen:** *
- **Destino:** *
- **Acción:** Permitir
- **Descripción:** Resolución de nombres

## Pasos para configurar en Azure Portal

1. **Ir a la VM Frontend** → Redes → Grupo de seguridad de red: `FrontDistri-nsg`

2. **Configurar Reglas de Entrada:**
   - Click en "Reglas de seguridad de entrada"
   - Click en "+ Agregar"
   - Configurar cada regla según arriba

3. **Configurar Reglas de Salida:**
   - Click en "Reglas de seguridad de salida"
   - Click en "+ Agregar"
   - Configurar cada regla según arriba

## Verificación de conectividad

### Desde tu máquina local (Windows):
```powershell
# Probar SSH (debe funcionar después de configurar regla)
ssh azureuser@20.163.61.241

# Probar HTTP (después de instalar Nginx)
curl http://20.163.61.241/health
```

### Desde VM Backend debe poder conectarse a Frontend:
```bash
# Ping a IP privada (más rápido, sin costo de salida de Azure)
ping 172.19.0.4

# O a IP pública
curl http://20.163.61.241
```

## IMPORTANTE: Actualizar Backend para aceptar Frontend

En **VM Backend (135.234.27.161)**, editar `.env`:

```bash
# Conectar a VM Backend vía Consola Serie
nano ~/ExamenDistribuidos/.env
```

Cambiar línea CORS_ORIGINS:
```dotenv
CORS_ORIGINS=http://20.163.61.241,http://localhost:3000
```

Reiniciar servicios:
```bash
sudo supervisorctl restart all
```

## Actualizar .env.production del Frontend

El archivo `.env.production` debe tener:
```dotenv
# Usar IP PRIVADA del backend si están en la misma VNet (más rápido)
NEXT_PUBLIC_API_URL=http://135.234.27.161/api
NEXT_PUBLIC_WS_URL=http://135.234.27.161

# O si prefieres usar IP pública:
# NEXT_PUBLIC_API_URL=http://135.234.27.161/api
# NEXT_PUBLIC_WS_URL=http://135.234.27.161
```

## Comandos de verificación

```bash
# En VM Frontend, verificar conectividad al backend
curl http://135.234.27.161/health

# Verificar que Next.js está corriendo
curl http://localhost:3000

# Verificar que Nginx está corriendo
curl http://localhost/health

# Ver puertos abiertos
sudo netstat -tulpn | grep -E ':(80|3000)'
```

## Acceso Final

Una vez configurado todo:
- **Frontend:** http://20.163.61.241
- **Backend API:** http://135.234.27.161/api
- **Base de Datos:** 20.163.61.202:3306 (solo accesible desde Backend)

## Seguridad Mejorada (Opcional)

Para mayor seguridad, puedes:

1. **Restringir SSH solo a tu IP:**
   - Origen: [Tu IP Pública] en lugar de *

2. **Usar IP Privada para comunicación Backend-Frontend:**
   - Frontend usa `http://172.19.0.X` (IP privada del backend)
   - No sale a Internet, más rápido y seguro
   - Requiere que estén en la misma VNet

3. **Crear NSG Rules más específicas:**
   - Denegar todo por defecto
   - Permitir solo lo necesario
