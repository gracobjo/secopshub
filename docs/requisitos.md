# Requisitos — SecOps Hub

Documento de especificación de requisitos funcionales (RF) y no funcionales (RNF) del sistema.

---

## 1. Alcance del sistema

SecOps Hub es una plataforma web que centraliza operaciones de ciberseguridad: autenticación con roles, monitorización de incidentes, triaje de IOCs, gestión de vulnerabilidades CISA KEV y ejecución de playbooks de respuesta, con recepción de alertas vía webhooks.

---

## 2. Actores

| Actor | Descripción |
|-------|-------------|
| **Administrador (Admin)** | Usuario con privilegios elevados: ejecuta playbooks, registra usuarios |
| **Analista (Analyst)** | Usuario operativo: monitoriza, analiza IOCs y vulnerabilidades |
| **Sistema externo** | SIEM, EDR u otra herramienta que envía alertas por webhook |
| **Desarrollador** | Mantiene y extiende la plataforma (fuera del alcance funcional directo) |

---

## 3. Requisitos funcionales

### RF-01 — Autenticación de usuarios

| ID | RF-01 |
|----|-------|
| **Descripción** | El sistema debe permitir a los usuarios autenticarse con nombre de usuario y contraseña |
| **Prioridad** | Alta |
| **Criterio de aceptación** | Credenciales válidas devuelven JWT; inválidas devuelven 401 |
| **Implementación** | `POST /api/auth/login`, `AuthContext.login()`, `LoginPage` |

### RF-02 — Gestión de sesión JWT

| ID | RF-02 |
|----|-------|
| **Descripción** | Las sesiones deben basarse en tokens JWT con tiempo de expiración |
| **Prioridad** | Alta |
| **Criterio de aceptación** | Token expira a las 8 h; peticiones sin token válido reciben 401 |
| **Implementación** | `Flask-JWT-Extended`, `JWT_ACCESS_TOKEN_EXPIRES`, interceptor Axios |

### RF-03 — Control de acceso basado en roles (RBAC)

| ID | RF-03 |
|----|-------|
| **Descripción** | El sistema debe diferenciar permisos entre roles `admin` y `analyst` |
| **Prioridad** | Alta |
| **Criterio de aceptación** | Endpoints restringidos devuelven 403 si el rol no es suficiente |
| **Implementación** | `@admin_required`, `@analyst_or_admin_required`, claims JWT |

### RF-04 — Registro de usuarios (admin)

| ID | RF-04 |
|----|-------|
| **Descripción** | Un administrador puede registrar nuevos usuarios con rol asignado |
| **Prioridad** | Media |
| **Criterio de aceptación** | Solo admin puede llamar a register; username/email únicos |
| **Implementación** | `POST /api/auth/register` |

### RF-05 — Perfil de usuario autenticado

| ID | RF-05 |
|----|-------|
| **Descripción** | El usuario autenticado puede consultar su perfil |
| **Prioridad** | Alta |
| **Criterio de aceptación** | `GET /api/auth/me` devuelve id, username, email, role |
| **Implementación** | `auth.py`, `AuthProvider.fetchUser()` |

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
| **Descripción** | Análisis de IPs/hashes/URLs con puntuación de riesgo y veredicto |
| **Prioridad** | Alta |
| **Criterio de aceptación** | Devuelve risk_score, verdict, datos VT/AbuseIPDB |
| **Implementación** | `POST /api/iocs/enrich`, `ioc_enrichment.py`, `IOCsPage` |

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
| **Descripción** | Solo admin puede ejecutar playbooks de respuesta |
| **Prioridad** | Alta |
| **Criterio de aceptación** | Analyst recibe 403; admin recibe resultado de ejecución |
| **Implementación** | `POST /api/playbooks/run`, `run_playbook()` |

### RF-15 — Recepción de webhooks

| ID | RF-15 |
|----|-------|
| **Descripción** | Endpoint para recibir alertas externas autenticadas por API Key |
| **Prioridad** | Alta |
| **Criterio de aceptación** | Alerta válida crea incidente; API Key inválida → 401 |
| **Implementación** | `POST /api/webhooks/alert`, header `X-API-Key` |

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
| **Descripción** | Creación automática de usuarios demo y datos de prueba |
| **Prioridad** | Baja |
| **Criterio de aceptación** | Al primer arranque existen admin, analyst, incidentes, IOCs, CVEs |
| **Implementación** | `seed_database()` en `create_app()` |

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

### RNF-06 — Rendimiento de arranque

| ID | RNF-06 |
|----|--------|
| **Descripción** | Creación automática de esquema BD sin migraciones manuales |
| **Prioridad** | Media |
| **Implementación** | `db.create_all()` al iniciar |

### RNF-07 — Mantenibilidad

| ID | RNF-07 |
|----|--------|
| **Descripción** | Arquitectura desacoplada frontend/backend con blueprints modulares |
| **Prioridad** | Alta |
| **Implementación** | Flask blueprints + React SPA separados |

### RNF-08 — Portabilidad

| ID | RNF-08 |
|----|--------|
| **Descripción** | Ejecutable en entorno local con Python 3.11+ y Node.js |
| **Prioridad** | Alta |
| **Implementación** | SQLite embebido, sin dependencias externas obligatorias |

### RNF-09 — Trazabilidad

| ID | RNF-09 |
|----|--------|
| **Descripción** | Acciones sensibles quedan registradas en log de auditoría |
| **Prioridad** | Media |
| **Implementación** | `AuditLog`, `log_action()` |

### RNF-10 — Escalabilidad (diseño)

| ID | RNF-10 |
|----|--------|
| **Descripción** | Preparado para sustituir SQLite por PostgreSQL y APIs simuladas por reales |
| **Prioridad** | Baja |
| **Implementación** | `DATABASE_URL` configurable, servicios desacoplados |

### RNF-11 — Disponibilidad (desarrollo)

| ID | RNF-11 |
|----|--------|
| **Descripción** | Backend y frontend pueden ejecutarse de forma independiente |
| **Prioridad** | Media |
| **Implementación** | Puertos 5000 y 5173, proxy Vite |

### RNF-12 — Internacionalización (limitada)

| ID | RNF-12 |
|----|--------|
| **Descripción** | Interfaz en español |
| **Prioridad** | Baja |
| **Implementación** | Textos hardcoded en español en componentes React |

---

## 5. Matriz de trazabilidad RF → Módulo

| RF | Módulo backend | Módulo frontend |
|----|----------------|-----------------|
| RF-01–05 | `routes/auth.py` | `AuthContext`, `LoginPage` |
| RF-06–09b | `routes/incidents.py` | `DashboardPage`, `KpiDetailModal` |
| RF-10–11 | `routes/iocs.py`, `ioc_enrichment.py` | `IOCsPage` |
| RF-12 | `routes/vulns.py` | `VulnerabilitiesPage` |
| RF-13–14 | `routes/playbooks.py` | `PlaybooksPage` |
| RF-15 | `routes/webhooks.py` | Documentado en Playbooks |
| RF-16 | — | `ProtectedRoute`, `api.ts` |
| RF-17 | `services/seed.py`, `services/bootstrap.py` | — |

---

## 6. Restricciones y supuestos

### Restricciones

- Enriquecimiento de IOCs es **simulado** (no requiere API keys externas en demo)
- No hay MFA ni OAuth en esta versión
- Registro de usuarios solo vía API (sin UI)

### Supuestos

- Usuario dispone de navegador moderno
- Backend accesible desde frontend (proxy o mismo origen)
- Datos de vulnerabilidades e incidentes son de demostración

---

## 7. Priorización MoSCoW

| Must | Should | Could | Won't (v1) |
|------|--------|-------|------------|
| RF-01, RF-02, RF-03 | RF-07, RF-08 | RF-17 | OAuth / SSO |
| RF-06, RF-09, RF-10 | RF-11, RF-13 | | MFA |
| RF-12, RF-14, RF-15 | RF-04 | | Integración real VT/AbuseIPDB |
| RF-16 | | | WebSockets tiempo real |
