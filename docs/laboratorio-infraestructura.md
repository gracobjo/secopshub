# Laboratorio de infraestructura — SecOps Hub

Guía para **montar desde cero** un laboratorio SOC cuando aún no hay SIEM, EDR ni firewall corporativos. El objetivo es tener una red de prácticas donde SecOps Hub reciba alertas reales (de un SIEM ligero) y pueda ejercitar triaje y playbooks.

**Audiencia:** DevSecOps, formadores, equipos que arrancan un SOC de laboratorio.  
**Duración estimada:** 1–2 días (pasos 1–3); ampliación opcional el resto de la semana.  
**Prerrequisito de código:** repositorio `secopshub` clonado (P0–P4 ya incluidos).

---

## 1. Idea del laboratorio

SecOps Hub **no sustituye** al SIEM ni al EDR. En el lab:

1. Un **SIEM ligero** genera alertas.
2. Esas alertas llegan por **webhook** a SecOps Hub.
3. El analista **tria** IOCs y decide respuesta.
4. Los playbooks pueden ir a un **callback lab** (n8n) o, más adelante, a APIs reales.

```
┌─────────────┐     logs      ┌──────────┐     webhook      ┌─────────────┐
│ Activo lab  │──────────────►│ SIEM lab │─────────────────►│ SecOps Hub  │
│ (agent)     │               │ (Wazuh)  │   X-API-Key      │ :443 / :80  │
└─────────────┘               └──────────┘                  └──────┬──────┘
                                                                   │
                     analistas (navegador) ◄── HTTPS/JWT ──────────┤
                                                                   │
                     n8n / mock  ◄── playbook block_ip (opcional) ──┘
```

### Qué NO hace falta al principio

- Splunk Enterprise / QRadar de producción  
- CrowdStrike / Microsoft Defender for Endpoint  
- Palo Alto de producción  
- Exposición a Internet  

Esos se sustituyen después; el **contrato** (webhook + JWT + playbooks) ya está en el producto.

---

## 2. Requisitos de hardware y software

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| CPU | 2 vCPU | 4 vCPU |
| RAM | 8 GB | 16 GB (Wazuh + Hub cómodos) |
| Disco | 40 GB | 80 GB |
| SO | Ubuntu 22.04+ / Debian 12 | Igual |
| Software | Docker Engine + Compose v2 | + `git`, `curl`, `openssl` |

### Topologías posibles

| Escenario | Cómo |
|-----------|------|
| **Un solo PC** | Docker: SecOps Hub; Wazuh All-in-One en otra carpeta o VM ligera |
| **Proxmox / ESXi** | VM `secops` (4 GB) + VM `wazuh` (8 GB) |
| **Solo Hub primero** | Pasos 1–2; SIEM el día siguiente |

Nombre sugerido en lab: `secops.lab.local` (añadir a `/etc/hosts` o DNS interno).

---

## 3. Paso 1 — SecOps Hub con Docker Compose

### 3.1 Clonar y preparar secretos

```bash
git clone https://github.com/gracobjo/secopshub.git
cd secopshub
cp .env.docker.example .env
```

Editar `.env` (obligatorio cambiar valores):

```bash
# Generar tres secretos
openssl rand -hex 32   # → SECRET_KEY
openssl rand -hex 32   # → JWT_SECRET_KEY
openssl rand -hex 32   # → WEBHOOK_API_KEY
```

Ejemplo de `.env` de laboratorio:

```env
SECRET_KEY=<hex-32-bytes>
JWT_SECRET_KEY=<hex-32-bytes>
WEBHOOK_API_KEY=<hex-32-bytes>
BOOTSTRAP_ADMIN_PASSWORD=LabAdminChangeMe12
POSTGRES_PASSWORD=secops_lab_change_me
CORS_ORIGINS=http://localhost,http://secops.lab.local,http://127.0.0.1
ENABLE_SEED=false
PLAYBOOK_FOUR_EYES=false
```

> En lab con un solo admin, `PLAYBOOK_FOUR_EYES=false` evita bloquear playbooks. En ejercicios de 4-eyes, créalo un segundo admin y pon `true`.

### 3.2 Arrancar

```bash
docker compose up -d --build
docker compose ps
curl -s http://127.0.0.1/health
```

| URL | Uso |
|-----|-----|
| http://localhost | Consola web |
| http://localhost/api/health | Health check |
| http://localhost/metrics | Prometheus (si scrapeas el backend) |

Login: usuario `admin` + la `BOOTSTRAP_ADMIN_PASSWORD` del `.env`.

### 3.3 Observabilidad opcional

```bash
docker compose --profile observability up -d
```

- Prometheus: http://localhost:9090  
- Grafana: http://localhost:3000 (admin/admin por defecto)

Más detalle: [runbook-operacion.md](runbook-operacion.md).

### 3.4 Verificación del paso 1

- [ ] `docker compose ps` muestra `backend`, `frontend`, `db` healthy  
- [ ] Login admin funciona  
- [ ] `POST /api/webhooks/alert` con `X-API-Key` crea un incidente (ver más abajo)

Prueba manual del webhook:

```bash
source .env   # o exporta WEBHOOK_API_KEY a mano
curl -s -X POST http://127.0.0.1/api/webhooks/alert \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $WEBHOOK_API_KEY" \
  -H "Idempotency-Key: lab-test-001" \
  -d '{
    "title": "Lab: prueba webhook",
    "severity": "high",
    "source": "lab-manual",
    "src_ip": "203.0.113.10",
    "hostname": "lab-host-01",
    "external_id": "lab-test-001"
  }'
```

En el dashboard debe subir **Alertas activas**.

---

## 4. Paso 2 — Red de laboratorio

### 4.1 Acceso en LAN

1. Anota la IP del host: `ip -4 addr` / `hostname -I`.
2. En clientes del lab:  
   `echo "<IP> secops.lab.local" | sudo tee -a /etc/hosts`
3. Ajusta `CORS_ORIGINS` para incluir `http://secops.lab.local` y recrea el backend:

```bash
docker compose up -d backend
```

4. Firewall del host (ejemplo ufw):

```bash
sudo ufw allow from 192.168.1.0/24 to any port 80 proto tcp comment "Lab SOC"
# Más adelante solo 443 con TLS
```

### 4.2 TLS (cuando el lab deje de ser “solo localhost”)

Usar Caddy o Nginx del directorio `deploy/` con certificado de CA interna o `tls internal` en Caddy. Ver [deploy/README.md](../deploy/README.md).

Hasta tener TLS, limita el acceso a la subred del laboratorio.

---

## 5. Paso 3 — SIEM de laboratorio (Wazuh → webhook)

Wazuh es la opción más directa para un lab gratuito con agents y reglas.

### 5.1 Despliegue Wazuh (visión)

Opciones:

| Opción | Comentario |
|--------|------------|
| **Wazuh Docker** (oficial) | All-in-One o stack multi-contenedor; documentación en docs.wazuh.com |
| **VM appliance** | Una VM dedicada `wazuh.lab.local` |
| **Wazuh central + agent** | Agent en la misma VM de SecOps o en un Ubuntu de prueba |

No se incluye el compose de Wazuh en este repo (es un producto aparte). Instálalo siguiendo la guía oficial *Wazuh Docker deployment* o el instalador asistido.

Arquitectura lab:

```
[Ubuntu lab + wazuh-agent] ──► [Wazuh manager] ──HTTP POST──► [SecOps Hub /api/webhooks/alert]
```

### 5.2 Agent de prueba

1. Instala el agent Wazuh en un Ubuntu de lab.
2. Apúntalo al manager.
3. Genera eventos (SSH fallido, instalación de paquete, etc.) hasta ver alertas en Wazuh Dashboard.

### 5.3 Integración webhook hacia SecOps Hub

Configura una **integración / active response / script** (según versión Wazuh) que, ante una regla elegida (p. ej. múltiples fallos SSH), envíe:

```http
POST http://secops.lab.local/api/webhooks/alert
Content-Type: application/json
X-API-Key: <WEBHOOK_API_KEY>
Idempotency-Key: wazuh-<alert_id>

{
  "title": "Wazuh: <rule_description>",
  "description": "<full_log o agent.name>",
  "severity": "high",
  "source": "Wazuh",
  "external_id": "wazuh-<alert_id>",
  "src_ip": "<srcip>",
  "hostname": "<agent.name>"
}
```

Mapeo orientativo de severidad Wazuh → SecOps:

| Nivel Wazuh (aprox.) | `severity` |
|----------------------|------------|
| ≥ 12 | `critical` |
| 7–11 | `high` |
| 4–6 | `medium` |
| &lt; 4 | `low` |

Script de ejemplo (conceptual, adaptar rutas y parser JSON de Wazuh):

```bash
#!/usr/bin/env bash
# /var/ossec/integrations/custom-secops.py se suele preferir en Python;
# este curl ilustra el contrato HTTP.
SECOPS_URL="http://secops.lab.local/api/webhooks/alert"
API_KEY="REEMPLAZAR"

curl -sS -X POST "$SECOPS_URL" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -H "Idempotency-Key: wazuh-${ALERT_ID}" \
  -d "{\"title\":\"Wazuh: ${RULE_DESC}\",\"severity\":\"high\",\"source\":\"Wazuh\",\"external_id\":\"wazuh-${ALERT_ID}\",\"src_ip\":\"${SRC_IP}\",\"hostname\":\"${AGENT_NAME}\"}"
```

### 5.4 Verificación E2E SIEM → Hub

1. Fuerza la condición de la regla (p. ej. `ssh root@lab-host` con password incorrecta varias veces).
2. Confirma la alerta en Wazuh.
3. En SecOps Hub: KPI **Alertas activas** +1, origen `Wazuh`, `src_ip` relleno.
4. Reenvío con el mismo `external_id` / `Idempotency-Key` → respuesta `duplicate: true` (no duplica incidente).

---

## 6. Paso 4 — Callback de playbooks (n8n u otro mock)

Sin firewall real, valida el camino **Hub → automatización**:

1. Despliega [n8n](https://docs.n8n.io/hosting/) en Docker en la misma red lab.
2. Crea un webhook `POST /webhook/block-ip` que solo registre el JSON.
3. En el `.env` de SecOps Hub:

```env
PLAYBOOK_CALLBACK_URL=http://n8n:5678/webhook/block-ip
# Si n8n está en el host:
# PLAYBOOK_CALLBACK_URL=http://host.docker.internal:5678/webhook/block-ip
FIREWALL_TYPE=generic
```

4. Reinicia backend, comprueba `GET /api/integrations/status` → `respuesta.executable.block_ip: true`.
5. Ejecuta playbook **Bloquear IP** (o bloquea un IOC IP malicioso).
6. Verifica la petición en el historial de n8n.

---

## 7. Paso 5 — Ampliaciones opcionales del lab

| Ampliación | Cómo |
|------------|------|
| **Threat intel live** | Cuentas free AbuseIPDB + VirusTotal → claves en `.env` ([threat-intel.md](threat-intel.md)) |
| **Sync CISA KEV** | Admin → Vulnerabilidades → Sync CISA KEV |
| **SSO lab** | Keycloak en Docker + `OIDC_*` ([runbook-operacion.md](runbook-operacion.md)) |
| **MFA** | Admin → generar TOTP |
| **pfSense lab** | VM pfSense + API o seguir con callback n8n |
| **Segundo admin / 4-eyes** | `PLAYBOOK_FOUR_EYES=true` + usuario admin2 |

Camino hacia producción corporativa: [integracion-red.md](integracion-red.md) y [roadmap-integracion.md](roadmap-integracion.md).

---

## 8. Checklist de aceptación del laboratorio

### Nivel A — Hub solo

- [ ] Compose arriba; health OK  
- [ ] Admin bootstrap login  
- [ ] Webhook manual crea incidente + IOC opcional  

### Nivel B — Ingesta SIEM

- [ ] Wazuh (u otro SIEM lab) instalado  
- [ ] Al menos un agent reportando  
- [ ] Alerta automática → incidente en SecOps Hub  
- [ ] Idempotencia verificada  

### Nivel C — Respuesta lab

- [ ] Callback n8n/mock recibe `block_ip`  
- [ ] Enrich IOC (simulado o live)  
- [ ] (Opcional) 4-eyes con dos admins  

Cuando A+B estén verdes, el laboratorio **ya es una red real de prácticas**. El resto es conectar productos más grandes sin cambiar el diseño de SecOps Hub.

---

## 9. Problemas frecuentes

| Síntoma | Qué revisar |
|---------|-------------|
| Webhook 401 | `WEBHOOK_API_KEY` distinta a la del SIEM; clave rotada en Admin |
| CORS en navegador | `CORS_ORIGINS` debe listar el origen exacto (`http://secops.lab.local`) |
| SIEM no alcanza al Hub | Firewall, misma red Docker/`host`, URL correcta (no `localhost` desde otra VM) |
| Duplicados de alertas | Usa `external_id` o `Idempotency-Key` estable por evento |
| Playbook “simulated” | Falta `PLAYBOOK_CALLBACK_URL` o credenciales EDR/FW |
| 4-eyes bloquea todo | Solo hay un admin, o pon `PLAYBOOK_FOUR_EYES=false` en lab |

---

## 10. Referencias

| Documento | Contenido |
|-----------|-----------|
| [runbook-operacion.md](runbook-operacion.md) | Docker, MFA, OIDC, métricas, rotación webhook |
| [integracion-red.md](integracion-red.md) | Splunk, QRadar, EDR, firewall en red corporativa |
| [manual-laboratorio.md](manual-laboratorio.md) | Ejercicios de uso de la consola (no de infra) |
| [deploy/README.md](../deploy/README.md) | Producción Nginx/Caddy/systemd |
| [threat-intel.md](threat-intel.md) | API keys y cuotas |
| Wazuh docs | https://documentation.wazuh.com/ |

---

## 11. Orden sugerido de la primera semana

| Día | Entregable |
|-----|------------|
| 1 | Paso 1: Hub en Docker + webhook manual |
| 2 | Paso 2: hostname lab + acceso LAN |
| 3–4 | Paso 3: Wazuh + agent + alerta → Hub |
| 5 | Paso 4: n8n callback + un playbook |
| Después | Threat intel / OIDC / acercamiento a stack corporativo |
