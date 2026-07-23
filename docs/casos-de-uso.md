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
| **Descripción** | Acceso con credenciales locales (o LDAP) y MFA opcional |
| **Precondiciones** | Usuario en BD (local/LDAP/OIDC) y `is_active=true` |
| **Postcondiciones** | Access (+ refresh) emitidos; redirección al dashboard |
| **RF asociados** | RF-01, RF-02, RF-16, RF-18, RF-20 |

### Flujo principal

1. Usuario accede a `/login`
2. Introduce username y password
3. Frontend envía `POST /api/auth/login`
4. Backend valida local o LDAP; si MFA activo y no hay OTP → 401 `mfa_required`
5. Con OTP válido (si aplica) genera access + refresh JWT
6. Frontend guarda sesión (localStorage y/o cookies según `AUTH_COOKIE_MODE`)
7. Redirección al dashboard

### Flujos alternativos

- Credenciales inválidas → 401 y mensaje de error
- MFA requerido → UI pide código TOTP
- SSO → ver CU-13

### Implementación

| Capa | Archivo |
|------|---------|
| Backend | `routes/auth.py`, `ldap_auth.py` |
| Frontend | `LoginPage.tsx`, `AuthContext.tsx`, `api.ts` |

---

## CU-02 — Cerrar sesión

| Campo | Valor |
|-------|-------|
| **Actor** | Admin, Analyst |
| **Postcondiciones** | Tokens/cookies eliminados; pantalla login |
| **RF asociados** | RF-02 |

### Flujo principal

1. Usuario pulsa **Cerrar sesión**
2. Frontend llama `POST /api/auth/logout` (si aplica) y limpia almacenamiento/cookies
3. Navegación a `/login`

### Implementación

| Capa | Archivo |
|------|---------|
| Backend | `routes/auth.py` → logout |
| Frontend | `Sidebar.tsx`, `AuthContext.tsx` |

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

1. Usuario accede a `/iocs` y pega IP, hash o URL
2. `POST /api/iocs/enrich`
3. `ioc_service.enrich_ioc()` usa VT/AbuseIPDB **live** si hay claves; si no, simuladores
4. Calcula `risk_score`, `verdict`, `enrichment_mode`, `sources_used`
5. Persiste IOC y audit log
6. UI muestra badge live/simulado y resultados

### Implementación

| Capa | Archivo |
|------|---------|
| Backend | `routes/iocs.py`, `ioc_service.py`, `external_clients.py`, `ioc_enrichment.py` |
| Frontend | `IOCsPage.tsx` |

---

## CU-05 — Bloquear IOC malicioso

| Campo | Valor |
|-------|-------|
| **Actor** | Admin, Analyst |
| **Precondiciones** | IOC con verdict `malicious`, `blocked=false` |
| **RF asociados** | RF-11 |

### Flujo principal

1. Usuario pulsa "Bloquear" / "Bloquear en FW" y confirma el diálogo
2. Frontend envía `POST /api/iocs/:id/block` con `{ confirm: true }`
3. Si el IOC es IP → se ejecuta playbook `block_ip` (live o simulado)
4. Backend actualiza `IOC.blocked = True`
5. Se registra en audit log (incluye resultado del playbook si aplica)
6. Tabla se refresca

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

### Flujo principal (sin four-eyes o con `force_direct`)

1. Admin en `/playbooks` rellena parámetros y confirma
2. `POST /api/playbooks/run` con `confirm: true`
3. Runner live o simulado; resultado en UI + audit log

### Flujo alternativo — Four-eyes (`PLAYBOOK_FOUR_EYES=true`)

1. Admin solicita playbook destructivo → 202 `pending_approval` (`PlaybookApproval`)
2. **Otro** admin aprueba o rechaza en la cola (`/api/playbooks/approvals/...`)
3. Si aprueba → se ejecuta el runner; si rechaza → estado `rejected`

### Implementación

| Capa | Archivo |
|------|---------|
| Backend | `routes/playbooks.py`, `playbook_runners.py` |
| Frontend | `PlaybooksPage.tsx` |

---

## CU-08 — Recibir alerta vía webhook

| Campo | Valor |
|-------|-------|
| **Actor** | Sistema externo (SIEM/EDR) |
| **Precondiciones** | API Key válida |
| **RF asociados** | RF-15 |

### Flujo principal

1. `POST /api/webhooks/alert` con `X-API-Key`
2. Normaliza title/severity/source/`src_ip`/`hostname`
3. Idempotencia (`Idempotency-Key` / `external_id`) o dedup por ventana → 200 si duplicado
4. Crea `Incident` (201); opcionalmente IOC IP
5. Visible en dashboard

### Implementación

| Capa | Archivo |
|------|---------|
| Backend | `routes/webhooks.py`, `settings_store.py` |

---

## CU-09 — Gestionar usuarios (admin)

| Campo | Valor |
|-------|-------|
| **Actor** | Admin |
| **RF asociados** | RF-04 |

### Flujo principal

1. Admin abre `/admin`
2. Crea usuario (`POST /api/auth/register`) o lista/edita (`GET/PATCH /api/users`)
3. Puede cambiar rol y `is_active`

### Implementación

| Capa | Archivo |
|------|---------|
| Backend | `routes/auth.py`, `routes/users.py` |
| Frontend | `UsersPage.tsx` |

---

## CU-10 — Restablecer / renovar sesión

| Campo | Valor |
|-------|-------|
| **Actor** | Admin, Analyst |
| **RF asociados** | RF-02, RF-16 |

### Flujo principal

1. Access token caduca → interceptor intenta `POST /api/auth/refresh`
2. Si refresh OK → reintenta la petición
3. Si falla → limpia sesión y redirige a `/login`

### Implementación

| Capa | Archivo |
|------|---------|
| Frontend | `api.ts`, `AuthContext.tsx` |
| Backend | `routes/auth.py` → refresh |

---

## CU-11 — Actualizar estado y asignación de incidente

| Campo | Valor |
|-------|-------|
| **Actor** | Admin, Analyst |
| **RF asociados** | RF-09b |

### Flujo principal

1. Modal KPI → cambia status / assigned_to → Guardar
2. `PATCH /api/incidents/<id>` + audit log + refresco KPIs

### Implementación

| Capa | Archivo |
|------|---------|
| Backend | `routes/incidents.py` |
| Frontend | `KpiDetailModal.tsx` |

---

## CU-12 — Activar MFA TOTP

| Campo | Valor |
|-------|-------|
| **Actor** | Admin, Analyst |
| **RF asociados** | RF-18 |

1. En Admin / perfil MFA: `POST /api/auth/mfa/setup` → secret + otpauth URI  
2. Escanea con app Authenticator → `enable` con código  
3. Siguientes logins exigen OTP  

---

## CU-13 — Login SSO (OIDC)

| Campo | Valor |
|-------|-------|
| **Actor** | Admin, Analyst |
| **RF asociados** | RF-19 |

1. Con OIDC habilitado, usuario pulsa SSO en Login  
2. Redirect IdP → `/api/auth/oidc/callback`  
3. Provisioning `auth_source=oidc` → sesión JWT → SPA  

---

## CU-14 — Rotar clave webhook

| Campo | Valor |
|-------|-------|
| **Actor** | Admin |
| **RF asociados** | RF-21 |

1. Admin rota clave en UI Admin  
2. `POST /api/settings/webhook-key/rotate`  
3. Copia la clave (una vez) y actualiza el SIEM  

---

## CU-15 — Sincronizar CISA KEV

| Campo | Valor |
|-------|-------|
| **Actor** | Admin |
| **RF asociados** | RF-22 |

1. En Vulnerabilidades → **Sync CISA KEV**  
2. `POST /api/vulnerabilities/sync-kev`  
3. Tabla actualizada con CVEs KEV  

---

## CU-16 — Actualizar estado de vulnerabilidad

| Campo | Valor |
|-------|-------|
| **Actor** | Admin, Analyst |
| **RF asociados** | RF-23 |

1. Desplegable de estado en fila CVE  
2. `PATCH /api/vulnerabilities/<id>`  

---

## CU-17 — Exportar PDF de incidente

| Campo | Valor |
|-------|-------|
| **Actor** | Admin, Analyst |
| **RF asociados** | RF-24 |

1. Modal KPI → botón **PDF**  
2. `GET /api/incidents/<id>/report/pdf` → descarga  

---

## CU-18 — Aprobar / rechazar playbook (4-eyes)

| Campo | Valor |
|-------|-------|
| **Actor** | Admin (distinto del solicitante) |
| **RF asociados** | RF-14 |

1. Solicitud pendiente en cola  
2. Aprobar → ejecución; Rechazar → `rejected`  
3. El solicitante no puede autoaprobar  

---

## 2. Resumen de casos de uso

| ID | Caso de uso | Actor | RF |
|----|-------------|-------|-----|
| CU-01 | Iniciar sesión | Admin, Analyst | RF-01, RF-18, RF-20 |
| CU-02 | Cerrar sesión | Admin, Analyst | RF-02 |
| CU-03 | Consultar dashboard | Admin, Analyst | RF-06–08 |
| CU-04 | Enriquecer IOC | Admin, Analyst | RF-10 |
| CU-05 | Bloquear IOC | Admin, Analyst | RF-11 |
| CU-06 | Filtrar vulnerabilidades | Admin, Analyst | RF-12 |
| CU-07 | Ejecutar playbook | Admin | RF-14 |
| CU-08 | Recibir webhook | Sistema externo | RF-15 |
| CU-09 | Gestionar usuarios | Admin | RF-04 |
| CU-10 | Renovar sesión | Admin, Analyst | RF-02 |
| CU-11 | Actualizar incidente | Admin, Analyst | RF-09b |
| CU-12 | Activar MFA | Admin, Analyst | RF-18 |
| CU-13 | Login SSO OIDC | Admin, Analyst | RF-19 |
| CU-14 | Rotar webhook key | Admin | RF-21 |
| CU-15 | Sync CISA KEV | Admin | RF-22 |
| CU-16 | Estado CVE | Admin, Analyst | RF-23 |
| CU-17 | Exportar PDF | Admin, Analyst | RF-24 |
| CU-18 | Aprobar playbook 4-eyes | Admin | RF-14 |

---

## 3. Matriz actor × caso de uso

| Caso de uso | Admin | Analyst | SIEM | IdP |
|-------------|:-----:|:-------:|:----:|:---:|
| CU-01 Login | ✓ | ✓ | | |
| CU-03 Dashboard | ✓ | ✓ | | |
| CU-04 / CU-05 IOCs | ✓ | ✓ | | |
| CU-06 / CU-16 Vulns | ✓ | ✓ | | |
| CU-07 / CU-18 Playbooks | ✓ | | | |
| CU-08 Webhook | | | ✓ | |
| CU-09 / CU-14 Admin | ✓ | | | |
| CU-12 MFA | ✓ | ✓ | | |
| CU-13 SSO | ✓ | ✓ | | ✓ |
| CU-15 Sync KEV | ✓ | | | |
| CU-17 PDF | ✓ | ✓ | | |
