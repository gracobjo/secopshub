# Diccionario de términos — SecOps Hub

Glosario alfabético de conceptos, acrónimos, productos y términos técnicos que aparecen en la plataforma, la documentación y el ecosistema SOC.

Cada entrada incluye **definición** y **ejemplo** en el contexto de SecOps Hub (código y docs actuales: auth MFA/OIDC/LDAP, four-eyes, Docker, métricas, threat intel live/simulado).

---

## A

### Active Directory (AD)

Directorio de identidades de Microsoft para usuarios, equipos y permisos en red Windows.

**Ejemplo:** El playbook *Revocar Usuario* en producción llamaría a AD o Azure AD para deshabilitar la cuenta `jperez` tras un incidente de credenciales comprometidas.

---

### Admin (Administrador)

Rol de usuario con privilegios elevados en SecOps Hub: puede ejecutar playbooks y registrar usuarios vía API.

**Ejemplo:** Solo un usuario con rol `admin` puede ejecutar el playbook *Aislar Host*; un `analyst` ve el botón deshabilitado.

---

### Alerta

Notificación de un evento de seguridad que requiere atención. En SecOps Hub, una alerta externa recibida por webhook se convierte en **incidente**.

**Ejemplo:** Splunk envía una alerta de brute force → SecOps Hub crea un incidente con `severity: high` y aparece en el KPI *Alertas activas*.

---

### Analyst (Analista)

Rol operativo en SecOps Hub: monitoriza el dashboard, enriquece IOCs, consulta vulnerabilidades y revisa playbooks (sin ejecutarlos).

**Ejemplo:** El usuario `analyst` / `analyst123` puede bloquear un IOC malicioso pero no ejecutar playbooks.

---

### API (Application Programming Interface)

Interfaz para que sistemas se comuniquen por HTTP. SecOps Hub expone una API REST en `/api/*`.

**Ejemplo:** `POST /api/iocs/enrich` enriquece un IOC; `POST /api/webhooks/alert` recibe alertas del SIEM.

---

### API Key

Clave secreta en cabecera HTTP para autenticar sistemas externos (no usuarios humanos).

**Ejemplo:** El SIEM envía `X-API-Key: secops-webhook-key-dev` al registrar una alerta. Sin clave válida → error 401.

---

### Audit log / Feed de auditoría

Registro cronológico de acciones realizadas por usuarios o el sistema (enriquecer IOC, ejecutar playbook, etc.).

**Ejemplo:** Tras bloquear la IP `192.168.1.100`, el dashboard muestra: *"IOC enriquecido y bloqueado — analyst"*.

---

### AbuseIPDB

Servicio de reputación de direcciones IP que reporta abusos (spam, ataques, escaneos).

**Ejemplo:** Con `ABUSEIPDB_API_KEY` el enriquecimiento consulta la API real (`enrichment_mode: live`). Sin clave, usa simulador determinista.

---

### Alembic

Herramienta de migraciones de esquema para SQLAlchemy. En SecOps Hub las revisiones viven en `backend/migrations/`.

**Ejemplo:** En producción: `alembic upgrade head` crea/actualiza tablas (`users`, `incidents`, `playbook_approvals`, etc.).

---

### AppSetting

Tabla clave-valor (`app_settings`) para ajustes persistentes que priorizan sobre `.env` (p. ej. `WEBHOOK_API_KEY` rotada).

**Ejemplo:** Tras `POST /api/settings/webhook-key/rotate`, la nueva clave se guarda en `AppSetting` y el webhook la usa de inmediato.

---

### auth_source

Origen de la cuenta de usuario en el modelo `User`: `local`, `ldap` u `oidc`.

**Ejemplo:** Un analista que entra por Microsoft Entra queda con `auth_source=oidc`; el admin demo del seed es `local`.

---

## B

### Bearer Token

Formato estándar para enviar un JWT en la cabecera HTTP: `Authorization: Bearer <token>`.

**Ejemplo:** Tras el login, Axios añade `Authorization: Bearer eyJhbGci...`. Con `AUTH_COOKIE_MODE=true` el token también puede ir en cookie httpOnly.

---

### Blueprint (Flask)

Módulo que agrupa rutas relacionadas en el backend Flask.

**Ejemplo:** `auth_bp` agrupa `/api/auth/login`, `/api/auth/me`; `webhooks_bp` agrupa `/api/webhooks/alert`.

---

### Bloqueo (IOC)

Marcar un indicador de compromiso como bloqueado (`blocked: true`). En IPs exige confirmación y dispara el playbook `block_ip` (live o simulado).

**Ejemplo:** Tras veredicto `malicious`, el analista confirma *Bloquear* → KPI *IPs bloqueadas* +1 y, si hay firewall configurado, llamada real.

---

### Bootstrap admin

Creación del primer administrador cuando la BD está vacía y `ENABLE_SEED=false`, vía variables `BOOTSTRAP_ADMIN_*` o el script `scripts/create_admin.py`.

**Ejemplo:** En Docker Compose de producción no hay usuarios demo; el arranque crea el admin definido en `BOOTSTRAP_ADMIN_USERNAME` / `PASSWORD` (≥12 caracteres).

---

### Brute force

Ataque de fuerza bruta: muchos intentos de login con contraseñas hasta acertar.

**Ejemplo:** Alerta webhook: *"500 intentos de login fallidos desde 198.51.100.42"* → incidente en dashboard.

---

## C

### CA (Certificate Authority)

Entidad que emite certificados digitales TLS para HTTPS.

**Ejemplo:** En producción, SecOps Hub usa un certificado firmado por la CA interna de la empresa o Let's Encrypt.

---

### Caddy

Servidor web / reverse proxy con TLS automático (alternativa a Nginx). Configuración en `deploy/caddy/Caddyfile`.

**Ejemplo:** En bare-metal, Caddy escucha en `:443`, sirve `frontend/dist` y proxifica `/api/*` a Gunicorn en `127.0.0.1:5000`.

---

### CISA

Cybersecurity and Infrastructure Security Agency (EE.UU.). Publica el catálogo **KEV** de vulnerabilidades explotadas activamente.

**Ejemplo:** `POST /api/vulnerabilities/sync-kev` (admin) descarga el feed oficial CISA y actualiza CVEs; también hay seed demo con entradas KEV.

---

### Confirm (confirmación)

Flag JSON obligatorio (`confirm: true`) para acciones destructivas: ejecutar playbooks sensibles o bloquear una IP IOC.

**Ejemplo:** `POST /api/playbooks/run` con `isolate_host` sin `confirm` → error 400; con confirmación → ejecución o cola four-eyes.

---

### Consola SOC

Interfaz web central donde analistas monitorizan, investigan y responden a incidentes. SecOps Hub es una consola SOC.

**Ejemplo:** El analista abre http://localhost:5173, ve KPIs, IOCs y vulnerabilidades en un solo lugar.

---

### Contain (EDR)

Acción del EDR que aísla un endpoint de la red limitando sus conexiones sin apagarlo.

**Ejemplo:** Playbook *Aislar Host* en CrowdStrike ejecutaría la acción `contain` sobre el `device_id` del PC infectado.

---

### Cookies httpOnly (`AUTH_COOKIE_MODE`)

Modo de autenticación en el que access/refresh JWT se envían también como cookies httpOnly (`secops_access` / `secops_refresh`), con `withCredentials` en el SPA.

**Ejemplo:** Con `AUTH_COOKIE_MODE=true` el frontend no depende de tokens en `localStorage`; el navegador envía la cookie automáticamente.

---

### CORS (Cross-Origin Resource Sharing)

Mecanismo que permite al navegador llamar a APIs en otro origen (puerto/dominio).

**Ejemplo:** En desarrollo, Vite (:5173) usa proxy hacia Flask (:5000) para evitar problemas CORS.

---

### Critical / High / Medium / Low

Niveles de **severidad** de incidentes y vulnerabilidades, de mayor a menor impacto.

**Ejemplo:** Un ransomware activo → `critical`; un phishing reportado → `medium`. El gráfico del dashboard agrupa incidentes por severidad.

---

### CrowdStrike Falcon

Plataforma EDR comercial. Detecta malware y permite contener hosts vía API.

**Ejemplo:** Alertas de Falcon → Splunk → webhook SecOps Hub; playbook aislar host → API Falcon `contain`.

---

### CVE (Common Vulnerabilities and Exposures)

Identificador público único para una vulnerabilidad de software (formato `CVE-AAAA-NNNNN`).

**Ejemplo:** `CVE-2024-3400` — inyección de comandos en Palo Alto PAN-OS, CVSS 10.0, marcada KEV.

---

### CVSS (Common Vulnerability Scoring System)

Puntuación estándar (0.0–10.0) del impacto técnico de una vulnerabilidad.

**Ejemplo:** En *Vulnerabilidades*, las CVEs se ordenan por CVSS descendente; `CVE-2024-3400` tiene 10.0.

---

## D

### Dashboard

Vista principal de SecOps Hub con KPIs, gráficos y feed de auditoría.

**Ejemplo:** Al pulsar el KPI *Alertas activas* (4), se abre un modal con la lista de incidentes en estado `open` o `investigating`.

---

### Dark mode

Tema visual oscuro de la interfaz, habitual en entornos SOC para reducir fatiga visual.

**Ejemplo:** SecOps Hub usa fondo slate oscuro con acentos emerald y rose.

---

### Deny list (lista de denegación)

Lista de IPs, URLs o dominios bloqueados en el firewall.

**Ejemplo:** Tras triaje, el playbook de bloqueo añadiría `203.0.113.50` a la deny list del Palo Alto.

---

### DevSecOps

Práctica que integra seguridad en el ciclo de desarrollo y operaciones (DevOps + Security).

**Ejemplo:** El equipo DevSecOps despliega SecOps Hub, configura webhooks desde Splunk y mantiene las API keys en `.env`.

---

### DMZ (Demilitarized Zone)

Segmento de red expuesto con servicios accesibles desde fuera pero aislado de la red interna crítica.

**Ejemplo:** SecOps Hub podría publicarse en la DMZ para recibir webhooks del SIEM sin exponer la red corporativa completa.

---

### DLP (Data Loss Prevention)

Sistema que detecta y previene fugas de datos sensibles.

**Ejemplo:** Incidente seed: *"Exfiltración de datos sospechosa — 2.3GB hacia IP externa"* con origen `DLP`.

---

### Drill-down

Navegación desde un resumen (KPI) al detalle (listado de registros).

**Ejemplo:** Clic en *IPs bloqueadas* → modal con tabla de IOCs donde `blocked=true`.

---

### Deduplicación (webhook)

Evita incidentes duplicados: cabecera `Idempotency-Key` / campo `external_id`, o ventana temporal por título+source+IP (`WEBHOOK_DEDUP_WINDOW_MINUTES`, default 15).

**Ejemplo:** Splunk reenvía la misma alerta dos veces en 5 minutos → SecOps Hub reutiliza el incidente existente.

---

### Docker Compose

Orquestación de contenedores: PostgreSQL, backend (Gunicorn) y frontend (Nginx). El perfil `observability` añade Prometheus y Grafana.

**Ejemplo:** `docker compose up -d` levanta el Hub; `docker compose --profile observability up -d` activa métricas.

---

## E

### EDR (Endpoint Detection and Response)

Solución que monitoriza y responde a amenazas en endpoints (PCs, servidores).

**Ejemplo:** Microsoft Defender detecta malware → alerta al SIEM → SecOps Hub → playbook aísla el host.

---

### enrichment_mode

Campo de la respuesta de `POST /api/iocs/enrich`: `live` si AbuseIPDB y/o VirusTotal respondieron en vivo; `simulated` si no hay claves o hubo fallback.

**Ejemplo:** La UI de IOCs muestra badge *API en vivo* o *Modo simulado* según `enrichment_mode`.

---

### Enriquecimiento (IOC)

Proceso de consultar fuentes externas (VirusTotal, AbuseIPDB) para obtener contexto sobre un indicador. Orquestado en `ioc_service.py` con fallback simulado.

**Ejemplo:** Pegar `203.0.113.50` → *Enriquecer* → veredicto, score, `sources_used` y recomendación `block` o `monitor`.

---

### ensure_schema

Compatibilidad ligera al arranque: aplica `ALTER TABLE` para columnas nuevas (MFA, `external_id`, etc.) sin exigir siempre una migración completa.

**Ejemplo:** Tras actualizar el código, el backend añade columnas faltantes automáticamente además de Alembic.

---

### Endpoint

Dispositivo final conectado a la red: portátil, PC, servidor, móvil.

**Ejemplo:** *"Malware detectado en endpoint HR-042"* — el EDR reporta la estación de trabajo comprometida.

---

### external_id

Identificador externo del incidente (SIEM) usado para idempotencia del webhook; puede venir del body (`id`, `alert_id`, `event_id`) o de la cabecera de idempotencia.

**Ejemplo:** `{"title":"...","external_id":"splunk-alert-88421"}` — un reenvío con el mismo id no crea un segundo incidente.

---

### Exfiltración

Transferencia no autorizada de datos fuera de la organización.

**Ejemplo:** Webhook: *"Transferencia anómala de 1.8GB desde SRV-FIN-01"* → incidente `critical`.

---

## F

### Feed (CISA KEV / auditoría)

Flujo continuo de datos. *Feed KEV*: catálogo CISA de CVEs explotadas (sync HTTP o seed). *Feed de auditoría*: acciones recientes en SecOps Hub.

**Ejemplo:** El dashboard muestra las últimas entradas del feed de auditoría con usuario y timestamp.

---

### Four-eyes (cuatro ojos)

Control de doble autorización: con `PLAYBOOK_FOUR_EYES=true`, los playbooks destructivos crean una solicitud `pending` y otro admin debe aprobar o rechazar (no el solicitante).

**Ejemplo:** Admin A solicita *Aislar Host* → HTTP 202 `pending_approval` → Admin B aprueba en la cola → se ejecuta el runner.

---

### force_direct

Parámetro opcional en `POST /api/playbooks/run` que bypasea la cola four-eyes (sigue exigiendo rol admin y `confirm=true`).

**Ejemplo:** En emergencia, el admin ejecuta con `force_direct: true` y se salta la aprobación de segundo operador.

---

### Firewall

Dispositivo o software que filtra tráfico de red según reglas de seguridad.

**Ejemplo:** Palo Alto bloquea tráfico malicioso; logs → Splunk → alerta → SecOps Hub.

---

### Flask

Framework web de Python usado para el backend API de SecOps Hub.

**Ejemplo:** `python run.py` arranca Flask en el puerto 5000 con JWT, SQLAlchemy y blueprints.

---

## G

### Graph API

API de Microsoft para administrar Azure AD, usuarios, dispositivos y seguridad.

**Ejemplo:** Playbook `revoke_user` con tenant y credenciales de aplicación invalida sesiones vía Microsoft Graph.

---

### Grafana

Plataforma de dashboards de observabilidad. En SecOps Hub se provisiona con el perfil Docker `observability` contra Prometheus.

**Ejemplo:** Dashboard en `deploy/grafana/` muestra series `secops_http_*` e incidentes abiertos.

---

## H

### Hash (MD5 / SHA1 / SHA256)

Huella digital fija de un fichero o dato. Se usa como IOC para detectar malware conocido.

**Ejemplo:** Hash SHA256 en IOCs → tipo `sha256` → VirusTotal live (con API key) o simulado.

---

### Health check (`/health`)

Endpoint de liveness/readiness: comprueba la BD (`SELECT 1`). Responde `ok` o `degraded` (HTTP 503).

**Ejemplo:** El reverse proxy o el orquestador consultan `/health` antes de enviar tráfico.

---

### Host / Hostname

Equipo en la red identificado por nombre (p. ej. `WS-HR-042`, `SRV-FIN-01`).

**Ejemplo:** Playbook *Aislar Host* recibe parámetro `hostname: WS-HR-042`.

---

### HTTPS / TLS

Protocolo HTTP cifrado. TLS garantiza confidencialidad e integridad. En producción, obligatorio detrás de Nginx/Caddy.

**Ejemplo:** `https://secops.empresa.local/api/webhooks/alert` con certificado de CA interna o Let's Encrypt.

---

## I

### Idempotencia (webhook)

Garantía de que reenviar la misma alerta no duplica incidentes (`Idempotency-Key`, `external_id` o ventana de deduplicación).

**Ejemplo:** Cabecera `Idempotency-Key: alert-88421` en dos POST → un solo incidente.

---

### IDS (Intrusion Detection System)

Sistema que **detecta** intrusiones y genera alertas, sin bloquear tráfico automáticamente.

**Ejemplo:** Un IDS detecta un exploit attempt → alerta al SIEM → webhook SecOps Hub con `source: "IDS"`.

---

### Incidente

Registro en SecOps Hub que representa un evento de seguridad (título, severidad, estado, origen, `external_id` opcional). Estados: `open`, `investigating`, `resolved`, `closed`.

**Ejemplo:** Webhook crea incidente *"Brute force detectado"* con `status: open`, `source: Splunk`.

---

### Ingesta

Recepción e incorporación de datos externos (alertas, logs) al sistema.

**Ejemplo:** Capa de ingesta: SIEM → `POST /api/webhooks/alert` → tabla `incidents`.

---

### Integración

Conexión entre SecOps Hub y sistemas externos (SIEM, EDR, firewall, threat intel). Estado en `GET /api/integrations/status`.

**Ejemplo:** El endpoint indica si triaje/respuesta están en modo `live` o `simulated` según API keys y runners.

---

### IOC (Indicator of Compromise)

Indicador de compromiso: evidencia de actividad maliciosa (IP, hash, URL, dominio).

**Ejemplo:** La IP `192.168.1.100` es un IOC con veredicto `malicious` y `blocked: true` en la tabla IOCs.

---

### IPS (Intrusion Prevention System)

Sistema que **detecta y bloquea** intrusiones en tiempo real (IDS + acción).

**Ejemplo:** Palo Alto IPS bloquea exploit → log → alerta Splunk → incidente en SecOps Hub.

---

## J

### JSON Web Token (JWT)

Token firmado que acredita identidad y rol tras el login. Incluye **access token** (corta vida, ~8 h) y **refresh token** (~30 días).

**Ejemplo:** Login devuelve tokens; el SPA los usa en `Authorization: Bearer …` o, con `AUTH_COOKIE_MODE=true`, en cookies httpOnly (`secops_access` / `secops_refresh`). Ante 401 se intenta `POST /api/auth/refresh`.

---

## K

### KEV (Known Exploited Vulnerabilities)

Catálogo CISA de CVEs con explotación activa conocida. Prioridad de parcheo urgente.

**Ejemplo:** Filtro *Solo CISA KEV* en Vulnerabilidades; sincronización real con `POST /api/vulnerabilities/sync-kev` o `KEV_SYNC_ON_STARTUP=true`.

---

### KPI (Key Performance Indicator)

Métrica resumida en el dashboard: alertas activas, IPs bloqueadas, etc.

**Ejemplo:** KPI *Vulnerabilidades KEV* = count de CVEs con `is_kev=true` y `status=open`.

---

## L

### Lateral movement

Movimiento lateral: atacante que pasa de un sistema comprometido a otros dentro de la red.

**Ejemplo:** Payload webhook: `{"title":"Lateral movement detected","severity":"high","source":"EDR"}`.

---

### LDAP

Protocolo de directorio. En SecOps Hub es login opcional: si falla el usuario local y `LDAP_ENABLED=true`, intenta bind (`ldap3`) y provisiona cuenta con `auth_source=ldap`.

**Ejemplo:** Credenciales corporativas → bind a `LDAP_SERVER` → usuario creado/actualizado con rol `LDAP_DEFAULT_ROLE`.

---

### Live / Simulated (modo)

Modo de operación de triaje y respuesta: **live** usa APIs reales; **simulated** usa fallbacks deterministas cuando faltan claves o la integración no es ejecutable.

**Ejemplo:** Badge en IOCs/Playbooks y campo `enrichment_mode` / `response_mode` en las respuestas API.

---

## M

### MFA / TOTP

Autenticación multifactor con código de un solo uso basado en tiempo (pyotp). Setup en `/api/auth/mfa/setup`; login exige `otp` si `mfa_enabled`.

**Ejemplo:** Tras activar MFA, el login responde `mfa_required` hasta que el analista introduce el código de su app Authenticator.

---

### Malicious / Suspicious / Clean

Veredictos de enriquecimiento IOC: malicioso (≥75 score), sospechoso (40–74), limpio (<40).

**Ejemplo:** IP con score 85 → veredicto `malicious` → recomendación `block`.

---

### Malware

Software malicioso: virus, troyanos, ransomware, etc.

**Ejemplo:** Incidente seed: *"Trojan.Generic detectado en estación HR-042"* con origen `EDR`.

---

### Microsoft Defender

EDR/antivirus de Microsoft integrado en Windows y Microsoft 365.

**Ejemplo:** Con `EDR_TYPE=defender` y `EDR_API_TOKEN`, el playbook `isolate_host` apunta a la API de aislamiento de dispositivo.

---

### Métricas (`/metrics`)

Endpoint Prometheus con contadores/gauges (`secops_http_*`, `secops_incidents_open`, `secops_users_active`).

**Ejemplo:** Prometheus scrapea `/metrics`; Grafana visualiza el dashboard SecOps Hub.

---

## N

### Nginx

Servidor web / reverse proxy. En Compose sirve el frontend y proxifica `/api`, `/health` y `/metrics` al backend; en bare-metal ver `deploy/nginx/secops-hub.conf`.

**Ejemplo:** El contenedor frontend usa `frontend/nginx.conf` para unificar UI y API en el mismo origen.

---

### NGFW (Next-Generation Firewall)

Firewall de nueva generación con IPS, filtrado de aplicaciones y amenazas integradas.

**Ejemplo:** Palo Alto PA-5200 es un NGFW; sus logs alimentan alertas en SecOps Hub vía SIEM.

---

## O

### OIDC (OpenID Connect)

Protocolo de SSO sobre OAuth2. SecOps Hub implementa Authorization Code: `/api/auth/oidc/login` y `/callback`; provisiona usuarios `auth_source=oidc`.

**Ejemplo:** Con `OIDC_ENABLED=true` el login muestra botón SSO; si el claim de grupos incluye `OIDC_ADMIN_GROUP`, el usuario recibe rol `admin`.

---

### Ofensa (QRadar)

En IBM QRadar, agrupación correlacionada de eventos que constituye un incidente de seguridad.

**Ejemplo:** Ofensa magnitud 8 → script QRadar envía webhook con `severity: critical`.

---

### Orquestación

Coordinación automatizada de múltiples acciones de respuesta (playbooks encadenados).

**Ejemplo:** SecOps Hub orquesta: bloquear IP → aislar host → revocar usuario en secuencia.

---

## P

### Palo Alto Networks

Fabricante de firewalls NGFW (serie PA). API XML para gestión de reglas y objetos.

**Ejemplo:** Playbook bloqueo IP añade entrada en `/address` del PAN-OS vía API.

---

### Patch / Parcheo

Actualización de software que corrige una vulnerabilidad.

**Ejemplo:** CVE KEV `CVE-2024-3400` en estado `open` — el analista prioriza parcheo del firewall PA-5200.

---

### Phishing

Suplantación de identidad por email para robar credenciales o instalar malware.

**Ejemplo:** Incidente seed: *"Email de suplantación del CEO"* — severidad `medium`, origen Email Gateway.

---

### Playbook

Secuencia automatizada de respuesta. IDs: `isolate_host`, `block_ip`, `revoke_user`, `data_scan`. Los tres primeros son **destructivos** (exigen `confirm`; con four-eyes van a cola de aprobación).

**Ejemplo:** Admin ejecuta `isolate_host` con `hostname: SRV-FIN-01` → runner live (EDR) o simulado → audit log.

---

### PlaybookApproval

Entidad/cola de solicitudes four-eyes: estados `pending`, `executed`, `failed`, `rejected`. El aprobador no puede ser el solicitante.

**Ejemplo:** UI de Playbooks lista pendientes; Admin B aprueba → se llama a `run_playbook` y el estado pasa a `executed`.

---

### PostgreSQL

Motor relacional recomendado en producción (Compose usa Postgres 16). Sustituye SQLite.

**Ejemplo:** `DATABASE_URL=postgresql+psycopg://secops:pass@db:5432/secops_hub`.

---

### Prometheus

Sistema de scrape de métricas. Perfil Docker `observability` scrapea `/metrics` del backend.

**Ejemplo:** Config en `deploy/prometheus/prometheus.yml`; series `secops_incidents_open` en Grafana.

---

### Proxy (Vite)

Intermediario en desarrollo que redirige `/api` del frontend al backend.

**Ejemplo:** `localhost:5173/api/incidents/stats` → Vite → `localhost:5000`.

---

### ProxyFix

Middleware Werkzeug que confía en cabeceras `X-Forwarded-*` cuando hay reverse proxy. Se activa con `BEHIND_PROXY=true` o `FLASK_ENV=production`.

**Ejemplo:** Nginx envía `X-Forwarded-Proto: https`; Flask genera URLs y esquemas HTTPS correctos.

---

## Q

### QRadar

SIEM de IBM que correlaciona logs y genera ofensas.

**Ejemplo:** Regla QRadar magnitud ≥ 5 → script Python → `POST /api/webhooks/alert`.

---

## R

### Ransomware

Malware que cifra datos y exige rescate.

**Ejemplo:** Webhook: `{"title":"Ransomware detectado en DC-01","severity":"critical","source":"CrowdStrike"}`.

---

### RBAC (Role-Based Access Control)

Control de acceso según rol del usuario (`admin` vs `analyst`).

**Ejemplo:** `@admin_required` en backend devuelve 403 si un analyst intenta ejecutar un playbook.

---

### REST API

Estilo de API que usa HTTP y recursos identificados por URLs (`GET /api/incidents`).

**Ejemplo:** SecOps Hub expone REST JSON: login, stats, IOCs, vulnerabilidades, playbooks, webhooks.

---

### Refresh token

JWT de larga vida usado para renovar el access token sin volver a pedir contraseña (`POST /api/auth/refresh`).

**Ejemplo:** Access caduca a las 8 h → el SPA reintenta con refresh (~30 días) antes de redirigir a `/login`.

---

### Revocación (usuario)

Invalidar credenciales y cerrar sesiones de un usuario comprometido (playbook `revoke_user`).

**Ejemplo:** Con Azure AD configurado → Graph API; sin credenciales → resultado simulado con `mode: simulated`.

---

### RGPD / GDPR

Reglamento General de Protección de Datos (UE). La vista de vulnerabilidades menciona cumplimiento normativo.

**Ejemplo:** Auditoría de CVEs y parcheo documentado en SecOps Hub puede apoyar evidencias de cumplimiento.

---

### Risk score (puntuación de riesgo)

Valor 0–100 que resume el peligro de un IOC tras enriquecimiento.

**Ejemplo:** IP con score 85 → badge rojo, veredicto `malicious`, botón *Bloquear* disponible.

---

### Runbook

Procedimiento documentado paso a paso para responder a un tipo de incidente (humano).

**Ejemplo:** El [manual de laboratorio](manual-laboratorio.md) Lab 7 es un runbook de exfiltración; los playbooks automatizan partes del runbook.

---

## S

### Seed (datos semilla)

Carga demo al arranque si `ENABLE_SEED=true` (usuarios, incidentes, IOCs, CVEs). En producción debe ser `false` y usarse bootstrap admin.

**Ejemplo:** Con seed: `admin/admin123`. Sin seed: `BOOTSTRAP_ADMIN_*` o `python scripts/create_admin.py`.

---

### Sentencia SPL (Splunk)

Lenguaje de búsqueda de Splunk para consultar logs indexados.

**Ejemplo:** `index=firewall action=blocked | stats count by src_ip` — base de una alerta hacia SecOps Hub.

---

### Severidad

Grado de impacto de un incidente o vulnerabilidad: `critical`, `high`, `medium`, `low`.

**Ejemplo:** Filtro en Vulnerabilidades por severidad `critical` muestra solo CVEs críticas.

---

### SIEM (Security Information and Event Management)

Plataforma que centraliza logs, correlaciona eventos y genera alertas (Splunk, QRadar, Sentinel).

**Ejemplo:** Splunk recibe logs de firewall, EDR y AD; dispara webhook cuando detecta brute force.

---

### Simulador

Código que imita una integración sin llamar a sistemas externos. Queda como **fallback** si faltan claves o falla la API real.

**Ejemplo:** `simulate_virustotal()` / `simulate_abuseipdb()` en `ioc_enrichment.py` cuando no hay `VIRUSTOTAL_API_KEY` / `ABUSEIPDB_API_KEY`.

---

### SOAR (Security Orchestration, Automation and Response)

Plataforma que automatiza respuesta (Phantom, XSOAR, n8n, Ansible). SecOps Hub puede delegar vía `PLAYBOOK_CALLBACK_URL`.

**Ejemplo:** `block_ip` hace POST al callback SOAR con la IP a denegar en el firewall.

---

### SOC (Security Operations Center)

Centro de operaciones de ciberseguridad: equipo y herramientas para detectar, analizar y responder.

**Ejemplo:** SecOps Hub es la consola web del SOC; analistas trabajan en el dashboard e IOCs.

---

### SecOps (Security Operations)

Operaciones de seguridad: procesos y herramientas del día a día del SOC.

**Ejemplo:** *SecOps Hub* = hub centralizado de operaciones SecOps con JWT, IOCs y playbooks.

---

### SPA (Single Page Application)

Aplicación web que carga una sola página HTML y navega sin recargas completas (React).

**Ejemplo:** El frontend de SecOps Hub es una SPA en Vite/React con rutas `/`, `/iocs`, `/vulnerabilities`.

---

### Splunk

SIEM líder que indexa logs y permite alertas con acciones webhook.

**Ejemplo:** Alert Action webhook → `https://secops.empresa.local/api/webhooks/alert` con JSON de la alerta.

---

### SQLite

Base de datos embebida en fichero, usada en desarrollo/demo de SecOps Hub.

**Ejemplo:** `backend/instance/secops_hub.db` almacena usuarios, incidentes, IOCs y audit logs.

---

### SSO (Single Sign-On)

Inicio de sesión único con IdP corporativo. En SecOps Hub se implementa con **OIDC** (p. ej. Entra ID / Okta).

**Ejemplo:** Botón SSO en login → redirección al IdP → callback → sesión JWT (header o cookie).

---

### sync-kev

Acción admin (`POST /api/vulnerabilities/sync-kev`) que descarga el feed CISA KEV e inserta/actualiza CVEs. También puede ejecutarse al arranque (`KEV_SYNC_ON_STARTUP`).

**Ejemplo:** Tras sync, el filtro KEV muestra CVEs reales del catálogo además del seed.

---

### Syslog

Protocolo estándar para enviar mensajes de log (firewalls, switches, servidores).

**Ejemplo:** pfSense envía syslog a Splunk → alertas → SecOps Hub.

---

## T

### Threat Intel (inteligencia de amenazas)

Información sobre amenazas, actores y IOCs conocidos.

**Ejemplo:** IOC precargado `192.168.1.100` con `source: Threat Intel` — reputación maliciosa conocida.

---

### Token (de acceso)

Credencial temporal JWT tras autenticación. Distinto de API Key (sistemas) y de refresh token.

**Ejemplo:** Access ~8 h; si caduca, el cliente usa refresh o redirige a `/login`.

---

### Triaje

Clasificación y priorización inicial de alertas o IOCs para decidir acciones.

**Ejemplo:** Analista enriquece IP del incidente, revisa score y decide bloquear o escalar.

---

### Trojan

Tipo de malware que se disfraza de software legítimo.

**Ejemplo:** *"Trojan.Generic detectado en HR-042"* — incidente critical del seed.

---

## U

### URL (como IOC)

Dirección web usada como indicador (phishing, C2, descarga de malware).

**Ejemplo:** Pegar `http://malicious-site.example/path` en IOCs → tipo detectado `url` (si empieza por http).

---

## V

### Veredicto

Conclusión del enriquecimiento IOC: `malicious`, `suspicious` o `clean`.

**Ejemplo:** Badge verde `CLEAN` para `8.8.8.8`; badge rojo `MALICIOUS` para IP con score alto.

---

### VLAN

Red local virtual: segmento lógico aislado dentro de la red física.

**Ejemplo:** SecOps Hub en VLAN 10 (SOC); SIEM en VLAN 20; reglas firewall entre VLANs.

---

### VirusTotal

Servicio que escanea ficheros, IPs y URLs con múltiples motores antivirus.

**Ejemplo:** Con `VIRUSTOTAL_API_KEY` → lookup live y contadores reales; sin clave → simulador con `mode: simulated`.

---

### Vulnerabilidad

Debilidad de seguridad explotable. Estados: `open`, `in_progress`, `mitigated`, `accepted`, `closed`.

**Ejemplo:** `CVE-2024-21413` — Outlook MonikerLink RCE, CVSS 9.8, KEV, estado `open`.

---

## W

### Wazuh

SIEM/XDR open source usado en el laboratorio de infraestructura (alternativa a Splunk/QRadar en aula).

**Ejemplo:** Regla Wazuh → webhook → `POST /api/webhooks/alert`. Ver [laboratorio-infraestructura.md](laboratorio-infraestructura.md).

---

### Webhook

Callback HTTP: un sistema notifica a otro con POST al ocurrir un evento. Autenticado con `X-API-Key` (rotatable vía settings).

**Ejemplo:** Splunk → `/api/webhooks/alert` con `{title, severity, source}` e idempotencia opcional.

---

### WSGI / Gunicorn

Interfaz estándar Python para servidores web. Gunicorn sirve `wsgi:app` en producción (solo localhost detrás del proxy).

**Ejemplo:** Unidad systemd o contenedor: `gunicorn -w 2 -b 0.0.0.0:5000 wsgi:app`.

---

## X

### X-API-Key

Cabecera para autenticar el webhook SIEM. Puede rotarse (`/api/settings/webhook-key/rotate`); `AppSetting` prioriza sobre `.env`.

**Ejemplo:**
```http
X-API-Key: <WEBHOOK_API_KEY>
```

---

## Z

### Zero-day

Vulnerabilidad explotada antes de que exista parche público.

**Ejemplo:** Payload webhook: `{"title":"Zero-day exploit attempt","severity":"critical","source":"IDS"}`.

---

## Índice por categoría

| Categoría | Términos |
|-----------|----------|
| **Roles** | Admin, Analyst, auth_source, Bootstrap admin |
| **Operaciones SOC** | SOC, SecOps, Consola, Dashboard, Triaje, Runbook, Orquestación, Ingesta, Four-eyes |
| **Amenazas** | Malware, Ransomware, Phishing, Trojan, Brute force, Exfiltración, Lateral movement, Zero-day |
| **Indicadores** | IOC, Hash, URL, Veredicto, Risk score, Enriquecimiento, enrichment_mode, Bloqueo, Confirm |
| **Vulnerabilidades** | CVE, CVSS, KEV, CISA, sync-kev, Vulnerabilidad, Patch, Severidad |
| **Herramientas SIEM/EDR** | SIEM, Splunk, QRadar, Wazuh, EDR, Defender, CrowdStrike, SOAR |
| **Red y perimetral** | Firewall, NGFW, Palo Alto, IDS, IPS, DMZ, VLAN, Syslog, Deny list |
| **Identidad** | AD, Azure AD, LDAP, SSO, OIDC, Graph API, MFA/TOTP, Revocación |
| **Integración** | Webhook, API, API Key, X-API-Key, REST, Integración, Simulador, Live/Simulated, Idempotencia, Deduplicación, external_id |
| **Autenticación** | JWT, Bearer, Refresh token, AUTH_COOKIE_MODE, RBAC, Token, CORS |
| **SecOps Hub (app)** | Playbook, PlaybookApproval, Incidente, Alerta, KPI, Audit log, Seed, AppSetting, Drill-down, force_direct |
| **Fuentes threat intel** | AbuseIPDB, VirusTotal, Threat Intel |
| **Infraestructura** | HTTPS/TLS, PostgreSQL, SQLite, Flask, SPA, Proxy Vite, ProxyFix, WSGI, Gunicorn, Nginx, Caddy, Docker Compose, Alembic, ensure_schema, Health, Prometheus, Grafana, Métricas |
| **Cumplimiento** | RGPD, GDPR |
| **Desarrollo** | Blueprint, DevSecOps, Dark mode |

---

## Referencias cruzadas

- [Manual de usuario — glosario breve](manual-usuario.md#11-glosario)
- [Contexto formativo](proyecto-institucional.md)
- [Integración en red](integracion-red.md)
- [Threat intel](threat-intel.md)
- [Runbook operativo](runbook-operacion.md)
- [Manual de laboratorio](manual-laboratorio.md)
- [Manual de desarrollador](manual-desarrollador.md)
