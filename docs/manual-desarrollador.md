# Manual de desarrollador — SecOps Hub

## 1. Visión general

SecOps Hub es una aplicación **desacoplada** full-stack:

| Capa | Tecnología | Puerto |
|------|------------|--------|
| Frontend | React 18, Vite, TypeScript, Tailwind, Recharts | 5173 (dev) |
| Backend | Flask 3, SQLAlchemy, Flask-JWT-Extended | 5000 |
| Base de datos | SQLite | `backend/instance/secops_hub.db` |

Comunicación vía **REST JSON** con autenticación **JWT Bearer**.

---

## 2. Estructura del repositorio

```
secopsHub/
├── backend/
│   ├── config.py / run.py / wsgi.py
│   ├── requirements.txt / migrations/ / tests/
│   └── app/
│       ├── routes/     # auth, users, settings, incidents, iocs, vulns,
│       │               # playbooks, webhooks, integrations, health, frontend
│       ├── services/   # ioc_*, playbook_runners, kev_sync, pdf_report,
│       │               # oidc/ldap/auth_cookies, metrics, bootstrap...
│       ├── models/
│       └── utils/
├── frontend/src/pages/   # Login, Dashboard, IOCs, Vulns, Playbooks, Users(Admin)
├── deploy/               # nginx, caddy, systemd, prometheus, grafana
├── formacion/            # notebooks Jupyter
├── docs/
└── docker-compose.yml
```

Guía no técnica: [guia-carpetas.md](guia-carpetas.md).

---

## 3. Configuración del entorno

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python run.py
```

Variables de entorno (`.env` en `backend/`):

```env
SECRET_KEY=clave-secreta-flask-min-32-chars
JWT_SECRET_KEY=clave-jwt-min-32-chars
WEBHOOK_API_KEY=clave-webhook-produccion
DATABASE_URL=sqlite:///secops_hub.db
# Producción: postgresql+psycopg://secops:pass@localhost:5432/secops_hub
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
ENABLE_SEED=true
FLASK_ENV=development

# Sin seed: primer admin automático (password ≥ 12 chars)
# BOOTSTRAP_ADMIN_USERNAME=admin
# BOOTSTRAP_ADMIN_EMAIL=admin@secops.local
# BOOTSTRAP_ADMIN_PASSWORD=...
```

Con `FLASK_ENV=production` el arranque **falla** si las claves son las de demo o tienen menos de 32 caracteres, o si `CORS_ORIGINS` es `*`.

Crear admin sin seed:

```bash
python scripts/create_admin.py --username admin --email admin@secops.local
```

### Frontend

```bash
cd frontend
npm install
npm run dev      # Desarrollo con HMR
npm run build    # Build producción → dist/
npm run preview  # Previsualizar build
```

---

## 4. Application factory (Flask)

El patrón **factory** en `app/__init__.py`:

1. Valida secretos si `FLASK_ENV=production` (`validate_production_config`)
2. Carga configuración desde `config.py`
3. Inicializa extensiones: `CORS` (orígenes desde `CORS_ORIGINS`), `SQLAlchemy`, `JWTManager`
4. Registra blueprints bajo `/api/*`
5. Registra blueprint `frontend` para servir SPA estática
6. Ejecuta `db.create_all()`; si `ENABLE_SEED` → `seed_database()`, si no → `bootstrap_admin_if_needed()`

### Blueprints registrados

| Blueprint | Prefijo | Archivo |
|-----------|---------|---------|
| auth | `/api/auth` | `routes/auth.py` (login, refresh, logout, MFA, OIDC, register, config) |
| users | `/api/users` | `routes/users.py` |
| settings | `/api/settings` | `routes/settings.py` (webhook key) |
| incidents | `/api/incidents` | `routes/incidents.py` (+ PDF) |
| iocs | `/api/iocs` | `routes/iocs.py` |
| vulns | `/api/vulnerabilities` | `routes/vulns.py` (+ sync-kev) |
| playbooks | `/api/playbooks` | `routes/playbooks.py` (+ approvals) |
| webhooks | `/api/webhooks` | `routes/webhooks.py` |
| integrations | `/api/integrations` | `routes/integrations.py` |
| health | `/api/health`, `/health`, `/metrics` | `routes/health.py` |
| frontend | `/` | `routes/frontend.py` |

---

## 5. Modelo de datos

Ver diagrama ERD en [diagramas-uml.md](diagramas-uml.md).

### Relaciones

- `AuditLog.user_id` → `User.id` (FK nullable)
- Resto de entidades son independientes en esta versión

### Seed automático y bootstrap

`services/seed.py` → `seed_database()` crea datos demo si la tabla `users` está vacía y `ENABLE_SEED=true`.

Con `ENABLE_SEED=false`, `services/bootstrap.py` crea el primer admin desde `BOOTSTRAP_ADMIN_*` (o usar `scripts/create_admin.py`).

Para resetear en desarrollo:

```bash
# Eliminar la BD y reiniciar
rm -f backend/instance/secops_hub.db backend/secops_hub.db
python run.py
```

---

## 6. Autenticación y autorización

### Emisión de token (login)

```python
create_access_token(
    identity=str(user.id),
    additional_claims={"role": user.role, "username": user.username},
)
```

### Decoradores RBAC

| Decorador | Ubicación | Comportamiento |
|-----------|-----------|----------------|
| `@jwt_required()` | Flask-JWT-Extended | Exige token válido |
| `@admin_required` | `utils/decorators.py` | Claim `role == "admin"` |
| `@analyst_or_admin_required` | `utils/decorators.py` | Claim `role in ("admin", "analyst")` |

### Frontend — flujo JWT

1. Login → access (+ refresh); opcional cookies (`AUTH_COOKIE_MODE`)
2. Interceptor → `Authorization: Bearer` y/o credentials
3. Ante 401 → intenta `POST /api/auth/refresh`; si falla → `/login`
4. `GET /api/auth/me` y `GET /api/auth/config` al montar

Variables relevantes: `OIDC_*`, `LDAP_*`, `AUTH_COOKIE_MODE`, `PLAYBOOK_FOUR_EYES`, `ABUSEIPDB_API_KEY`, `VIRUSTOTAL_API_KEY`, `EDR_*`, `FIREWALL_*`, `AZURE_AD_*`.

---

## 7. API REST — referencia rápida

### Auth

```
POST /api/auth/login            { username, password, otp? }
POST /api/auth/refresh
POST /api/auth/logout
GET  /api/auth/me               [JWT]
GET  /api/auth/config           → cookie_mode, oidc, ldap, four_eyes
POST /api/auth/register         [JWT admin]
POST /api/auth/mfa/setup|enable|disable  [JWT]
GET  /api/auth/oidc/login
GET  /api/auth/oidc/callback
```

### Users / settings

```
GET   /api/users                [JWT admin]
PATCH /api/users/<id>           [JWT admin] { role?, is_active?, ... }
GET   /api/settings/webhook-key [JWT admin]
POST  /api/settings/webhook-key/rotate [JWT admin]
```

### Incidentes

```
GET   /api/incidents                      [JWT] ?status=active
GET   /api/incidents/<id>                 [JWT]
PATCH /api/incidents/<id>                 [JWT analyst|admin]
      { status?, assigned_to? }
      status: open | investigating | resolved | closed
      assigned_to: username existente o null/"" para desasignar
GET   /api/incidents/stats                [JWT] → KPIs + gráficos + audit feed
GET   /api/incidents/<id>/report/pdf      [JWT] → Informe PDF ejecutivo
```

### Vulnerabilidades

```
GET   /api/vulnerabilities                [JWT] ?severity=&kev_only=&status=
PATCH /api/vulnerabilities/<id>           [JWT analyst|admin] { status }
POST  /api/vulnerabilities/sync-kev       [JWT admin] { limit? } → upsert CISA KEV
```

### Webhooks

```
POST /api/webhooks/alert      [X-API-Key]
     Headers opcionales: Idempotency-Key
     Body: title?, description?, severity?, source?,
           external_id|alert_id|event_id?, src_ip|ip?, hostname|host?
     → 201 creado | 200 duplicado
```

### Salud

```
GET /api/health   (también GET /health)  → status ok|degraded, check DB
```

### IOCs

```
GET  /api/iocs                [JWT analyst|admin]
POST /api/iocs/enrich         [JWT analyst|admin] { value }
POST /api/iocs/:id/block      [JWT analyst|admin]
```

### Playbooks

```
GET  /api/playbooks                 [JWT]
POST /api/playbooks/run             [JWT admin]
     { playbook_id, params?, confirm: true, force_direct? }
     → 200 ejecutado | 202 pending_approval (4-eyes)
GET  /api/playbooks/approvals       [JWT admin]
POST /api/playbooks/approvals/<id>/approve|reject  [JWT admin]
GET  /api/integrations/status       [JWT]
```

### Códigos de respuesta habituales

| Código | Significado |
|--------|-------------|
| 200 | OK / duplicado webhook |
| 201 | Creado |
| 202 | Playbook pendiente 4-eyes |
| 400 | Datos inválidos / falta confirm |
| 401 | Auth / API Key / MFA |
| 403 | Rol insuficiente / auto-aprobación 4-eyes |
| 404 | No encontrado |
| 409 | Duplicado usuario |
| 503 | Health degraded |

---

## 8. Servicios de negocio

| Módulo | Responsabilidad |
|--------|-----------------|
| `ioc_enrichment.py` | Regex + simuladores deterministas |
| `ioc_service.py` | Orquesta live/simulado + veredicto |
| `external_clients.py` | HTTP AbuseIPDB / VirusTotal |
| `playbook_runners.py` | EDR / firewall / AD / callback |
| `kev_sync.py` | Feed CISA KEV |
| `pdf_report.py` | Informe PDF |
| `oidc_auth.py` / `ldap_auth.py` / `auth_cookies.py` | Auth avanzada |
| `metrics.py` | Prometheus |
| `settings_store.py` | `app_settings` (webhook key) |
| `bootstrap.py` / `seed.py` | Primer admin / demo |

---

## 9. Frontend — arquitectura

### Enrutamiento (`App.tsx`)

```
/login           → LoginPage (pública)
/                → DashboardPage
/iocs            → IOCsPage
/vulnerabilities → VulnerabilitiesPage
/playbooks       → PlaybooksPage
/admin           → UsersPage (AdminRoute)
*                → redirect /
```

### Proxy de desarrollo

`vite.config.ts` redirige `/api/*` a `http://localhost:5000`.

### Convenciones UI

- Clases utilitarias Tailwind + componentes en `@layer components` (`btn-primary`, `card`, `input-field`)
- Paleta: slate (fondo), emerald (acento), rose (peligro)
- Iconos: `lucide-react`

---

## 10. Añadir una nueva funcionalidad

### Ejemplo: nuevo endpoint protegido

1. **Modelo** (si aplica) → `app/models/__init__.py`
2. **Ruta** → `app/routes/nuevo.py` con blueprint
3. **Registrar** → `app/__init__.py`
4. **Servicio** → `app/services/` para lógica compleja
5. **Tipo TS** → `frontend/src/types/index.ts`
6. **Página/componente** → `frontend/src/pages/`
7. **Ruta React** → `App.tsx` + enlace en `Sidebar.tsx`
8. **Documentación** → actualizar `docs/`

### Diagramas SVG en el IDE

Los SVG de `docs/` (red, infraestructura) requieren la extensión **SVG** (`jock.svg`) para vista previa en Cursor/VS Code (`SVG: Open Preview`). Guía: [README de docs](README.md#cómo-ver-los-diagramas-svg-en-cursor--vs-code).

### Ejemplo: restricción por rol

```python
@nuevo_bp.route("/accion", methods=["POST"])
@jwt_required()
@admin_required
def accion_admin():
    ...
```

---

## 11. Despliegue

### Modo desarrollo (2 procesos)

- Backend: `python run.py`
- Frontend: `npm run dev`

### Modo unificado (1 proceso)

```bash
cd frontend && npm run build
cd ../backend && python run.py
```

Flask sirve `frontend/dist/` en `/` y la API en `/api/*`.

### Docker Compose

```bash
cp .env.docker.example .env   # secretos ≥ 32 chars
docker compose up -d
# Observabilidad:
docker compose --profile observability up -d
```

Servicios: `db` (Postgres), `backend` (Gunicorn), `frontend` (Nginx :80). Profile `observability`: Prometheus + Grafana. Ver `deploy/README.md`.

---

## 12. Testing

### Manual (curl)

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

curl http://localhost:5000/api/incidents/stats -H "Authorization: Bearer TOKEN"

curl -X POST http://localhost:5000/api/webhooks/alert \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secops-webhook-key-dev" \
  -d '{"title":"Test","severity":"high","source":"lab"}'
```

### Automatizado

```bash
cd backend
pytest
```

Tests en `backend/tests/` (auth, webhooks, four_eyes, enrich/health).

### Formación

Notebooks en `formacion/` (sin Flask para las prácticas 01–03). Ver `formacion/README.md`.

---

## 13. Dependencias principales

### Backend

`flask`, `flask-jwt-extended`, `flask-sqlalchemy`, `requests`, `reportlab`, `gunicorn`, `psycopg`, `prometheus-client`, `pyotp`, `ldap3`, `alembic`, `pytest`

### Frontend

`react`, `react-router-dom`, `axios`, `recharts`, `lucide-react`, `tailwindcss`

---

## 14. Puntos de extensión / próximos pasos

- Completar llamadas HTTP finales a EDR/firewall/Graph (scaffolding en `playbook_runners.py`)
- WebSockets para alertas en tiempo real
- Restringir `CORS_ORIGINS` en producción
- Ampliar cobertura de tests E2E

Ya implementado (no listar como futuro): MFA, OIDC, LDAP, VT/AbuseIPDB live, 4-eyes, KEV sync, Docker, Prometheus, `formacion/`.

Referencias: [requisitos.md](requisitos.md) · [casos-de-uso.md](casos-de-uso.md) · [diagramas-uml.md](diagramas-uml.md) · [runbook-operacion.md](runbook-operacion.md)
