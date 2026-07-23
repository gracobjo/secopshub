# Requisitos — SecOps Hub

Documento de especificación de requisitos funcionales (RF) y no funcionales (RNF) del sistema.

---

## 1. Alcance del sistema

SecOps Hub es una plataforma web que centraliza operaciones de ciberseguridad: autenticación con roles, monitorización de incidentes, triaje de IOCs, gestión de vulnerabilidades CISA KEV y ejecución de playbooks de respuesta, con recepción de alertas vía webhooks.

---

## 2. Actores

| Actor | Descripción |
|-------|-------------|
| **Administrador (Admin)** | Privilegios elevados: playbooks, usuarios, MFA admin, sync KEV, rotar webhook, aprobar 4-eyes |
| **Analista (Analyst)** | Operativa: dashboard, IOCs, vulnerabilidades, PDF; puede activar MFA propio |
| **Sistema externo** | SIEM/EDR que envía alertas por webhook (`X-API-Key`) |
| **IdP / LDAP** (opcional) | Proveedor OIDC o directorio LDAP para login corporativo |
| **Desarrollador** | Mantiene y extiende la plataforma |

---

## 3. Requisitos funcionales

### RF-01 — Autenticación de usuarios

| ID | RF-01 |
|----|-------|
| **Descripción** | Autenticación con usuario/contraseña local; opcionalmente LDAP; challenge MFA TOTP si está activado |
| **Prioridad** | Alta |
| **Criterio de aceptación** | Credenciales válidas → JWT (y refresh); si MFA activo sin OTP → `mfa_required` 401; inválidas → 401 |
| **Implementación** | `POST /api/auth/login`, `ldap_auth.py`, `LoginPage`, `AuthContext` |

### RF-02 — Gestión de sesión JWT

| ID | RF-02 |
|----|-------|
| **Descripción** | Access token (~8 h) + refresh token (~30 d); opcionalmente cookies httpOnly (`AUTH_COOKIE_MODE`) |
| **Prioridad** | Alta |
| **Criterio de aceptación** | Access caducado permite renovar vía `POST /api/auth/refresh`; logout invalida sesión/cookies |
| **Implementación** | Flask-JWT-Extended, `auth_cookies.py`, interceptor Axios |

### RF-03 — Control de acceso basado en roles (RBAC)

| ID | RF-03 |
|----|-------|
| **Descripción** | Permisos por roles `admin` y `analyst`; usuarios inactivos no pueden autenticarse |
| **Prioridad** | Alta |
| **Criterio de aceptación** | Endpoints restringidos → 403; `is_active=false` → login rechazado |
| **Implementación** | `@admin_required`, `@analyst_or_admin_required`, `AdminRoute` |

### RF-04 — Registro y gestión de usuarios (admin)

| ID | RF-04 |
|----|-------|
| **Descripción** | Admin crea usuarios (API y UI `/admin`), lista y modifica rol/`is_active` |
| **Prioridad** | Alta |
| **Criterio de aceptación** | Solo admin; username/email únicos; UI Admin operativa |
| **Implementación** | `POST /api/auth/register`, `GET/PATCH /api/users`, `UsersPage` |

### RF-05 — Perfil de usuario autenticado

| ID | RF-05 |
|----|-------|
| **Descripción** | Consulta de perfil y configuración de auth pública (`cookie_mode`, OIDC, LDAP, four_eyes) |
| **Prioridad** | Alta |
| **Criterio de aceptación** | `GET /api/auth/me` y `GET /api/auth/config` |
| **Implementación** | `auth.py`, `AuthProvider` |

### RF-06 — Dashboard con KPIs

| ID | RF-06 |
|----|-------|
| **Descripción** | Vista principal con métricas de seguridad en tiempo real |
| **Prioridad** | Alta |
| **Criterio de aceptación** | Muestra alertas activas, IPs bloqueadas, KEV abiertas, total incidentes |
| **Implementación** | `GET /api/incidents/stats`, `DashboardPage`, `KpiCard` |

### RF-07 — Gráficos de monitorización

| ID | RF-07 |
|----|-------|
| **Descripción** | Gráficos de distribución por severidad y eventos por hora |
| **Prioridad** | Media |
| **Criterio de aceptación** | Al menos 2 gráficos interactivos en dashboard |
| **Implementación** | Recharts en `DashboardPage` |

### RF-08 — Feed de auditoría

| ID | RF-08 |
|----|-------|
| **Descripción** | Registro visible de acciones recientes de usuarios |
| **Prioridad** | Media |
| **Criterio de aceptación** | Últimas 10 acciones con usuario, acción, fecha |
| **Implementación** | Modelo `AuditLog`, `log_action()`, dashboard stats |

### RF-09 — Listado de incidentes

| ID | RF-09 |
|----|-------|
| **Descripción** | Consulta de incidentes de seguridad registrados |
| **Prioridad** | Alta |
| **Criterio de aceptación** | Lista ordenada por fecha con severidad y estado |
| **Implementación** | `GET /api/incidents`, modelo `Incident` |

### RF-09b — Actualización de incidentes

| ID | RF-09b |
|----|--------|
| **Descripción** | Un analista o admin puede cambiar el estado y la asignación de un incidente |
| **Prioridad** | Alta |
| **Criterio de aceptación** | `PATCH` acepta `status` ∈ {open, investigating, resolved, closed} y `assigned_to` de un usuario existente; escribe audit log |
| **Implementación** | `PATCH /api/incidents/<id>`, `KpiDetailModal` |

### RF-10 — Enriquecimiento de IOCs

| ID | RF-10 |
|----|-------|
| **Descripción** | Análisis de IPs/hashes/URLs con risk score y veredicto; VirusTotal/AbuseIPDB **live** si hay API keys, si no **simulado** |
| **Prioridad** | Alta |
| **Criterio de aceptación** | Respuesta con `enrichment_mode` (`live`\|`simulated`), `sources_used`, risk_score, verdict |
| **Implementación** | `POST /api/iocs/enrich`, `ioc_service.py`, `external_clients.py`, `IOCsPage` |

### RF-11 — Bloqueo de IOCs

| ID | RF-11 |
|----|-------|
| **Descripción** | Marcar IOCs maliciosos como bloqueados y, si son IP, orquestar bloqueo en firewall |
| **Prioridad** | Media |
| **Criterio de aceptación** | Campo `blocked=true`, audit log; IPs ejecutan playbook `block_ip` tras `confirm=true` |
| **Implementación** | `POST /api/iocs/<id>/block`, `playbook_runners.block_ip` |

### RF-12 — Gestión de vulnerabilidades

| ID | RF-12 |
|----|-------|
| **Descripción** | Tabla de CVEs con filtros por severidad y flag CISA KEV |
| **Prioridad** | Alta |
| **Criterio de aceptación** | Filtros funcionan; KEV visible con badge |
| **Implementación** | `GET /api/vulnerabilities`, `VulnerabilitiesPage` |

### RF-13 — Catálogo de playbooks

| ID | RF-13 |
|----|-------|
| **Descripción** | Listado de playbooks de respuesta disponibles |
| **Prioridad** | Media |
| **Criterio de aceptación** | Muestra id, nombre, descripción y parámetros |
| **Implementación** | `GET /api/playbooks`, `PlaybooksPage` |

### RF-14 — Ejecución de playbooks (admin)

| ID | RF-14 |
|----|-------|
| **Descripción** | Solo admin ejecuta playbooks; destructivos exigen `confirm=true`; con `PLAYBOOK_FOUR_EYES` crean solicitud pendiente |
| **Prioridad** | Alta |
| **Criterio de aceptación** | Analyst → 403; sin confirm → 400; con 4-eyes → 202 `pending_approval`; otro admin aprueba/rechaza |
| **Implementación** | `POST /api/playbooks/run`, `/approvals`, `playbook_runners.py`, `PlaybooksPage` |

### RF-15 — Recepción de webhooks

| ID | RF-15 |
|----|-------|
| **Descripción** | Alertas externas con `X-API-Key`; idempotencia; deduplicación temporal; campos `src_ip`/`hostname`; IOC IP opcional |
| **Prioridad** | Alta |
| **Criterio de aceptación** | 201 creado / 200 duplicado; API Key inválida → 401; clave rotada en `app_settings` prioriza sobre `.env` |
| **Implementación** | `POST /api/webhooks/alert`, `settings_store.py` |

### RF-16 — Rutas protegidas en frontend

| ID | RF-16 |
|----|-------|
| **Descripción** | Vistas del dashboard inaccesibles sin autenticación |
| **Prioridad** | Alta |
| **Criterio de aceptación** | Redirect automático a `/login` si no hay sesión |
| **Implementación** | `ProtectedRoute`, interceptor 401 |

### RF-17 — Seed de datos iniciales

| ID | RF-17 |
|----|-------|
| **Descripción** | Datos demo si `ENABLE_SEED=true`; si no, bootstrap admin (`BOOTSTRAP_ADMIN_*` o script) |
| **Prioridad** | Baja |
| **Criterio de aceptación** | Seed o bootstrap según configuración; producción con `ENABLE_SEED=false` |
| **Implementación** | `seed_database()`, `bootstrap_admin_if_needed()`, `scripts/create_admin.py` |

### RF-18 — MFA TOTP

| ID | RF-18 |
|----|-------|
| **Descripción** | Segundo factor TOTP: setup, enable, disable |
| **Prioridad** | Alta |
| **Criterio de aceptación** | Login exige OTP si `mfa_enabled`; setup genera secret/`otpauth_uri` |
| **Implementación** | `/api/auth/mfa/*`, `pyotp`, UI Admin |

### RF-19 — SSO OIDC

| ID | RF-19 |
|----|-------|
| **Descripción** | Login Authorization Code con IdP; provisioning `auth_source=oidc` |
| **Prioridad** | Alta |
| **Criterio de aceptación** | Con `OIDC_ENABLED` el login muestra SSO; callback crea/actualiza usuario |
| **Implementación** | `oidc_auth.py`, `/api/auth/oidc/login`, `/callback` |

### RF-20 — Autenticación LDAP

| ID | RF-20 |
|----|-------|
| **Descripción** | Login LDAP (bind) y alta JIT si falla local y `LDAP_ENABLED` |
| **Prioridad** | Media |
| **Criterio de aceptación** | Usuario LDAP provisionado con `auth_source=ldap` |
| **Implementación** | `ldap_auth.py`, `ldap3` |

### RF-21 — Rotación de WEBHOOK_API_KEY

| ID | RF-21 |
|----|-------|
| **Descripción** | Admin consulta meta y rota la clave (visible una sola vez) |
| **Prioridad** | Media |
| **Criterio de aceptación** | Clave nueva en `app_settings`; SIEM debe actualizarse |
| **Implementación** | `/api/settings/webhook-key`, `UsersPage` / settings UI |

### RF-22 — Sincronización CISA KEV

| ID | RF-22 |
|----|-------|
| **Descripción** | Admin sincroniza feed KEV; opcional al arranque |
| **Prioridad** | Alta |
| **Criterio de aceptación** | `POST /api/vulnerabilities/sync-kev` upsert CVEs |
| **Implementación** | `kev_sync.py`, botón Sync en `VulnerabilitiesPage` |

### RF-23 — Actualización de estado de vulnerabilidad

| ID | RF-23 |
|----|-------|
| **Descripción** | Analyst/admin cambian estado CVE |
| **Prioridad** | Media |
| **Criterio de aceptación** | `PATCH` con status permitido |
| **Implementación** | `PATCH /api/vulnerabilities/<id>` |

### RF-24 — Informe PDF de incidente

| ID | RF-24 |
|----|-------|
| **Descripción** | Exportar informe ejecutivo PDF desde el modal KPI |
| **Prioridad** | Media |
| **Criterio de aceptación** | `GET /api/incidents/<id>/report/pdf` descarga PDF |
| **Implementación** | `pdf_report.py`, `KpiDetailModal` |

### RF-25 — Estado de integraciones

| ID | RF-25 |
|----|-------|
| **Descripción** | Consultar qué capas están live/simulated |
| **Prioridad** | Media |
| **Criterio de aceptación** | `GET /api/integrations/status` |
| **Implementación** | `integrations.py`, `integration_capabilities.py` |

### RF-26 — Health check

| ID | RF-26 |
|----|-------|
| **Descripción** | Endpoint de salud con comprobación de BD |
| **Prioridad** | Media |
| **Criterio de aceptación** | `/health` → `ok` o `degraded` (503) |
| **Implementación** | `routes/health.py` |

---

## 4. Requisitos no funcionales

### RNF-01 — Seguridad de contraseñas

| ID | RNF-01 |
|----|--------|
| **Descripción** | Las contraseñas se almacenan hasheadas, nunca en texto plano |
| **Prioridad** | Alta |
| **Implementación** | Werkzeug `generate_password_hash` / `check_password_hash` |

### RNF-02 — Comunicación autenticada API

| ID | RNF-02 |
|----|--------|
| **Descripción** | Peticiones autenticadas usan cabecera `Authorization: Bearer <token>` |
| **Prioridad** | Alta |
| **Implementación** | Interceptor Axios, `@jwt_required()` |

### RNF-03 — Expiración de tokens

| ID | RNF-03 |
|----|--------|
| **Descripción** | Los tokens JWT expiran tras un periodo configurable |
| **Prioridad** | Alta |
| **Valor actual** | 8 horas |
| **Implementación** | `JWT_ACCESS_TOKEN_EXPIRES` en `config.py` |

### RNF-04 — CORS

| ID | RNF-04 |
|----|--------|
| **Descripción** | El backend permite peticiones cross-origin en rutas API |
| **Prioridad** | Media |
| **Implementación** | `Flask-CORS` en `/api/*` |

### RNF-05 — Usabilidad (UX SOC)

| ID | RNF-05 |
|----|--------|
| **Descripción** | Interfaz dark mode profesional, responsive e intuitiva |
| **Prioridad** | Media |
| **Implementación** | Tailwind CSS, paleta slate/emerald/rose |

### RNF-06 — Esquema de base de datos

| ID | RNF-06 |
|----|--------|
| **Descripción** | Arranque con `create_all` + `ensure_schema`; migraciones Alembic disponibles |
| **Prioridad** | Media |
| **Implementación** | `db.create_all()`, `schema.py`, `backend/migrations/` |

### RNF-07 — Mantenibilidad

| ID | RNF-07 |
|----|--------|
| **Descripción** | Arquitectura desacoplada frontend/backend con blueprints modulares |
| **Prioridad** | Alta |
| **Implementación** | Flask blueprints + React SPA |

### RNF-08 — Portabilidad

| ID | RNF-08 |
|----|--------|
| **Descripción** | Ejecutable en local (Python 3.11+, Node) o Docker Compose |
| **Prioridad** | Alta |
| **Implementación** | SQLite embebido o Postgres; `docker-compose.yml` |

### RNF-09 — Trazabilidad

| ID | RNF-09 |
|----|--------|
| **Descripción** | Acciones sensibles en audit log |
| **Prioridad** | Media |
| **Implementación** | `AuditLog`, `log_action()` |

### RNF-10 — Escalabilidad

| ID | RNF-10 |
|----|--------|
| **Descripción** | PostgreSQL en producción/Compose; integraciones live vía `.env` |
| **Prioridad** | Media |
| **Implementación** | `DATABASE_URL`, clientes HTTP |

### RNF-11 — Disponibilidad (desarrollo)

| ID | RNF-11 |
|----|--------|
| **Descripción** | Backend y frontend independientes en desarrollo |
| **Prioridad** | Media |
| **Implementación** | Puertos 5000 y 5173, proxy Vite |

### RNF-12 — Internacionalización (limitada)

| ID | RNF-12 |
|----|--------|
| **Descripción** | Interfaz en español |
| **Prioridad** | Baja |
| **Implementación** | Textos en componentes React |

### RNF-13 — Observabilidad

| ID | RNF-13 |
|----|--------|
| **Descripción** | Métricas Prometheus en `/metrics`; profile Grafana opcional |
| **Prioridad** | Media |
| **Implementación** | `metrics.py`, `deploy/prometheus`, `deploy/grafana` |

### RNF-14 — Despliegue en contenedores

| ID | RNF-14 |
|----|--------|
| **Descripción** | Stack Compose: Postgres + backend + frontend (+ observability) |
| **Prioridad** | Alta |
| **Implementación** | `docker-compose.yml`, Dockerfiles |

### RNF-15 — Material formativo

| ID | RNF-15 |
|----|--------|
| **Descripción** | Notebooks Jupyter de prácticas Python SOC |
| **Prioridad** | Baja |
| **Implementación** | Carpeta `formacion/` |

---

## 5. Matriz de trazabilidad RF → Módulo

| RF | Módulo backend | Módulo frontend |
|----|----------------|-----------------|
| RF-01–05, RF-18–20 | `routes/auth.py`, `ldap_auth`, `oidc_auth`, `auth_cookies` | `LoginPage`, `AuthContext`, `UsersPage` |
| RF-06–09b, RF-24 | `routes/incidents.py`, `pdf_report` | `DashboardPage`, `KpiDetailModal` |
| RF-10–11 | `ioc_service`, `external_clients`, `ioc_enrichment` | `IOCsPage` |
| RF-12, RF-22–23 | `routes/vulns.py`, `kev_sync` | `VulnerabilitiesPage` |
| RF-13–14 | `routes/playbooks.py`, `playbook_runners` | `PlaybooksPage` |
| RF-15, RF-21 | `webhooks.py`, `settings.py` | Admin / settings |
| RF-16 | — | `ProtectedRoute`, `AdminRoute`, `api.ts` |
| RF-17 | `seed.py`, `bootstrap.py` | — |
| RF-25–26 | `integrations.py`, `health.py` | badges modo live |
| RNF-13–14 | `metrics.py`, Compose | — |
| RNF-15 | — | `formacion/*.ipynb` |

---

## 6. Restricciones y supuestos

### Restricciones

- Sin API keys de threat intel/EDR → modo **simulado** (fallback automático)
- Four-eyes opcional (`PLAYBOOK_FOUR_EYES`); por defecto puede estar desactivado
- SSO/LDAP solo si se configuran variables de entorno
- No hay WebSockets de alertas en tiempo real en esta versión

### Supuestos

- Navegador moderno; backend accesible (proxy Vite, mismo origen o Compose `:80`)
- En demo, `ENABLE_SEED=true` carga datos de prueba
- En producción: HTTPS, PostgreSQL, secretos ≥ 32 caracteres, `ENABLE_SEED=false`

---

## 7. Priorización MoSCoW

| Must | Should | Could | Won't (aún) |
|------|--------|-------|-------------|
| RF-01–03, RF-06, RF-09, RF-10 | RF-04, RF-07, RF-08, RF-11 | RF-17, RNF-15 | WebSockets tiempo real |
| RF-12, RF-14–16, RF-18 | RF-19–21, RF-23–26 | | SOAR comercial completo |
| RF-22, RNF-01–03, RNF-14 | RNF-10, RNF-13 | | |
