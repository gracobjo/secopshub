# SecOps Hub

Plataforma web full-stack de operaciones de ciberseguridad con autenticación JWT, RBAC y consola SOC en dark mode.

## Stack

| Capa | Tecnologías |
|------|-------------|
| Backend | Flask, SQLAlchemy, Flask-JWT-Extended, SQLite |
| Frontend | React 18, Vite, TypeScript, Tailwind CSS, Recharts |
| Seguridad | JWT Bearer tokens, roles Admin/Analyst, API Key para webhooks |

## Estructura

```
secopsHub/
├── backend/          # API REST Flask (puerto 5000)
└── frontend/         # SPA React (puerto 5173)
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
- `GET /api/incidents/stats` — KPIs y datos del dashboard
- `GET /api/iocs` — Listado de IOCs
- `POST /api/iocs/enrich` — Enriquecimiento de IOCs (simulado)
- `POST /api/iocs/<id>/block` — Bloquear IOC
- `GET /api/vulnerabilities` — CVEs con filtros (`?severity=`, `?kev_only=true`)
- `GET /api/playbooks` — Playbooks disponibles
- `POST /api/playbooks/run` — Ejecutar playbook (solo admin)

### Webhooks
- `POST /api/webhooks/alert` — Receptor de alertas externas

```bash
curl -X POST http://localhost:5000/api/webhooks/alert \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secops-webhook-key-dev" \
  -d '{"title": "Alerta externa", "severity": "high", "source": "SIEM"}'
```

## Variables de entorno (opcional)

Crea un archivo `.env` en `backend/`:

```env
SECRET_KEY=tu-clave-secreta
JWT_SECRET_KEY=tu-clave-jwt
WEBHOOK_API_KEY=tu-api-key-webhook
DATABASE_URL=sqlite:///secops_hub.db
```

## Módulos

1. **Dashboard** — KPIs, gráficos de severidad, eventos por hora y feed de auditoría
2. **IOCs** — Triaje y enriquecimiento simulado (AbuseIPDB / VirusTotal)
3. **Vulnerabilidades** — Tabla CVE con filtro CISA KEV
4. **Playbooks** — Automatización de respuesta (aislar host, revocar usuario, escaneo)

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

## Licencia

Proyecto de demostración — uso educativo.
