# SecOps Hub

Plataforma web full-stack de operaciones de ciberseguridad con autenticación JWT, RBAC y consola SOC en dark mode.

## Stack

| Capa | Tecnologías |
|------|-------------|
| Backend | Flask, SQLAlchemy, Flask-JWT-Extended, SQLite |
| Frontend | React 18, Vite, TypeScript, Tailwind CSS, Recharts |
| Seguridad | JWT Bearer tokens, roles Admin/Analyst, API Key para webhooks |

## Arquitectura de red

![Flujo de red corporativa](docs/flujo_red_secops_hub.svg)

Cuatro direcciones de comunicación dentro de la red corporativa:

- **SIEM → SecOps Hub** — ingesta de alertas por webhook (`X-API-Key`)
- **Analistas ↔ SecOps Hub** — consola web vía JWT (VLAN analistas / VPN)
- **SecOps Hub → EDR** — playbooks de contención (Defender, CrowdStrike)
- **SecOps Hub → Firewall** — bloqueo de IPs (Palo Alto, pfSense)

Ver [Integración en red](docs/integracion-red.md) para Splunk/QRadar y [Despliegue producción](deploy/README.md) para Nginx/Caddy + TLS.

## Estructura

```
secopsHub/
├── backend/          # API REST Flask (dev :5000, prod vía Gunicorn)
├── frontend/         # SPA React (dev :5173, prod → dist/)
└── deploy/           # Nginx, Caddy, systemd, scripts build
```

## Credenciales de prueba

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| `admin` | `admin123` | Administrador (playbooks, registro) |
| `analyst` | `analyst123` | Analista (IOCs, dashboard, vulns) |

## Arranque local

### 1. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
python run.py
```

La API quedará disponible en `http://localhost:5000`. Al iniciar se crea la base de datos SQLite y se cargan datos de prueba automáticamente.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Abre `http://localhost:5173` e inicia sesión con las credenciales de prueba.

## Endpoints principales

### Autenticación
- `POST /api/auth/login` — Login (público)
- `GET /api/auth/me` — Perfil del usuario autenticado
- `POST /api/auth/register` — Registro (solo admin)

### Operaciones
- `GET /api/incidents` — Listado de incidentes
- `PATCH /api/incidents/<id>` — Actualizar estado y asignación (`status`, `assigned_to`)
- `GET /api/incidents/stats` — KPIs y datos del dashboard
- `GET /api/iocs` — Listado de IOCs
- `POST /api/iocs/enrich` — Enriquecimiento de IOCs (simulado)
- `POST /api/iocs/<id>/block` — Bloquear IOC
- `GET /api/vulnerabilities` — CVEs con filtros (`?severity=`, `?kev_only=true`)
- `GET /api/playbooks` — Playbooks disponibles
- `POST /api/playbooks/run` — Ejecutar playbook (solo admin)

### Webhooks
- `POST /api/webhooks/alert` — Receptor de alertas externas

### Informes
- `GET /api/incidents/<id>/report/pdf` — Exportar informe PDF del incidente (JWT)
- `GET /api/health` — Health check (DB)
- `POST /api/vulnerabilities/sync-kev` — Sincronizar catálogo CISA KEV (admin)

```bash
curl -X POST http://localhost:5000/api/webhooks/alert \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secops-webhook-key-dev" \
  -H "Idempotency-Key: splunk-evt-001" \
  -d '{"title": "Alerta externa", "severity": "high", "source": "SIEM", "src_ip": "203.0.113.10", "hostname": "fw-01"}'
```

## Variables de entorno

Copia `backend/.env.example` → `backend/.env`. Sin claves de threat intel o EDR, el sistema opera en **modo simulado** con fallback automático.

```env
SECRET_KEY=tu-clave-secreta
JWT_SECRET_KEY=tu-clave-jwt
WEBHOOK_API_KEY=tu-api-key-webhook
DATABASE_URL=sqlite:///secops_hub.db
# Producción: postgresql+psycopg://secops:pass@localhost:5432/secops_hub
CORS_ORIGINS=http://localhost:5173
ENABLE_SEED=true

# Sin seed: bootstrap del primer admin
# BOOTSTRAP_ADMIN_PASSWORD=...
# o: python scripts/create_admin.py

# Opcional — activar enriquecimiento real
ABUSEIPDB_API_KEY=
VIRUSTOTAL_API_KEY=

# Opcional — activar playbooks reales
EDR_TYPE=defender
EDR_API_TOKEN=
FIREWALL_API_URL=
AZURE_AD_TENANT_ID=
```

Estado de integraciones: `GET /api/integrations/status` (requiere JWT).

## Módulos

1. **Dashboard** — KPIs, gráficos de severidad, eventos por hora y feed de auditoría
2. **IOCs** — Triaje con enriquecimiento live (AbuseIPDB/VirusTotal) o simulado
3. **Vulnerabilidades** — Tabla CVE con filtro CISA KEV
4. **Playbooks** — Respuesta automatizada (aislar host, bloquear IP, revocar usuario)
5. **Informes PDF** — Exportación de reportes ejecutivos por incidente

## Documentación

Documentación completa en la carpeta [`docs/`](docs/README.md):

| Documento | Contenido |
|-----------|-----------|
| [Manual de usuario](docs/manual-usuario.md) | Guía de uso de la consola SOC |
| [Manual de laboratorio](docs/manual-laboratorio.md) | Ejercicios prácticos paso a paso |
| [Manual de desarrollador](docs/manual-desarrollador.md) | Arquitectura, API y despliegue |
| [Requisitos](docs/requisitos.md) | RF/RNF y trazabilidad |
| [Casos de uso](docs/casos-de-uso.md) | CU-01 a CU-10 con implementación |
| [Diagramas UML](docs/diagramas-uml.md) | Casos de uso, clases, secuencia, componentes, despliegue, ERD |
| [Integración en red](docs/integracion-red.md) | Splunk, QRadar, firewall, EDR |
| [Diccionario de términos](docs/diccionario.md) | Glosario SOC y técnico con ejemplos |
| [Ejemplos prácticos](docs/ejemplos-practicos.md) | Escenarios SOC y casos de prueba TC-01–TC-15 |
| [Roadmap integración](docs/roadmap-integracion.md) | Plan simulado → producción por fases |
| [Despliegue producción](deploy/README.md) | Nginx/Caddy, Gunicorn, TLS, firewall |

## Licencia

Proyecto de demostración — uso educativo.
