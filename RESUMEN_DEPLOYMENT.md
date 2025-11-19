# 🎯 RESUMEN EJECUTIVO - DEPLOYMENT A PRODUCCIÓN

**Sistema Bancario Distribuido v2.0**  
**Última actualización:** 19 Noviembre 2025  
**Incluye:** Transferencias + Alertas Visuales + Bug Fixes (Decimal)

---

## 📌 TL;DR - Pasos Rápidos

### ⏱️ Tiempo Total: ~2 horas

1. **Azure MySQL** (20 min) → Crear DB + Configurar Firewall + Crear Tablas
2. **Azure VM** (30 min) → Crear VM + SSH + Instalar Dependencias
3. **Backend Deploy** (40 min) → Clonar Repo + Configurar + Supervisor + Nginx
4. **Frontend Deploy** (20 min) → Netlify + Variables + Build
5. **Testing** (10 min) → Verificar todas las funcionalidades

---

## ✅ ORDEN CORRECTO DE DEPLOYMENT

### 1️⃣ PRIMERO: Base de Datos Azure MySQL

**¿Por qué primero?**
- Backend necesita conectarse a la DB
- Sin DB, nada funciona
- Toma tiempo aprovisionar (5-10 min)

**Pasos:**
```
Azure Portal → Create MySQL Flexible Server
→ Configurar firewall
→ Crear base de datos "examen"
→ Ejecutar scripts SQL de tablas
→ Anotar credenciales
```

**Resultado esperado:**
- Host: `examen-db.mysql.database.azure.com`
- User: `adminuser`
- Pass: `tu_password_seguro`
- DB: `examen`

---

### 2️⃣ SEGUNDO: Máquina Virtual Azure

**¿Por qué segundo?**
- Necesitas un lugar donde correr el backend
- VM necesita tiempo de aprovisionamiento
- Configurar networking antes de instalar código

**Pasos:**
```
Azure Portal → Create VM Ubuntu 22.04
→ Descargar clave SSH
→ Configurar NSG (puertos 22, 80, 5000, 5001)
→ Obtener IP pública
→ Conectar por SSH
```

**Resultado esperado:**
- IP Pública: `20.185.XXX.XXX`
- SSH: `ssh -i clave.pem azureuser@IP`

---

### 3️⃣ TERCERO: Backend en VM

**¿Por qué tercero?**
- Ya tienes DB funcionando
- Ya tienes VM accesible
- Ahora puedes configurar la conexión

**Pasos:**
```bash
# En la VM:
git clone https://github.com/TU_USER/ExamenDistribuidos.git
cd ExamenDistribuidos
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar
cp .env.production .env
nano .env  # Editar con credenciales reales

# Inicializar DB
python db_setup.py
python update_database.py

# Auto-inicio con Supervisor
sudo cp config/supervisor/*.conf /etc/supervisor/conf.d/
sudo supervisorctl reread && sudo supervisorctl update
sudo supervisorctl start all

# Proxy con Nginx
sudo cp config/nginx/backend /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/backend /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

**Resultado esperado:**
- `curl http://localhost/api/stats` retorna JSON
- `sudo supervisorctl status` muestra RUNNING

---

### 4️⃣ CUARTO: Frontend en Netlify

**¿Por qué cuarto?**
- Backend ya está corriendo
- Tienes IP pública para configurar variables
- Frontend se conectará a backend existente

**Pasos:**
```bash
# Local:
cd Frontend
nano .env.production

# Agregar:
NEXT_PUBLIC_API_URL=http://TU_IP_PUBLICA
NEXT_PUBLIC_WS_URL=http://TU_IP_PUBLICA

# Test build
pnpm build

# Push a GitHub
git add .
git commit -m "chore: production config"
git push origin main

# Netlify:
# → Import from GitHub
# → Seleccionar repo
# → Base dir: Frontend
# → Build: pnpm build
# → Publish: Frontend/.next
# → Variables: NEXT_PUBLIC_API_URL, NEXT_PUBLIC_WS_URL
# → Deploy
```

**Resultado esperado:**
- URL: `https://random-name.netlify.app`
- Build exitoso
- App carga sin errores

---

### 5️⃣ QUINTO: Actualizar CORS

**¿Por qué quinto?**
- Ya tienes URL de Netlify
- Backend necesita permitir requests desde Netlify

**Pasos:**
```bash
# SSH a VM
ssh -i clave.pem azureuser@IP

# Editar .env
cd ~/ExamenDistribuidos
nano .env

# Actualizar línea:
CORS_ORIGINS=https://tu-app.netlify.app,http://localhost:3000

# Reiniciar
sudo supervisorctl restart bridge
```

**Resultado esperado:**
- Frontend puede llamar API sin errores CORS

---

## 🧪 VERIFICACIÓN PASO A PASO

### Después de cada paso:

**1. MySQL:**
```bash
# Test de conexión
mysql -h HOST -u USER -p
> SHOW DATABASES;
> USE examen;
> SHOW TABLES;
> SELECT * FROM clientes;
```

**2. VM:**
```bash
# Test SSH
ssh -i clave.pem azureuser@IP
azureuser@vm:~$  # ✅ Conectado
```

**3. Backend:**
```bash
# Test services
sudo supervisorctl status
# socket_server    RUNNING  ✅
# bridge           RUNNING  ✅

# Test API
curl http://localhost/api/stats
# {"success": true, ...}  ✅
```

**4. Frontend:**
```
Navegador → https://tu-app.netlify.app
Login con: 1234567890
Dashboard carga ✅
```

**5. CORS:**
```javascript
// Consola del navegador (F12)
// NO debe aparecer:
// ❌ CORS policy error
// ✅ Requests 200 OK
```

---

## 🔥 PROBLEMAS COMUNES Y SOLUCIONES

### ❌ "Can't connect to MySQL server"

**Causa:** Firewall de Azure bloqueando conexión

**Solución:**
```
Azure Portal → MySQL Server → Networking
→ Add firewall rule
→ Name: AllowVM
→ Start IP: IP de tu VM
→ End IP: IP de tu VM
→ Save
```

---

### ❌ "Decimal is not JSON serializable"

**Causa:** Código antiguo sin las correcciones

**Solución:**
```bash
# Verificar que tienes las correcciones:
cd ~/ExamenDistribuidos
grep "float(row\['monto'\])" db_connection.py

# Si no aparece, hacer pull del repo actualizado:
git pull origin main
sudo supervisorctl restart all
```

---

### ❌ "CORS policy: No 'Access-Control-Allow-Origin'"

**Causa:** URL de Netlify no está en CORS_ORIGINS

**Solución:**
```bash
# En la VM:
nano ~/ExamenDistribuidos/.env

# Agregar URL de Netlify:
CORS_ORIGINS=https://tu-app.netlify.app

# Reiniciar:
sudo supervisorctl restart bridge
```

---

### ❌ Frontend: "Failed to fetch" o "Network Error"

**Causa 1:** Variables de entorno incorrectas en Netlify

**Solución:**
```
Netlify → Site settings → Environment variables
→ Verificar NEXT_PUBLIC_API_URL tiene IP correcta
→ Re-deploy si cambias variables
```

**Causa 2:** Puertos cerrados en Azure NSG

**Solución:**
```
Azure Portal → VM → Networking → NSG
→ Add inbound rule
→ Port 80, 5000, 5001: Allow from Any
→ Save
```

---

### ❌ WebSocket no funciona

**Causa:** Nginx no configurado para WebSocket

**Solución:**
```bash
# Verificar config Nginx:
sudo nano /etc/nginx/sites-available/backend

# Debe tener:
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";

# Reiniciar:
sudo systemctl restart nginx
```

---

## 📊 ARQUITECTURA FINAL

```
[Usuario Browser]
      ↓
[Netlify CDN] → Frontend Next.js
      ↓ HTTP/WS
[Azure VM] 
  ├─ Nginx (Puerto 80) → Proxy
  ├─ Flask Bridge (5001) → REST API + WebSocket
  └─ Socket Server (5000) → Lógica de negocio
      ↓ MySQL Protocol
[Azure MySQL] → Base de datos
  ├─ clientes
  └─ transacciones (con TRANSFERENCIA_ENVIADA/RECIBIDA)
```

---

## 📝 ARCHIVOS CRÍTICOS CON CAMBIOS

### Backend (todos en la VM):

1. **db_connection.py**
   - ✅ Corrección: `float(row['monto'])` en `obtener_historial`
   - ✅ Corrección: `float(result['saldo'])` en `consultar_cliente`
   - **Sin esto:** Error "Decimal not serializable"

2. **socket_server.py**
   - ✅ Soporte comando: `CREAR <cedula> <nombre_completo>`
   - ✅ Soporte comando: `TRANSFERIR <origen> <destino> <monto>`
   - ✅ Validación: cédula empieza con "0"

3. **update_database.py**
   - ✅ ALTER TABLE para agregar TRANSFERENCIA_ENVIADA/RECIBIDA
   - **Ejecutar una vez:** `python update_database.py`

4. **.env**
   - ✅ DB_HOST con Azure MySQL
   - ✅ CORS_ORIGINS con URL de Netlify
   - ✅ Credenciales reales (NO commitear)

### Frontend (en Netlify):

1. **alert-toast.tsx** (NUEVO)
   - ✅ Componente de alertas visuales grandes
   - **Sin esto:** No se ven errores de transferencias

2. **transfer-card.tsx**
   - ✅ Manejo de alertas con `AlertToast`
   - ✅ Console.log para debugging
   - ✅ Verificación explícita: `success === true`

3. **globals.css**
   - ✅ Animaciones: `slide-in-right`, `slide-out-right`
   - **Sin esto:** Alertas no tienen animaciones

4. **.env.production**
   - ✅ NEXT_PUBLIC_API_URL
   - ✅ NEXT_PUBLIC_WS_URL

---

## 🎯 TESTING FINAL

### Crear y ejecutar este test:

```bash
# En tu PC local o desde VM:
cat > test_production.sh << 'EOF'
#!/bin/bash

API_URL="http://TU_IP_PUBLICA"

echo "1. Test API Stats..."
curl -s $API_URL/api/stats | jq .

echo "2. Test Crear Cuenta..."
curl -X POST $API_URL/api/crear \
  -H "Content-Type: application/json" \
  -d '{"cedula":"0999888777","nombre":"Test User"}' | jq .

echo "3. Test Login..."
curl -X POST $API_URL/api/consulta \
  -H "Content-Type: application/json" \
  -d '{"cedula":"0999888777"}' | jq .

echo "4. Test Deposito..."
curl -X POST $API_URL/api/deposito \
  -H "Content-Type: application/json" \
  -d '{"cedula":"0999888777","monto":100}' | jq .

echo "5. Test Transferencia con Decimales..."
curl -X POST $API_URL/api/transferir \
  -H "Content-Type: application/json" \
  -d '{"cedula_origen":"0999888777","cedula_destino":"1234567890","monto":1.22}' | jq .

echo "✅ Todos los tests completados"
EOF

chmod +x test_production.sh
./test_production.sh
```

**Todos deberían retornar:** `{"success": true, ...}`

---

## 🎉 DEPLOYMENT EXITOSO

**Si llegaste hasta aquí sin errores:**

✅ Base de datos Azure MySQL funcionando  
✅ VM Azure con backend auto-restart  
✅ Frontend en Netlify con CDN global  
✅ WebSocket real-time operativo  
✅ Todas las funcionalidades:
- Login
- Crear cuenta (pública)
- Depósito/Retiro
- **Transferencias (sin error Decimal)** ⭐
- **Alertas visuales grandes** ⭐
- **Gráfico sin restart** ⭐
- Historial completo

**URLs de tu aplicación:**
- Frontend: `https://________.netlify.app`
- Backend: `http://___.___.___.___`

**Costos mensuales estimados:** $20-30 USD

---

## 🔗 DOCUMENTACIÓN COMPLETA

- **Guía Detallada:** `GUIA_PRODUCCION_COMPLETA.md` (30+ páginas)
- **Checklist Paso a Paso:** `DEPLOYMENT_CHECKLIST.md`
- **Script de Verificación:** `verify-deployment.sh`
- **Correcciones Aplicadas:** `CORRECCIONES_BUGS.md`
- **Alertas Visuales:** `ALERTAS_VISUALES_IMPLEMENTADAS.md`

---

**¡Buena suerte con el deployment! 🚀**
