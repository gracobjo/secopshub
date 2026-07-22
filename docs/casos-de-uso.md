# Casos de uso — SecOps Hub

Documento de casos de uso con descripción, flujos, actores y **mapeo a la implementación** en código.

---

## 1. Diagrama general de casos de uso

Ver diagrama completo en [diagramas-uml.md#1-diagrama-de-casos-de-uso](diagramas-uml.md).

---

## CU-01 — Iniciar sesión

| Campo | Valor |
|-------|-------|
| **Actor** | Admin, Analyst |
| **Descripción** | El usuario accede al sistema con credenciales válidas |
| **Precondiciones** | Usuario registrado en BD |
| **Postcondiciones** | Token JWT almacenado; redirección al dashboard |
| **RF asociados** | RF-01, RF-02, RF-16 |

### Flujo principal

1. Usuario accede a `/login`
2. Introduce username y password
3. Frontend envía `POST /api/auth/login`
4. Backend valida credenciales con `User.check_password()`
5. Backend genera JWT con claims `role` y `username`
6. Frontend guarda token en `localStorage` (`secops_token`)
7. Usuario es redirigido al dashboard

### Flujo alternativo — Credenciales inválidas

3a. Backend responde 401  
4a. Frontend muestra error en formulario

### Implementación

| Capa | Archivo | Elemento |
|------|---------|----------|
| Backend | `app/routes/auth.py` | `login()` |
| Backend | `app/models/__init__.py` | `User.check_password()` |
| Frontend | `src/pages/LoginPage.tsx` | Formulario login |
| Frontend | `src/context/AuthContext.tsx` | `login()` |
| Frontend | `src/services/api.ts` | Cliente Axios |

---

## CU-02 — Cerrar sesión

| Campo | Valor |
|-------|-------|
| **Actor** | Admin, Analyst |
| **Postcondiciones** | Token eliminado; usuario en pantalla login |

### Flujo principal

1. Usuario pulsa "Cerrar sesión" en Sidebar
2. `AuthContext.logout()` elimina token de localStorage
3. Navegación a `/login`

### Implementación

| Capa | Archivo |
|------|---------|
| Frontend | `src/components/Sidebar.tsx` |
| Frontend | `src/context/AuthContext.tsx` → `logout()` |

---

## CU-03 — Consultar dashboard SOC

| Campo | Valor |
|-------|-------|
| **Actor** | Admin, Analyst |
| **Precondiciones** | Sesión activa |
| **RF asociados** | RF-06, RF-07, RF-08 |

### Flujo principal

1. Usuario navega a `/`
2. `ProtectedRoute` verifica autenticación
3. Frontend llama `GET /api/incidents/stats` con JWT
4. Backend calcula KPIs, distribución severidad, eventos/hora, audit feed
5. `DashboardPage` renderiza tarjetas KPI y gráficos Recharts

### Implementación

| Capa | Archivo |
|------|---------|
| Backend | `app/routes/incidents.py` → `dashboard_stats()` |
| Frontend | `src/pages/DashboardPage.tsx` |
| Frontend | `src/components/KpiCard.tsx` |

---

## CU-04 — Enriquecer indicador de compromiso (IOC)

| Campo | Valor |
|-------|-------|
| **Actor** | Admin, Analyst |
| **Precondiciones** | Rol analyst o admin |
| **RF asociados** | RF-10 |

### Flujo principal

1. Usuario accede a `/iocs`
2. Pega IP, hash o URL en formulario
3. Frontend envía `POST /api/iocs/enrich` con `{ value }`
4. Backend detecta tipo con `detect_ioc_type()`
5. Backend consulta simuladores VT y AbuseIPDB (si IP)
6. Backend calcula `risk_score` y `verdict`
7. Backend persiste/actualiza registro en tabla `iocs`
8. Backend registra acción en `audit_logs`
9. Frontend muestra panel de resultados

### Flujo alternativo — Valor vacío

3a. Backend responde 400 "Valor IOC requerido"

### Implementación

| Capa | Archivo |
|------|---------|
| Backend | `app/routes/iocs.py` → `enrich()` |
| Backend | `app/services/ioc_enrichment.py` |
| Backend | `app/utils/decorators.py` → `@analyst_or_admin_required` |
| Frontend | `src/pages/IOCsPage.tsx` |

---

## CU-05 — Bloquear IOC malicioso

| Campo | Valor |
|-------|-------|
| **Actor** | Admin, Analyst |
| **Precondiciones** | IOC con verdict `malicious`, `blocked=false` |
| **RF asociados** | RF-11 |

### Flujo principal

1. Usuario pulsa "Bloquear" en fila de tabla IOCs
2. Frontend envía `POST /api/iocs/:id/block`
3. Backend actualiza `IOC.blocked = True`
4. Se registra en audit log
5. Tabla se refresca

### Implementación

| Capa | Archivo |
|------|---------|
| Backend | `app/routes/iocs.py` → `block_ioc()` |
| Frontend | `src/pages/IOCsPage.tsx` → `handleBlock()` |

---

## CU-06 — Consultar y filtrar vulnerabilidades

| Campo | Valor |
|-------|-------|
| **Actor** | Admin, Analyst |
| **RF asociados** | RF-12 |

### Flujo principal

1. Usuario accede a `/vulnerabilities`
2. Frontend llama `GET /api/vulnerabilities` con filtros opcionales
3. Backend aplica filtros `severity` y `kev_only`
4. Tabla muestra CVEs ordenados por CVSS descendente

### Flujos alternativos

- Usuario selecciona severidad → recarga con `?severity=critical`
- Usuario activa "Solo CISA KEV" → `?kev_only=true`

### Implementación

| Capa | Archivo |
|------|---------|
| Backend | `app/routes/vulns.py` → `list_vulnerabilities()` |
| Frontend | `src/pages/VulnerabilitiesPage.tsx` |

---

## CU-07 — Ejecutar playbook de respuesta

| Campo | Valor |
|-------|-------|
| **Actor** | Admin |
| **Precondiciones** | Rol admin |
| **RF asociados** | RF-14 |

### Flujo principal

1. Admin accede a `/playbooks`
2. Rellena parámetros (hostname, username, target)
3. Pulsa "Ejecutar" en playbook deseado
4. Frontend envía `POST /api/playbooks/run` con `{ playbook_id, params }`
5. Backend verifica `@admin_required`
6. `run_playbook()` simula ejecución
7. Resultado mostrado en panel de resultados
8. Acción registrada en audit log

### Flujo alternativo — Usuario analyst

3a. Botón ejecutar deshabilitado en UI  
4a. Si intenta vía API directa → 403

### Implementación

| Capa | Archivo |
|------|---------|
| Backend | `app/routes/playbooks.py` → `run()` |
| Backend | `app/services/ioc_enrichment.py` → `run_playbook()` |
| Frontend | `src/pages/PlaybooksPage.tsx` |

---

## CU-08 — Recibir alerta vía webhook

| Campo | Valor |
|-------|-------|
| **Actor** | Sistema externo (SIEM/EDR) |
| **Precondiciones** | API Key válida en header |
| **RF asociados** | RF-15 |

### Flujo principal

1. Sistema externo envía `POST /api/webhooks/alert`
2. Incluye header `X-API-Key: <clave>`
3. Backend valida clave contra `WEBHOOK_API_KEY`
4. Backend crea registro `Incident` con datos del body
5. Responde 201 con incidente creado
6. Incidente visible en dashboard (KPIs actualizados)

### Flujo alternativo — API Key inválida

3a. Backend responde 401

### Implementación

| Capa | Archivo |
|------|---------|
| Backend | `app/routes/webhooks.py` → `receive_alert()` |
| Backend | `app/utils/helpers.py` → `get_webhook_api_key()` |
| Backend | `config.py` → `WEBHOOK_API_KEY` |

---

## CU-09 — Registrar nuevo usuario (admin)

| Campo | Valor |
|-------|-------|
| **Actor** | Admin |
| **RF asociados** | RF-04 |

### Flujo principal

1. Admin autenticado envía `POST /api/auth/register`
2. Body: `{ username, email, password, role }`
3. Backend verifica rol admin
4. Crea usuario con password hasheado
5. Responde 201

> **Nota:** No existe UI para este caso de uso en v1; solo accesible vía API.

### Implementación

| Capa | Archivo |
|------|---------|
| Backend | `app/routes/auth.py` → `register()` |

---

## CU-10 — Restablecer sesión tras expiración

| Campo | Valor |
|-------|-------|
| **Actor** | Admin, Analyst |
| **Disparador** | Token JWT expirado (8 h) o inválido |

### Flujo principal

1. Usuario realiza petición API con token expirado
2. Backend responde 401
3. Interceptor Axios elimina token
4. Redirección automática a `/login`

### Implementación

| Capa | Archivo |
|------|---------|
| Frontend | `src/services/api.ts` → interceptor response |
| Backend | `config.py` → `JWT_ACCESS_TOKEN_EXPIRES` |

---

## CU-11 — Actualizar estado y asignación de incidente

| Campo | Valor |
|-------|-------|
| **Actor** | Admin, Analyst |
| **Disparador** | Modal de detalle KPI en el dashboard |
| **Precondiciones** | Usuario autenticado; incidente existente |

### Flujo principal

1. Usuario abre KPI «Alertas activas» o «Total incidentes»
2. Cambia `status` y/o `assigned_to` en la fila del incidente
3. Pulsa **Guardar**
4. Frontend llama `PATCH /api/incidents/<id>`
5. Backend valida estado permitido y que el username exista (si se asigna)
6. Persiste cambios, escribe audit log y responde 200
7. UI refresca KPIs; si el incidente deja de estar activo, sale de «Alertas activas»

### Implementación

| Capa | Archivo |
|------|---------|
| Backend | `app/routes/incidents.py` → `update_incident()` |
| Frontend | `KpiDetailModal.tsx`, `services/incidents.ts` |

---

## 2. Resumen de casos de uso

| ID | Caso de uso | Actor | Implementado |
|----|-------------|-------|:------------:|
| CU-01 | Iniciar sesión | Admin, Analyst | ✓ |
| CU-02 | Cerrar sesión | Admin, Analyst | ✓ |
| CU-03 | Consultar dashboard | Admin, Analyst | ✓ |
| CU-04 | Enriquecer IOC | Admin, Analyst | ✓ |
| CU-05 | Bloquear IOC | Admin, Analyst | ✓ |
| CU-06 | Filtrar vulnerabilidades | Admin, Analyst | ✓ |
| CU-07 | Ejecutar playbook | Admin | ✓ |
| CU-08 | Recibir webhook | Sistema externo | ✓ |
| CU-09 | Registrar usuario | Admin | ✓ (solo API) |
| CU-10 | Expiración de sesión | Admin, Analyst | ✓ |
| CU-11 | Actualizar incidente | Admin, Analyst | ✓ |

---

## 3. Matriz actor × caso de uso

| Caso de uso | Admin | Analyst | Sistema externo |
|-------------|:-----:|:-------:|:---------------:|
| CU-01 Login | ✓ | ✓ | |
| CU-03 Dashboard | ✓ | ✓ | |
| CU-04 Enriquecer IOC | ✓ | ✓ | |
| CU-05 Bloquear IOC | ✓ | ✓ | |
| CU-06 Vulnerabilidades | ✓ | ✓ | |
| CU-07 Playbooks | ✓ | | |
| CU-08 Webhook | | | ✓ |
| CU-09 Registro | ✓ | | |
| CU-11 Actualizar incidente | ✓ | ✓ | |
