# Manual de laboratorio — SecOps Hub

Guía práctica paso a paso para aprender a usar la plataforma con ejercicios concretos, valores de prueba y resultados esperados.

**Duración estimada:** 60–90 minutos  
**Nivel:** Principiante / intermedio  
**Entorno:** Local (Windows, macOS o Linux)

---

## 0. Preparación del entorno

### 0.1 Arrancar servicios

Abre **dos terminales**:

**Terminal 1 — Backend**
```bash
cd backend
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS
python run.py
```
Debe mostrar: `Running on http://127.0.0.1:5000`

**Terminal 2 — Frontend**
```bash
cd frontend
npm run dev
```
Debe mostrar: `Local: http://localhost:5173/`

### 0.2 Credenciales de laboratorio

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| `admin` | `admin123` | Administrador |
| `analyst` | `analyst123` | Analista |

### 0.3 Datos precargados (seed)

Al primer arranque, la base de datos incluye:

| Tipo | Cantidad | Ejemplos |
|------|----------|----------|
| Incidentes | 5 | Malware en HR-042, exfiltración de datos |
| IOCs | 4 | `192.168.1.100` (bloqueada), `10.0.0.55` (sospechosa) |
| Vulnerabilidades | 5 | `CVE-2024-3400`, `CVE-2023-4966` (KEV) |
| Logs de auditoría | 5 | Acciones previas de admin y analyst |

### 0.4 Resetear datos (opcional)

Si necesitas empezar de cero:
```bash
# Detén el backend (Ctrl+C), luego:
del backend\instance\secops_hub.db     # Windows
# rm backend/instance/secops_hub.db      # Linux/macOS
python run.py
```

---

## Laboratorio 1 — Autenticación y roles

**Objetivo:** Entender la diferencia entre admin y analyst.

### Paso 1.1 — Login como analista

1. Abre http://localhost:5173/login
2. Introduce: `analyst` / `analyst123`
3. Pulsa **Iniciar sesión**

**Resultado esperado:**
- Redirección al Dashboard (`/`)
- Sidebar muestra usuario `analyst` con rol `analyst`

### Paso 1.2 — Verificar sesión JWT

1. Abre DevTools del navegador (F12)
2. Ve a **Application → Local Storage → localhost:5173**
3. Busca la clave `secops_token`

**Resultado esperado:** Existe un token JWT almacenado.

### Paso 1.3 — Probar acceso restringido (API)

En PowerShell (Windows):
```powershell
# Obtener token de analyst
$login = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/auth/login" `
  -Method POST -ContentType "application/json" `
  -Body '{"username":"analyst","password":"analyst123"}'
$token = $login.access_token

# Intentar ejecutar playbook (debe fallar)
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/playbooks/run" `
  -Method POST -ContentType "application/json" `
  -Headers @{ Authorization = "Bearer $token" } `
  -Body '{"playbook_id":"isolate_host","params":{"hostname":"WS-001"}}'
```

**Resultado esperado:** Error **403** — *"Acceso restringido a administradores"*.

### Paso 1.4 — Cerrar sesión y entrar como admin

1. Pulsa **Cerrar sesión** en la sidebar
2. Inicia sesión con `admin` / `admin123`

**Resultado esperado:** Dashboard accesible con usuario `admin`.

---

## Laboratorio 2 — Dashboard SOC

**Objetivo:** Interpretar KPIs y el feed de auditoría.

**Usuario:** `analyst` o `admin`

### Paso 2.1 — Revisar KPIs

1. Ve al Dashboard (`/`)
2. Anota los valores de las 4 tarjetas:

| KPI | Valor esperado (aprox.) |
|-----|-------------------------|
| Alertas activas | 4 (incidentes open + investigating) |
| IPs bloqueadas | 1 (`192.168.1.100`) |
| Vulnerabilidades KEV | 3–4 (KEV abiertas) |
| Total incidentes | 5 |

> Los números pueden variar si completaste otros laboratorios antes.

### Paso 2.2 — Analizar gráficos

1. **Distribución por severidad:** observa cuántos incidentes activos hay en `critical`, `high`, `medium`.
2. **Eventos por hora:** revisa la tendencia de las últimas 24 horas.

**Pregunta de reflexión:** ¿Hay más incidentes `critical` que `medium`? ¿Qué priorizarías?

### Paso 2.3 — Feed de auditoría

Desplázate al final del dashboard y localiza entradas como:
- *"Playbook ejecutado: Aislar Host"*
- *"IOC enriquecido y bloqueado"*
- *"Vulnerabilidad KEV revisada"*

**Resultado esperado:** Al menos 5 entradas con usuario, acción y fecha.

---

## Laboratorio 3 — Triaje de IOCs

**Objetivo:** Enriquecer indicadores, interpretar veredictos y bloquear amenazas.

**Usuario:** `analyst`

### Paso 3.1 — Enriquecer una IP desconocida

1. Ve a **IOCs** (`/iocs`)
2. En el campo de texto, pega: `203.0.113.50`
3. Pulsa **Enriquecer**

**Resultado esperado:**

| Campo | Qué observar |
|-------|--------------|
| Tipo | `ip` |
| Puntuación | Número entre 0 y 100 |
| Veredicto | `MALICIOUS`, `SUSPICIOUS` o `CLEAN` |
| VirusTotal | Contadores malicious/suspicious/harmless |
| AbuseIPDB | Confianza de abuso (solo IPs) |
| Recomendación | `block` o `monitor` |

> El score es **determinístico**: la misma IP siempre produce el mismo resultado.

### Paso 3.2 — Enriquecer un hash SHA1

1. Pega este hash:
   ```
   da39a3ee5e6b4b0d3255bfef95601890afd80709
   ```
2. Pulsa **Enriquecer**

**Resultado esperado:** Tipo `sha1`, veredicto y score calculados. AbuseIPDB no aparece (solo aplica a IPs).

### Paso 3.3 — Enriquecer una IP "limpia"

1. Pega: `8.8.8.8`
2. Pulsa **Enriquecer**

**Resultado esperado:** Veredicto probablemente `CLEAN` o `SUSPICIOUS` con score bajo.

### Paso 3.4 — Revisar IOC precargado sospechoso

1. En la tabla inferior, localiza la IP `10.0.0.55`
2. Verifica: veredicto `suspicious`, score `45`, **no bloqueada**

**Pregunta:** ¿La bloquearías? ¿Por qué?

### Paso 3.5 — Bloquear un IOC malicioso (si aplica)

Si enriqueciste una IP con veredicto `malicious` que aún no está bloqueada:

1. En la tabla, pulsa **Bloquear** en esa fila
2. Vuelve al Dashboard

**Resultado esperado:**
- IOC marcado como "Bloqueado" en la tabla
- KPI "IPs bloqueadas" incrementado en 1
- Nueva entrada en el feed de auditoría

---

## Laboratorio 4 — Gestión de vulnerabilidades (CISA KEV)

**Objetivo:** Priorizar parches usando el catálogo KEV.

**Usuario:** `analyst` o `admin`

### Paso 4.1 — Ver todas las vulnerabilidades

1. Ve a **Vulnerabilidades** (`/vulnerabilities`)
2. Deja el filtro de severidad en **Todas**
3. Desactiva **Solo CISA KEV**

**Resultado esperado:** 5 CVEs listados, ordenados por CVSS descendente.

### Paso 4.2 — Filtrar solo CISA KEV

1. Activa el checkbox **Solo CISA KEV (explotación activa)**

**Resultado esperado:** Solo CVEs con badge **KEV**, por ejemplo:
- `CVE-2024-3400` — Palo Alto PAN-OS (CVSS 10.0)
- `CVE-2023-4966` — Citrix Bleed (CVSS 9.4)
- `CVE-2024-21413` — Microsoft Outlook (CVSS 9.8)
- `CVE-2024-1086` — Linux Kernel (CVSS 7.8)

### Paso 4.3 — Filtrar por severidad crítica

1. Desactiva KEV
2. Selecciona severidad **Critical**

**Resultado esperado:** Solo vulnerabilidades con severidad `critical`.

### Paso 4.4 — Escenario de priorización

**Ejercicio:** Eres el analista responsable de parcheo. Responde:

1. ¿Qué CVE KEV abierta tiene mayor CVSS?
2. ¿Qué sistema afecta `CVE-2024-3400`?
3. ¿Cuál está en estado `mitigated`?

**Respuestas esperadas:**
1. `CVE-2024-3400` (CVSS 10.0)
2. Firewall PA-5200
3. `CVE-2023-44487` (HTTP/2 Rapid Reset)

---

## Laboratorio 5 — Playbooks de respuesta

**Objetivo:** Ejecutar automatizaciones de respuesta (solo admin).

**Usuario:** `admin`

### Paso 5.1 — Ver catálogo de playbooks

1. Ve a **Playbooks** (`/playbooks`)
2. Revisa los 3 playbooks disponibles:

| Playbook | Parámetro de ejemplo |
|----------|---------------------|
| Aislar Host | `WS-HR-042` |
| Revocar Usuario | `jperez` |
| Escaneo de Datos | `192.168.10.0/24` |

### Paso 5.2 — Ejecutar "Aislar Host"

1. En el playbook **Aislar Host**, escribe en el campo `hostname`: `WS-HR-042`
2. Pulsa **Ejecutar**

**Resultado esperado:**
- Panel verde: *"Host WS-HR-042 aislado correctamente"*
- Status: `completed`

### Paso 5.3 — Ejecutar "Revocar Usuario"

1. En **Revocar Usuario**, escribe: `jperez`
2. Pulsa **Ejecutar**

**Resultado esperado:** *"Usuario jperez revocado"*

### Paso 5.4 — Verificar trazabilidad

1. Ve al Dashboard
2. Busca en el feed de auditoría las acciones de playbooks recién ejecutadas

**Resultado esperado:** Entradas como *"Playbook ejecutado: Aislar Host"* con detalles.

### Paso 5.5 — Probar restricción de rol (analyst)

1. Cierra sesión
2. Entra como `analyst` / `analyst123`
3. Ve a **Playbooks**

**Resultado esperado:**
- Los 3 playbooks visibles
- Botones **Ejecutar** deshabilitados
- Mensaje: *"Solo lectura — requiere rol admin"*

---

## Laboratorio 6 — Integración por webhook

**Objetivo:** Simular recepción de alertas desde un SIEM externo.

**Herramienta:** Terminal (curl o PowerShell). No requiere login web.

### Paso 6.1 — Enviar alerta válida

**PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/webhooks/alert" `
  -Method POST `
  -ContentType "application/json" `
  -Headers @{ "X-API-Key" = "secops-webhook-key-dev" } `
  -Body '{"title":"Brute force detectado","description":"500 intentos desde 198.51.100.42","severity":"high","source":"Splunk"}'
```

**curl (Linux/macOS/Git Bash):**
```bash
curl -X POST http://localhost:5000/api/webhooks/alert \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secops-webhook-key-dev" \
  -d '{"title":"Brute force detectado","description":"500 intentos desde 198.51.100.42","severity":"high","source":"Splunk"}'
```

**Resultado esperado:**
```json
{
  "message": "Alerta recibida y registrada",
  "incident": {
    "title": "Brute force detectado",
    "severity": "high",
    "status": "open",
    "source": "Splunk"
  }
}
```

### Paso 6.2 — Verificar en el dashboard

1. Inicia sesión como `analyst`
2. Ve al Dashboard

**Resultado esperado:**
- KPI "Alertas activas" incrementado
- KPI "Total incidentes" incrementado

### Paso 6.3 — Enviar alerta sin API Key (debe fallar)

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/webhooks/alert" `
  -Method POST -ContentType "application/json" `
  -Body '{"title":"Alerta sin auth","severity":"medium"}'
```

**Resultado esperado:** Error **401** — *"API Key inválida o ausente"*.

### Paso 6.4 — Enviar alerta crítica

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/webhooks/alert" `
  -Method POST -ContentType "application/json" `
  -Headers @{ "X-API-Key" = "secops-webhook-key-dev" } `
  -Body '{"title":"Ransomware detectado en DC-01","description":"Cifrado masivo en servidor de dominio","severity":"critical","source":"CrowdStrike"}'
```

**Resultado esperado:** Incidente crítico creado. Revisa el gráfico de severidad en el dashboard.

---

## Laboratorio 7 — Flujo SOC completo (escenario integrado)

**Objetivo:** Simular un ciclo real de respuesta a incidente.

**Duración:** 20 minutos  
**Roles:** `analyst` + `admin`

### Escenario

> El SIEM detecta actividad sospechosa desde la IP `198.51.100.77` hacia el servidor `SRV-FIN-01`. Hay indicios de exfiltración.

### Paso 7.1 — Recepción de alerta (analista)

Ejecuta el webhook del Laboratorio 6 con estos datos:
```json
{
  "title": "Exfiltración sospechosa hacia IP externa",
  "description": "Transferencia 1.8GB desde SRV-FIN-01 a 198.51.100.77",
  "severity": "critical",
  "source": "SIEM-QRadar"
}
```

### Paso 7.2 — Triaje del IOC (analista)

1. Login como `analyst`
2. Ve a **IOCs**
3. Enriquece la IP: `198.51.100.77`
4. Anota veredicto y score

### Paso 7.3 — Bloqueo (analista, si es malicious)

Si el veredicto es `malicious`, bloquea el IOC.

### Paso 7.4 — Revisión de vulnerabilidades (analista)

1. Ve a **Vulnerabilidades**
2. Activa filtro **Solo CISA KEV**
3. Identifica si alguna CVE afecta al servidor financiero

### Paso 7.5 — Respuesta automatizada (admin)

1. Cierra sesión, entra como `admin`
2. Ve a **Playbooks**
3. Ejecuta **Aislar Host** con hostname: `SRV-FIN-01`
4. Ejecuta **Escaneo de Datos** con target: `SRV-FIN-01`

### Paso 7.6 — Informe final (analista/admin)

Responde por escrito:

| Pregunta | Tu respuesta |
|----------|--------------|
| ¿Cuál fue el veredicto del IOC? | |
| ¿Se bloqueó la IP? | |
| ¿Qué playbooks se ejecutaron? | |
| ¿Cuántas alertas activas hay ahora? | |
| ¿Qué acciones aparecen en el audit feed? | |

---

## Laboratorio 8 — API directa (desarrolladores)

**Objetivo:** Interactuar con la API sin interfaz web.

### Paso 8.1 — Login y consulta de perfil

```powershell
$login = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/auth/login" `
  -Method POST -ContentType "application/json" `
  -Body '{"username":"admin","password":"admin123"}'

$login | ConvertTo-Json

$me = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/auth/me" `
  -Headers @{ Authorization = "Bearer $($login.access_token)" }
$me | ConvertTo-Json
```

### Paso 8.2 — Stats del dashboard

```powershell
$stats = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/incidents/stats" `
  -Headers @{ Authorization = "Bearer $($login.access_token)" }
$stats.kpis | ConvertTo-Json
```

### Paso 8.3 — Enriquecer IOC vía API

```powershell
$enrich = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/iocs/enrich" `
  -Method POST -ContentType "application/json" `
  -Headers @{ Authorization = "Bearer $($login.access_token)" } `
  -Body '{"value":"198.51.100.99"}'
$enrich | ConvertTo-Json
```

### Paso 8.4 — Registrar nuevo usuario (solo admin)

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/auth/register" `
  -Method POST -ContentType "application/json" `
  -Headers @{ Authorization = "Bearer $($login.access_token)" } `
  -Body '{"username":"labuser","email":"lab@secops.local","password":"lab123456","role":"analyst"}'
```

**Resultado esperado:** Usuario `labuser` creado. Puedes iniciar sesión con él en la web.

---

## Apéndice A — Valores de prueba recomendados

### IPs para enriquecimiento

| IP | Notas |
|----|-------|
| `192.168.1.100` | Precargada, malicious, bloqueada |
| `10.0.0.55` | Precargada, suspicious |
| `8.8.8.8` | IP pública, suele dar score bajo |
| `203.0.113.50` | IP de documentación (RFC 5737) |
| `198.51.100.77` | Escenario integrado Lab 7 |

### Hashes para enriquecimiento

| Hash | Tipo |
|------|------|
| `da39a3ee5e6b4b0d3255bfef95601890afd80709` | SHA1 (hash vacío) |
| `a1b2c3d4e5f6789012345678901234567890abcd` | SHA1 precargado, malicious |
| `d41d8cd98f00b204e9800998ecf8427e` | MD5 (hash vacío) |

### Payloads webhook

```json
{"title":"Phishing masivo","severity":"medium","source":"Email Gateway"}
{"title":"Lateral movement","severity":"high","source":"EDR"}
{"title":"Zero-day exploit attempt","severity":"critical","source":"IDS"}
```

---

## Apéndice B — Checklist de competencias

Al completar todos los laboratorios, deberías ser capaz de:

- [ ] Iniciar sesión con roles diferenciados (admin/analyst)
- [ ] Interpretar KPIs y gráficos del dashboard SOC
- [ ] Enriquecer IOCs (IP, hash) y actuar según veredicto
- [ ] Bloquear indicadores maliciosos
- [ ] Filtrar vulnerabilidades por severidad y CISA KEV
- [ ] Ejecutar playbooks de respuesta (como admin)
- [ ] Enviar alertas por webhook con API Key
- [ ] Completar un flujo SOC de extremo a extremo
- [ ] Usar la API REST directamente con JWT

---

## Apéndice C — Solución de problemas

| Problema | Solución |
|----------|----------|
| `Connection refused` en :5173 | Ejecuta `npm run dev` en `frontend/` |
| `Connection refused` en :5000 | Ejecuta `python run.py` en `backend/` |
| Login falla siempre | Verifica credenciales; resetea BD si es necesario |
| Playbook 403 | Debes ser `admin`, no `analyst` |
| Webhook 401 | Incluye header `X-API-Key: secops-webhook-key-dev` |
| KPIs no cambian | Recarga la página del dashboard |
| Token expirado | Cierra sesión y vuelve a entrar (expira a las 8 h) |

---

## Referencias

- [Manual de usuario](manual-usuario.md)
- [Manual de desarrollador](manual-desarrollador.md)
- [Casos de uso](casos-de-uso.md)
- [Diagramas UML](diagramas-uml.md)
