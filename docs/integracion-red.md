# Integración en red — SecOps Hub

Guía paso a paso para conectar SecOps Hub con sistemas reales de una red corporativa: **SIEM** (Splunk, QRadar), **firewall** y **EDR**.

**Audiencia:** administradores de seguridad, ingenieros SOC, DevSecOps.

---

## 1. Visión general

SecOps Hub actúa como **consola central de operaciones**. No sustituye al SIEM ni al EDR, sino que **recibe alertas**, permite **triaje manual/automático** y **orquesta respuestas** mediante playbooks.

![Flujo de red SecOps Hub](flujo_red_secops_hub.svg)

### Cuatro direcciones de comunicación

| # | Dirección | Mecanismo | Autenticación |
|---|-----------|-----------|---------------|
| ① | **SIEM → SecOps Hub** | Webhook `POST /api/webhooks/alert` | Header `X-API-Key` |
| ② | **Analistas ↔ SecOps Hub** | Consola React + API REST | JWT Bearer (HTTPS) |
| ③ | **SecOps Hub → EDR** | Playbooks de contención | API EDR (simulado en demo) |
| ④ | **SecOps Hub → Firewall** | Bloqueo IP / deny list | API firewall (simulado en demo) |

SecOps Hub permanece **dentro de la red corporativa**, accesible desde el SIEM y desde analistas autorizados (VLAN SOC o VPN). **No debe exponerse directamente a Internet.**

```
                    ┌─────────────────────────────────────────┐
                    │           RED CORPORATIVA               │
                    │                                         │
  ┌──────────┐      │   ┌─────────┐      ┌──────────────┐   │
  │ Splunk   │──────┼──►│ SecOps  │◄─────│  Analistas   │   │
  │ QRadar   │ webhook   │   Hub   │ JWT  │  (navegador) │   │
  └──────────┘      │   │  :443   │      └──────────────┘   │
                    │   └────┬────┘                          │
  ┌──────────┐      │        │ playbooks (API)               │
  │ CrowdStrike     │        ▼                               │
  │ Defender │◄─────┼─── Aislar / escanear host              │
  └──────────┘      │        │                               │
                    │        ▼                               │
  ┌──────────┐      │   Bloquear IP / URL                    │
  │ Palo Alto│◄─────┼─── (firewall API)                     │
  │ pfSense  │      │                                         │
  └──────────┘      └─────────────────────────────────────────┘
```

### Capas de integración

| Capa | Dirección | Mecanismo actual | Estado |
|------|-----------|------------------|--------|
| **Ingesta** | SIEM → SecOps Hub | Webhook `POST /api/webhooks/alert` | ✅ Implementado |
| **Triaje** | Analista → APIs externas | Enriquecimiento IOC | ⚠️ Simulado (extensible) |
| **Respuesta** | SecOps Hub → EDR/FW/AD | Playbooks `POST /api/playbooks/run` | ⚠️ Simulado (extensible) |
| **Visualización** | SecOps Hub → Analista | Dashboard web JWT | ✅ Implementado |

---

## 2. Requisitos previos de despliegue en red

Antes de conectar sistemas externos, SecOps Hub debe estar accesible en la red interna (o DMZ):

| Requisito | Desarrollo | Producción |
|-----------|------------|------------|
| URL API | `http://localhost:5000` | `https://secops.empresa.local` |
| Puerto | 5000 (backend), 5173 (frontend dev) | 443 (HTTPS) |
| Certificado TLS | No | Obligatorio (Let's Encrypt o CA interna) |
| Firewall interno | — | Permitir SIEM/EDR → SecOps Hub |
| Variables `.env` | Valores demo | Claves seguras ≥ 32 caracteres |

### Ejemplo `.env` producción

```env
SECRET_KEY=clave-flask-aleatoria-minimo-32-caracteres
JWT_SECRET_KEY=clave-jwt-aleatoria-minimo-32-caracteres
WEBHOOK_API_KEY=clave-webhook-compartida-con-siem
DATABASE_URL=postgresql://secops:password@db-server:5432/secops_hub
```

### Endpoint de webhook (referencia)

```http
POST https://secops.empresa.local/api/webhooks/alert
Content-Type: application/json
X-API-Key: <WEBHOOK_API_KEY>

{
  "title": "string (obligatorio recomendado)",
  "description": "string",
  "severity": "critical | high | medium | low",
  "source": "string (ej. Splunk, QRadar, CrowdStrike)"
}
```

**Respuesta exitosa:** `201 Created` con el incidente creado.

---

## 3. Integración con Splunk

### 3.1 Arquitectura

```
Splunk Enterprise / Cloud
    │
    │  Alert Action (webhook) o Scheduled Search
    ▼
SecOps Hub  POST /api/webhooks/alert
    │
    ▼
Tabla incidents → Dashboard KPI "Alertas activas"
```

### 3.2 Paso 1 — Crear alerta en Splunk

1. En Splunk, abre **Settings → Searches, reports, and alerts → Alerts**.
2. Crea o edita una búsqueda que detecte eventos relevantes, por ejemplo:

```spl
index=firewall action=blocked src_ip!=10.0.0.0/8
| stats count by src_ip, dest_ip
| where count > 100
```

3. Configura **Trigger**: cuando el número de resultados sea mayor que 0.
4. En **Trigger Actions**, añade **Webhook**.

### 3.3 Paso 2 — Configurar Webhook Action

| Campo Splunk | Valor |
|--------------|-------|
| URL | `https://secops.empresa.local/api/webhooks/alert` |
| HTTP Method | POST |
| Payload | JSON (ver plantilla abajo) |

**Headers personalizados:**

```http
Content-Type: application/json
X-API-Key: tu-clave-webhook-produccion
```

**Plantilla JSON (Splunk Webhook):**

```json
{
  "title": "Splunk: Brute force desde $result.src_ip$",
  "description": "$result.count$ intentos bloqueados. Destino: $result.dest_ip$",
  "severity": "high",
  "source": "Splunk"
}
```

> **Nota:** En Splunk Enterprise, las variables `$result.campo$` se sustituyen por valores del evento que disparó la alerta.

### 3.4 Paso 3 — Mapeo de severidad

| Condición Splunk | severity en SecOps Hub |
|------------------|------------------------|
| Crítico / compromiso confirmado | `critical` |
| Alta prioridad / múltiples hosts | `high` |
| Actividad sospechosa | `medium` |
| Informativo | `low` |

Puedes usar un **calculated field** o **eval** en SPL para generar el campo severity dinámicamente.

### 3.5 Paso 4 — Verificación

1. Fuerza la alerta en Splunk (Trigger Alert).
2. En SecOps Hub, inicia sesión y revisa el Dashboard.
3. KPI **Alertas activas** debe incrementarse.
4. Clic en el KPI → listado con el incidente de Splunk.

**Prueba manual (sin Splunk):**

```powershell
Invoke-RestMethod -Uri "https://secops.empresa.local/api/webhooks/alert" `
  -Method POST -ContentType "application/json" `
  -Headers @{ "X-API-Key" = "tu-clave-webhook" } `
  -Body '{"title":"Test Splunk","severity":"high","source":"Splunk"}'
```

### 3.6 Splunk SOAR (Phantom) — integración avanzada

Si usas Splunk SOAR en lugar de webhooks simples:

1. Crea un **Custom App** o usa la acción **Generic HTTP Request**.
2. Endpoint: `POST /api/webhooks/alert`
3. Encadena playbooks SOAR → SecOps Hub → respuesta EDR.

---

## 4. Integración con IBM QRadar

### 4.1 Arquitectura

```
QRadar Console
    │
    │  Rule → Response → External API
    ▼
SecOps Hub  POST /api/webhooks/alert
```

### 4.2 Paso 1 — Crear regla de ofensa en QRadar

1. **Log Activity** o **Offenses** → **Rules**.
2. Crea una regla, por ejemplo:
   - *When an offense is created*
   - *And magnitude >= 5*
3. En **Rule Response**, añade **External API**.

### 4.3 Paso 2 — Configurar External API

QRadar no tiene webhook nativo tan directo como Splunk; se usa **Scripted Rule Response** o **API externa vía App**:

**Opción A — Script (Python en QRadar appliance):**

```python
#!/usr/bin/env python3
import json
import urllib.request

def send_to_secops(offense):
    payload = {
        "title": f"QRadar Offense #{offense.get('id')}: {offense.get('description', '')[:100]}",
        "description": offense.get("source_address", "") + " → " + offense.get("destination_address", ""),
        "severity": map_magnitude(offense.get("magnitude", 3)),
        "source": "QRadar"
    }
    req = urllib.request.Request(
        "https://secops.empresa.local/api/webhooks/alert",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "tu-clave-webhook"
        },
        method="POST"
    )
    urllib.request.urlopen(req)

def map_magnitude(m):
    if m >= 8: return "critical"
    if m >= 6: return "high"
    if m >= 4: return "medium"
    return "low"
```

**Opción B — QRadar App (HTTP Forwarder):**

Instala una app de forwarding HTTP desde IBM App Exchange y configura:

| Campo | Valor |
|-------|-------|
| URL | `https://secops.empresa.local/api/webhooks/alert` |
| Method | POST |
| Header | `X-API-Key: <clave>` |
| Body template | JSON con campos de ofensa |

### 4.4 Paso 3 — Mapeo magnitud QRadar → severity

| Magnitud QRadar | severity SecOps Hub |
|-----------------|---------------------|
| 8–10 | `critical` |
| 6–7 | `high` |
| 4–5 | `medium` |
| 1–3 | `low` |

### 4.5 Paso 4 — Verificación

1. Genera una ofensa de prueba en QRadar.
2. Comprueba en SecOps Hub Dashboard que aparece con `source: "QRadar"`.

---

## 5. Integración con Firewall

Los firewalls suelen integrarse en **dos direcciones**:

| Dirección | Uso |
|-----------|-----|
| **Firewall → SecOps Hub** | Alertas de bloqueo, IPS, URL filtering → webhook |
| **SecOps Hub → Firewall** | Playbook bloquea IP/URL tras triaje IOC |

### 5.1 Firewall → SecOps Hub (ingesta de alertas)

#### Palo Alto Networks (PAN-OS + Logging)

1. Configura **Log Forwarding** a un collector syslog o SIEM.
2. Desde Splunk/QRadar (ya conectados), crea regla que reenvíe alertas IPS a SecOps Hub.
3. Alternativa directa: **HTTP Log Forwarding Profile** (PAN-OS 10.1+) hacia un middleware que traduzca a JSON webhook.

**Payload ejemplo (vía middleware):**

```json
{
  "title": "PAN-OS: Threat blocked",
  "description": "IP 203.0.113.50 blocked on rule Threat-Outbound. Threat: trojan.generic",
  "severity": "high",
  "source": "Palo Alto PA-5200"
}
```

#### pfSense / OPNsense

1. Instala plugin **syslog-ng** o envía logs a Splunk.
2. Crea alerta en Splunk sobre eventos `block` del firewall.
3. Splunk webhook → SecOps Hub (ver sección 3).

### 5.2 SecOps Hub → Firewall (bloqueo de IP)

**Estado actual:** el playbook no llama al firewall. **Integración futura** en `run_playbook()`:

#### Palo Alto — bloqueo vía API XML

```python
# Ejemplo conceptual para playbook "block_ip"
import requests

def block_ip_palo_alto(ip: str, api_key: str, fw_url: str):
    xml = f"""
    <entry ip="{ip}">
      <tag><member>secops-blocked</member></tag>
    </entry>
    """
    requests.post(
        f"{fw_url}/api/",
        params={"type": "config", "action": "set", "key": api_key},
        data={"xpath": "/config/devices/entry/vsys/entry/address", "element": xml},
        verify=False  # usar certificado en producción
    )
```

#### Variables `.env` adicionales

```env
FIREWALL_TYPE=palo_alto
FIREWALL_URL=https://firewall.empresa.local
FIREWALL_API_KEY=clave-api-firewall
```

#### Flujo operativo completo

```
1. SIEM detecta tráfico malicioso desde 203.0.113.50
2. Webhook → SecOps Hub (incidente creado)
3. Analista enriquece IP en IOCs → verdict: malicious
4. Analista pulsa "Bloquear" (marca en SecOps Hub)
5. Admin ejecuta playbook "block_ip" → API firewall añade IP a deny list
6. Tráfico bloqueado en red real
```

---

## 6. Integración con EDR

### 6.1 EDR → SecOps Hub (ingesta)

Los EDR envían alertas al SIEM; el camino habitual es:

```
EDR (CrowdStrike / Defender) → SIEM → SecOps Hub webhook
```

#### Microsoft Defender for Endpoint

1. En **Microsoft 365 Defender**, configura **Streaming API** o conector a Sentinel/Splunk.
2. Regla en Sentinel/Splunk: alertas severity High/Critical → webhook SecOps Hub.

**Payload ejemplo:**

```json
{
  "title": "Defender: Malware detected on WS-FIN-042",
  "description": "Trojan:Win32/Generic detected. User: jperez@empresa.com",
  "severity": "critical",
  "source": "Microsoft Defender"
}
```

#### CrowdStrike Falcon

1. **Falcon Data Replicator** → S3/Splunk/QRadar.
2. Alertas de detección → regla SIEM → webhook SecOps Hub.

O usa **CrowdStrike API** con polling periódico (script externo):

```python
# Script cron cada 5 min — ejemplo conceptual
import requests

headers = {"Authorization": "Bearer " + os.getenv("CROWDSTRIKE_API_TOKEN")}
alerts = requests.get(
    "https://api.crowdstrike.com/alerts/queries/alerts/v1",
    headers=headers,
    params={"filter": "status:'new'+severity:>='High'"}
).json()

for alert_id in alerts.get("resources", []):
    # Obtener detalle y enviar a SecOps Hub webhook
    ...
```

### 6.2 SecOps Hub → EDR (respuesta: aislar host)

**Playbook actual:** `isolate_host` con parámetro `hostname` (simulado).

#### Microsoft Defender — aislar dispositivo

```python
# Ejemplo conceptual
def isolate_host_defender(device_id: str, token: str):
    requests.post(
        f"https://api.securitycenter.microsoft.com/api/machines/{device_id}/isolate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "Comment": "Aislamiento iniciado desde SecOps Hub",
            "IsolationType": "Full"
        }
    )
```

#### CrowdStrike — contener host

```python
def contain_host_crowdstrike(device_id: str, token: str):
    requests.post(
        "https://api.crowdstrike.com/devices/entities/devices-actions/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "action_name": "contain",
            "ids": [device_id]
        }
    )
```

#### Variables `.env` EDR

```env
EDR_TYPE=defender
EDR_TENANT_ID=uuid-azure-ad
EDR_CLIENT_ID=app-registration-id
EDR_CLIENT_SECRET=secret
```

#### Flujo operativo

```
1. Defender detecta malware en WS-HR-042
2. Alerta → Splunk → SecOps Hub (incidente critical)
3. Analista revisa dashboard, abre detalle
4. Admin ejecuta playbook "Aislar Host" → hostname: WS-HR-042
5. SecOps Hub llama API Defender → máquina aislada de red
6. Audit log: "Playbook ejecutado: Aislar Host"
```

---

## 7. Flujo SOC completo de extremo a extremo

Escenario: **exfiltración de datos detectada**.

```
TIEMPO   ACTOR              ACCIÓN                           SISTEMA
─────────────────────────────────────────────────────────────────────
T+0      Firewall/SIEM      Detecta 2.3GB salida anómala     Palo Alto
T+1      Splunk             Alerta dispara webhook           Splunk → SecOps Hub
T+2      SecOps Hub         Crea incidente severity=critical BD SQLite/PG
T+3      Analista           Ve KPI "Alertas activas" +1      Dashboard
T+5      Analista           Extrae IP 198.51.100.77          Descripción incidente
T+6      Analista           Enriquece IP en IOCs             /api/iocs/enrich
T+8      Analista           Verdict: malicious → Bloquear    /api/iocs/{id}/block
T+10     Admin              Playbook: Aislar Host            /api/playbooks/run
                            hostname=SRV-FIN-01
T+12     EDR                Máquina aislada                  Defender API
T+15     Admin              Playbook: Revocar Usuario        /api/playbooks/run
                            username=jperez
T+17     AD/Azure AD        Sesiones revocadas               Graph API
T+20     Analista           Cierra incidente (manual/futuro) status=resolved
T+25     Auditor            Revisa feed de auditoría         Dashboard
```

---

## 8. Matriz de integración por producto

| Producto | Ingesta → SecOps Hub | Respuesta ← SecOps Hub | Mecanismo |
|----------|:--------------------:|:----------------------:|-----------|
| **Splunk** | ✅ | — | Webhook Alert Action |
| **QRadar** | ✅ | — | Scripted Response / App |
| **Palo Alto** | ✅ (vía SIEM) | 🔧 Playbook API | Log forwarding + XML API |
| **pfSense** | ✅ (vía SIEM) | 🔧 Script | Syslog → Splunk → webhook |
| **Microsoft Defender** | ✅ (vía SIEM) | 🔧 Playbook API | Streaming API / Graph |
| **CrowdStrike** | ✅ (vía SIEM) | 🔧 Playbook API | Falcon API |
| **SentinelOne** | ✅ (vía SIEM) | 🔧 Playbook API | REST API |
| **Active Directory** | — | 🔧 Playbook revoke | LDAP / PowerShell |

✅ = soportado hoy (webhook) · 🔧 = requiere extensión del playbook

---

## 9. Seguridad de la integración

| Medida | Implementación |
|--------|----------------|
| Autenticación webhook | Header `X-API-Key` (rotar periódicamente) |
| Autenticación analistas | JWT Bearer (8 h expiración) |
| RBAC | admin vs analyst en playbooks |
| TLS | HTTPS obligatorio en producción |
| Red | SecOps Hub en VLAN SOC; SIEM en misma VLAN o DMZ |
| Rate limiting | Recomendado en Nginx (no implementado aún) |
| Validación payload | severity whitelist; sanitizar title/description |
| Auditoría | Todas las acciones en `audit_logs` |
| Secrets | Nunca en código; solo `.env` o vault |

### Reglas de firewall recomendadas

```
Permitir:  SIEM (10.0.1.0/24)  → SecOps Hub (10.0.2.50:443)
Permitir:  Analistas (10.0.3.0/24) → SecOps Hub (10.0.2.50:443)
Denegar:   Internet → SecOps Hub (excepto VPN analistas)
Permitir:  SecOps Hub (10.0.2.50) → EDR API (443)
Permitir:  SecOps Hub (10.0.2.50) → Firewall API (443)
```

---

## 10. Plan de implementación por fases

### Fase 1 — Ingesta (1–2 semanas) ✅ parcialmente listo

- [x] Webhook `/api/webhooks/alert`
- [ ] Desplegar SecOps Hub en servidor con HTTPS
- [ ] Configurar Splunk Alert Action → webhook
- [ ] Configurar QRadar Rule Response → script
- [ ] Probar flujo: alerta SIEM → dashboard

### Fase 2 — Triaje real (2–3 semanas)

- [ ] Integrar AbuseIPDB API en `ioc_enrichment.py`
- [ ] Integrar VirusTotal API
- [ ] Sincronizar feed CISA KEV automático
- [ ] Desactivar seed en producción

### Fase 3 — Respuesta automatizada (3–4 semanas)

- [ ] Playbook `block_ip` → API firewall
- [ ] Playbook `isolate_host` → API EDR
- [ ] Playbook `revoke_user` → Azure AD / LDAP
- [ ] Aprobación manual antes de ejecutar (opcional)

### Fase 4 — Operación continua

- [ ] PostgreSQL en lugar de SQLite
- [ ] LDAP/SSO para login
- [ ] Monitorización (Prometheus/Grafana)
- [ ] Runbooks documentados para analistas

---

## 11. Checklist de puesta en marcha

```
□ SecOps Hub desplegado con HTTPS
□ WEBHOOK_API_KEY generada y compartida con equipo SIEM
□ Splunk: al menos 1 alerta de prueba → webhook
□ QRadar: al menos 1 regla → script/API
□ Dashboard muestra incidentes reales (no solo seed)
□ Analistas pueden enriquecer IOCs
□ Admins pueden ejecutar playbooks (simulados o reales)
□ Feed de auditoría registra acciones
□ Documentación interna actualizada con URLs y claves
□ Runbook de respuesta a incidentes enlazado
```

---

## 12. Referencias

- [Manual de usuario](manual-usuario.md) — uso de la consola
- [Manual de laboratorio](manual-laboratorio.md) — Lab 6 (webhooks) y Lab 7 (flujo completo)
- [Manual de desarrollador](manual-desarrollador.md) — API y extensión de playbooks
- [Splunk Webhook Alert Actions](https://docs.splunk.com/Documentation/Splunk/latest/Alert/Webhooks)
- [QRadar Rule Responses](https://www.ibm.com/docs/en/qsip)
- [CISA KEV Feed](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
- [Microsoft Defender API](https://learn.microsoft.com/en-us/microsoft-365/security/defender-endpoint/apis-intro)
- [CrowdStrike Falcon API](https://falcon.crowdstrike.com/documentation/92/apis-and-endpoints-reference)

---

## 13. Soporte y extensión

Para implementar integraciones reales en código, los puntos de extensión son:

| Archivo | Qué modificar |
|---------|---------------|
| `backend/app/routes/webhooks.py` | Validación extra, campos adicionales (IP, hostname) |
| `backend/app/services/ioc_enrichment.py` | Sustituir simuladores por APIs reales |
| `backend/app/services/ioc_enrichment.py` → `run_playbook()` | Llamadas a firewall/EDR/AD |
| `backend/config.py` | Nuevas variables de entorno |
| `backend/app/services/seed.py` | Desactivar en producción |

Consulta el [manual de desarrollador](manual-desarrollador.md) sección 10 para añadir nuevas funcionalidades.
