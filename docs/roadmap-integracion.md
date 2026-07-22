# Roadmap de integración — SecOps Hub

Documento maestro: idea central, flujo operativo, integraciones por producto y plan de evolución **simulado → producción**.

---

## Idea central

**SecOps Hub no sustituye a tu SIEM ni a tu EDR.** Actúa como **consola central** que recibe alertas, permite el triaje y orquesta respuestas mediante playbooks.

![Flujo de red](flujo_red_secops_hub.svg)

### Capas de comunicación

| Capa | Dirección | Mecanismo | Estado hoy |
|------|-----------|-----------|------------|
| **Ingesta** | SIEM → SecOps Hub | Webhook `POST /api/webhooks/alert` | ✅ Real |
| **Triaje** | Analista → APIs externas | `POST /api/iocs/enrich` | ⚠️ Simulado* / ✅ Live con API keys |
| **Visualización** | Analistas ↔ SecOps Hub | Dashboard JWT + consola React | ✅ Real |
| **Respuesta** | SecOps Hub → EDR/FW/AD | `POST /api/playbooks/run` | ⚠️ Simulado* / ✅ Live con config |

\* Sin variables de entorno → fallback simulado. Con claves → modo **live**.

Estado: `GET /api/integrations/status`

---

## Orden recomendado de implementación

1. **Fase 1** — Infraestructura básica (HTTPS, claves, PostgreSQL, reverse proxy)
2. **Fase 2** — Conectar SIEM (ingesta real Splunk/QRadar)
3. **Fase 3** — Triaje real (API keys threat intel)
4. **Fase 4** — Respuesta automatizada (EDR, firewall, AD)
5. **Fase 5** — Operación continua (SSO, monitorización, runbooks)

> **Esta semana (mínimo viable):** Fase 1 + una alerta de prueba Splunk/QRadar (Fase 2).

---

## Plan por fases

### Fase 1 — Infraestructura básica (lo primero)

- [ ] Desplegar SecOps Hub en servidor accesible desde la red (no localhost)
- [x] **Reverse proxy** Nginx/Caddy — ver [`deploy/`](../deploy/README.md)
- [ ] Certificado TLS (Let's Encrypt o CA interna)
- [x] Validación de `SECRET_KEY`, `JWT_SECRET_KEY` y `WEBHOOK_API_KEY` en producción (≥ 32 caracteres)
- [ ] Reglas de firewall: solo SIEM y analistas (VLAN/VPN); nada desde Internet abierto
- [x] Driver PostgreSQL (`psycopg`) + `DATABASE_URL=postgresql+psycopg://...`
- [x] Gunicorn + systemd (`deploy/systemd/secops-hub.service`)
- [x] Bootstrap admin sin seed (`BOOTSTRAP_ADMIN_*` o `scripts/create_admin.py`)
- [x] CORS restrictivo (`CORS_ORIGINS`)
- [x] PATCH de incidentes (`status`, `assigned_to`)
- [ ] Backup PostgreSQL programado (checklist en `deploy/README.md`)


### Fase 2 — Conectar el SIEM (ingesta real)

- [x] Webhook `/api/webhooks/alert` funcional
- [ ] Configurar Alert Action Splunk o Rule Response QRadar → `https://secops.empresa.local/api/webhooks/alert`
- [ ] Compartir `WEBHOOK_API_KEY` de forma segura con el equipo SIEM
- [ ] Probar alerta real de extremo a extremo (SIEM → dashboard +1 KPI)

Payload Splunk:

```json
{
  "title": "Splunk: Brute force desde $result.src_ip$",
  "description": "$result.count$ intentos",
  "severity": "high",
  "source": "Splunk"
}
```

### Fase 3 — Triaje real (scaffolding listo)

- [x] Clientes HTTP AbuseIPDB + VirusTotal (`external_clients.py`)
- [x] Orquestación live/simulado (`ioc_service.py`)
- [x] Indicador `enrichment_mode` en API y UI
- [ ] Configurar `ABUSEIPDB_API_KEY` y `VIRUSTOTAL_API_KEY` en producción
- [ ] Sincronizar catálogo CISA KEV automáticamente (hoy: seed fijo)
- [ ] `ENABLE_SEED=false` en producción

### Fase 4 — Respuesta automatizada (scaffolding listo)

- [x] Runners extensibles (`playbook_runners.py`)
- [x] Playbooks: `isolate_host`, `block_ip`, `revoke_user`, `data_scan`
- [x] Endpoint `/api/integrations/status`
- [ ] Llamadas HTTP completas a Defender / CrowdStrike / Palo Alto / Graph API
- [ ] Variables `.env`: `EDR_API_TOKEN`, `FIREWALL_API_KEY`, `AZURE_AD_TENANT_ID`, etc.
- [ ] Decidir aprobación manual antes de acciones destructivas (aislar/bloquear)

### Fase 5 — Operación continua

- [ ] SSO / LDAP para analistas (hoy: login local, sin MFA)
- [ ] Monitorización Prometheus + Grafana
- [x] Rate limiting webhook en Nginx/Caddy (config incluida en `deploy/`)
- [ ] Runbooks documentados para el equipo SOC
- [ ] Rotación periódica de `WEBHOOK_API_KEY`

---

## Flujo E2E — Exfiltración de datos

| Tiempo | Actor | Acción |
|--------|-------|--------|
| T+0 | Firewall/SIEM | Detecta 2.3 GB salida anómala |
| T+1 | Splunk | Webhook → SecOps Hub |
| T+2 | SecOps Hub | Incidente `severity=critical` |
| T+3 | Analista | KPI *Alertas activas* +1 |
| T+6 | Analista | Enriquece IP (`/api/iocs/enrich`) |
| T+8 | Analista | Verdict malicious → bloquear |
| T+10 | Admin | Playbook *Aislar Host* |
| T+12 | EDR | Host aislado (Defender API) |
| T+15 | Admin | Playbook *Revocar Usuario* |
| T+17 | AD/Azure AD | Sesiones revocadas |
| T+25 | Auditor | Feed de auditoría |

Ver [ejemplos-practicos.md](ejemplos-practicos.md).

---

## Integraciones por producto

| Producto | Ingesta | Respuesta | Mecanismo |
|----------|:-------:|:---------:|-----------|
| Splunk | ✅ | — | Alert Action → Webhook |
| QRadar | ✅ | — | Rule Response / HTTP forwarder |
| Palo Alto / pfSense | ✅ (vía SIEM) | 🔧 | Log + API XML |
| Microsoft Defender | ✅ (vía SIEM) | 🔧 | Streaming + aislamiento |
| CrowdStrike Falcon | ✅ (vía SIEM) | 🔧 | Falcon API contain |
| Active Directory | — | 🔧 | LDAP / Graph API |

---

## Requisitos de despliegue

| Requisito | Desarrollo | Producción |
|-----------|------------|------------|
| URL | `http://localhost:5000` | `https://secops.empresa.local` |
| Puerto | 5000 / 5173 | 443 (HTTPS) |
| Reverse proxy | Vite dev proxy | Nginx o Caddy |
| WSGI | `python run.py` | Gunicorn (`wsgi:app`) |
| TLS | No | Obligatorio |
| BD | SQLite | PostgreSQL |
| Seed | `ENABLE_SEED=true` | `ENABLE_SEED=false` |

### Firewall recomendado

```
Permitir:  SIEM (VLAN SOC)   → SecOps Hub :443
Permitir:  Analistas (VPN)   → SecOps Hub :443
Denegar:   Internet          → SecOps Hub
Denegar:   Cualquier origen  → Gunicorn :5000
Permitir:  SecOps Hub        → EDR / Firewall API :443
```

---

## Puntos de extensión en código

| Archivo | Función |
|---------|---------|
| `backend/app/services/external_clients.py` | Clientes AbuseIPDB + VirusTotal |
| `backend/app/services/ioc_service.py` | Enriquecimiento live/simulado |
| `backend/app/services/playbook_runners.py` | EDR, firewall, AD, callback SOAR |
| `backend/config.py` | Variables de entorno |
| `backend/.env.example` | Plantilla |
| `deploy/nginx/secops-hub.conf` | Reverse proxy + TLS + rate limit |
| `deploy/caddy/Caddyfile` | Alternativa con TLS automático |

---

## Referencias

- [Guía de despliegue](../deploy/README.md)
- [Integración en red (detalle)](integracion-red.md)
- [Ejemplos prácticos](ejemplos-practicos.md)
- [Manual desarrollador](manual-desarrollador.md)
