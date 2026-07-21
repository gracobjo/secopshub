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
│   ├── config.py                 # Configuración centralizada
│   ├── run.py                      # Entry point
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py             # Application factory
│       ├── models/__init__.py      # Modelos SQLAlchemy
│       ├── routes/                 # Blueprints Flask
│       ├── services/               # Lógica de negocio
│       └── utils/                  # Decoradores y helpers
├── frontend/
│   ├── vite.config.ts              # Proxy /api → :5000
│   └── src/
│       ├── context/                # AuthContext
│       ├── services/api.ts         # Cliente Axios + interceptores
│       ├── components/             # UI reutilizable
│       ├── pages/                  # Vistas por ruta
│       └── types/                  # Interfaces TypeScript
└── docs/                           # Documentación
```

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

Variables de entorno opcionales (`.env` en `backend/`):

```env
SECRET_KEY=clave-secreta-flask-min-32-chars
JWT_SECRET_KEY=clave-jwt-min-32-chars
WEBHOOK_API_KEY=clave-webhook-produccion
DATABASE_URL=sqlite:///secops_hub.db
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

1. Carga configuración desde `config.py`
2. Inicializa extensiones: `CORS`, `SQLAlchemy`, `JWTManager`
3. Registra blueprints bajo `/api/*`
4. Registra blueprint `frontend` para servir SPA estática
5. Ejecuta `db.create_all()` y `seed_database()` al arrancar

### Blueprints registrados

| Blueprint | Prefijo | Archivo |
|-----------|---------|---------|
| auth | `/api/auth` | `routes/auth.py` |
| incidents | `/api/incidents` | `routes/incidents.py` |
| iocs | `/api/iocs` | `routes/iocs.py` |
| vulns | `/api/vulnerabilities` | `routes/vulns.py` |
| playbooks | `/api/playbooks` | `routes/playbooks.py` |
| webhooks | `/api/webhooks` | `routes/webhooks.py` |
| frontend | `/` | `routes/frontend.py` |

---

## 5. Modelo de datos

Ver diagrama ERD en [diagramas-uml.md](diagramas-uml.md).

### Relaciones

- `AuditLog.user_id` → `User.id` (FK nullable)
- Resto de entidades son independientes en esta versión

### Seed automático

`services/seed.py` → `seed_database()` crea datos demo si la tabla `users` está vacía. Para resetear:

```bash
# Eliminar la BD y reiniciar
del backend\instance\secops_hub.db
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

1. Login → `localStorage.setItem('secops_token', token)`
2. Interceptor request → header `Authorization: Bearer <token>`
3. Interceptor response → 401 → borrar token + redirect `/login`
4. `AuthProvider` → al montar, `GET /api/auth/me` si hay token

---

## 7. API REST — referencia rápida

### Auth

```
POST /api/auth/login          { username, password }
GET  /api/auth/me             [JWT]
POST /api/auth/register       [JWT admin] { username, email, password, role? }
```

### Incidentes

```
GET /api/incidents                      [JWT] ?status=active
GET /api/incidents/<id>                 [JWT]
GET /api/incidents/stats                [JWT] → KPIs + gráficos + audit feed
GET /api/incidents/<id>/report/pdf      [JWT] → Informe PDF ejecutivo
```

### IOCs

```
GET  /api/iocs                [JWT analyst|admin]
POST /api/iocs/enrich         [JWT analyst|admin] { value }
POST /api/iocs/:id/block      [JWT analyst|admin]
```

### Vulnerabilidades

```
GET /api/vulnerabilities?severity=&kev_only=true   [JWT]
```

### Playbooks

```
GET  /api/playbooks           [JWT]
POST /api/playbooks/run       [JWT admin] { playbook_id, params? }
```

### Webhooks

```
POST /api/webhooks/alert      [X-API-Key] { title?, description?, severity?, source? }
```

### Códigos de respuesta habituales

| Código | Significado |
|--------|-------------|
| 200 | OK |
| 201 | Creado (webhook, registro) |
| 400 | Datos inválidos |
| 401 | Token ausente/inválido o API Key incorrecta |
| 403 | Rol insuficiente |
| 404 | Recurso no encontrado |
| 409 | Usuario/email duplicado |

---

## 8. Servicios de negocio

### `ioc_enrichment.py`

| Función | Descripción |
|---------|-------------|
| `detect_ioc_type()` | Clasifica IP, hash o URL por regex |
| `simulate_abuseipdb()` | Score determinístico simulado |
| `simulate_virustotal()` | Contadores simulados VT |
| `enrich_ioc()` | Orquesta enriquecimiento y veredicto |
| `run_playbook()` | Simula ejecución de playbook |

> En producción, sustituir simuladores por clientes HTTP reales a AbuseIPDB/VirusTotal con API keys en variables de entorno.

### `helpers.log_action()`

Registra acciones en `audit_logs` usando el usuario del JWT actual. Llamado desde rutas de IOCs, playbooks y registro.

---

## 9. Frontend — arquitectura

### Enrutamiento (`App.tsx`)

```
/login                    → LoginPage (pública)
/                         → DashboardPage (protegida)
/iocs                     → IOCsPage
/vulnerabilities          → VulnerabilitiesPage
/playbooks                → PlaybooksPage
*                         → redirect /
```

### Proxy de desarrollo

`vite.config.ts` redirige `/api/*` a `http://localhost:5000`, evitando problemas CORS en dev.

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

### Producción recomendada

| Componente | Recomendación |
|------------|---------------|
| WSGI | Gunicorn o Waitress (no usar `debug=True`) |
| Frontend | Nginx sirviendo `dist/` o CDN |
| BD | PostgreSQL (cambiar `DATABASE_URL`) |
| Secrets | Variables de entorno, claves ≥ 32 bytes |
| HTTPS | Obligatorio en producción |
| CORS | Restringir `origins` a dominios conocidos |

---

## 12. Testing manual con curl

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Stats (sustituir TOKEN)
curl http://localhost:5000/api/incidents/stats \
  -H "Authorization: Bearer TOKEN"

# Webhook
curl -X POST http://localhost:5000/api/webhooks/alert \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secops-webhook-key-dev" \
  -d '{"title":"Test","severity":"high"}'
```

---

## 13. Dependencias principales

### Backend (`requirements.txt`)

- `flask`, `flask-cors`, `flask-sqlalchemy`, `flask-jwt-extended`, `werkzeug`, `python-dotenv`

### Frontend (`package.json`)

- `react`, `react-dom`, `react-router-dom`, `axios`, `recharts`, `lucide-react`, `tailwindcss`

---

## 14. Puntos de extensión futuros

- Integración real con AbuseIPDB / VirusTotal
- Migraciones con Flask-Migrate (Alembic)
- WebSockets para alertas en tiempo real
- Página de registro de usuarios en frontend
- Tests automatizados (pytest + Vitest)
- Rate limiting y auditoría de webhooks
