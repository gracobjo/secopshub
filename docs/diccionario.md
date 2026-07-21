# Diccionario de términos — SecOps Hub

Glosario alfabético de conceptos, acrónimos, productos y términos técnicos que aparecen en la plataforma, la documentación y el ecosistema SOC.

Cada entrada incluye **definición** y **ejemplo** en el contexto de SecOps Hub.

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

**Ejemplo:** Al enriquecer una IP, SecOps Hub muestra datos de AbuseIPDB (simulados en demo). En producción consultaría la API real con *abuse confidence score*.

---

## B

### Bearer Token

Formato estándar para enviar un JWT en la cabecera HTTP: `Authorization: Bearer <token>`.

**Ejemplo:** Tras el login, Axios añade automáticamente `Authorization: Bearer eyJhbGci...` a cada petición.

---

### Blueprint (Flask)

Módulo que agrupa rutas relacionadas en el backend Flask.

**Ejemplo:** `auth_bp` agrupa `/api/auth/login`, `/api/auth/me`; `webhooks_bp` agrupa `/api/webhooks/alert`.

---

### Bloqueo (IOC)

Marcar un indicador de compromiso como bloqueado en SecOps Hub (`blocked: true`). En producción debería propagarse al firewall.

**Ejemplo:** Tras veredicto `malicious`, el analista pulsa *Bloquear* → el KPI *IPs bloqueadas* sube en 1.

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

### CISA

Cybersecurity and Infrastructure Security Agency (EE.UU.). Publica el catálogo **KEV** de vulnerabilidades explotadas activamente.

**Ejemplo:** Las CVEs marcadas como KEV en SecOps Hub simulan entradas de ese catálogo (p. ej. `CVE-2024-3400`).

---

### Consola SOC

Interfaz web central donde analistas monitorizan, investigan y responden a incidentes. SecOps Hub es una consola SOC.

**Ejemplo:** El analista abre http://localhost:5173, ve KPIs, IOCs y vulnerabilidades en un solo lugar.

---

### Contain (EDR)

Acción del EDR que aísla un endpoint de la red limitando sus conexiones sin apagarlo.

**Ejemplo:** Playbook *Aislar Host* en CrowdStrike ejecutaría la acción `contain` sobre el `device_id` del PC infectado.

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

## E

### EDR (Endpoint Detection and Response)

Solución que monitoriza y responde a amenazas en endpoints (PCs, servidores).

**Ejemplo:** Microsoft Defender detecta malware → alerta al SIEM → SecOps Hub → playbook aísla el host.

---

### Enriquecimiento (IOC)

Proceso de consultar fuentes externas (VirusTotal, AbuseIPDB) para obtener contexto sobre un indicador.

**Ejemplo:** Pegar `203.0.113.50` en IOCs → *Enriquecer* → veredicto, score y recomendación `block` o `monitor`.

---

### Endpoint

Dispositivo final conectado a la red: portátil, PC, servidor, móvil.

**Ejemplo:** *"Malware detectado en endpoint HR-042"* — el EDR reporta la estación de trabajo comprometida.

---

### Exfiltración

Transferencia no autorizada de datos fuera de la organización.

**Ejemplo:** Webhook: *"Transferencia anómala de 1.8GB desde SRV-FIN-01"* → incidente `critical`.

---

## F

### Feed (CISA KEV / auditoría)

Flujo continuo de datos. *Feed KEV*: catálogo actualizado de CVEs explotadas. *Feed de auditoría*: acciones recientes en SecOps Hub.

**Ejemplo:** El dashboard muestra las últimas 10 entradas del feed de auditoría con usuario y timestamp.

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

**Ejemplo:** Playbook *Revocar Usuario* en producción usaría Graph API para invalidar sesiones de `jperez@empresa.com`.

---

## H

### Hash (MD5 / SHA1 / SHA256)

Huella digital fija de un fichero o dato. Se usa como IOC para detectar malware conocido.

**Ejemplo:** `a1b2c3d4e5f6789012345678901234567890abcd` (SHA1) enriquecido en IOCs → tipo `sha1`, veredicto según simulación VT.

---

### Host / Hostname

Equipo en la red identificado por nombre (p. ej. `WS-HR-042`, `SRV-FIN-01`).

**Ejemplo:** Playbook *Aislar Host* recibe parámetro `hostname: WS-HR-042`.

---

### HTTPS / TLS

Protocolo HTTP cifrado. TLS (Transport Layer Security) garantiza confidencialidad e integridad.

**Ejemplo:** En producción la API debe estar en `https://secops.empresa.local`, no en HTTP plano.

---

## I

### IDS (Intrusion Detection System)

Sistema que **detecta** intrusiones y genera alertas, sin bloquear tráfico automáticamente.

**Ejemplo:** Un IDS detecta un exploit attempt → alerta al SIEM → webhook SecOps Hub con `source: "IDS"`.

---

### Incidente

Registro en SecOps Hub que representa un evento de seguridad a gestionar (título, severidad, estado, origen).

**Ejemplo:** Webhook crea incidente *"Brute force detectado"* con `status: open`, `source: Splunk`.

---

### Ingesta

Recepción e incorporación de datos externos (alertas, logs) al sistema.

**Ejemplo:** Capa de ingesta: SIEM → `POST /api/webhooks/alert` → tabla `incidents`.

---

### Integración

Conexión entre SecOps Hub y sistemas externos (SIEM, EDR, firewall).

**Ejemplo:** Ver [integracion-red.md](integracion-red.md) para conectar Splunk y QRadar paso a paso.

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

Token firmado que acredita la identidad y rol del usuario tras el login. Expira en 8 horas en SecOps Hub.

**Ejemplo:** Login devuelve `access_token`; el frontend lo guarda en `localStorage` como `secops_token`.

---

## K

### KEV (Known Exploited Vulnerabilities)

Catálogo CISA de CVEs con explotación activa conocida. Prioridad de parcheo urgente.

**Ejemplo:** Filtro *Solo CISA KEV* en Vulnerabilidades muestra `CVE-2023-4966` (Citrix Bleed) con badge KEV.

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

Protocolo de directorio para consultar usuarios y grupos (alternativa/complemento a AD).

**Ejemplo:** En producción, login corporativo podría validar credenciales contra LDAP en lugar de usuarios locales.

---

## M

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

**Ejemplo:** Defender detecta amenaza → Sentinel/Splunk → webhook; playbook aísla vía Defender API.

---

## N

### NGFW (Next-Generation Firewall)

Firewall de nueva generación con IPS, filtrado de aplicaciones y amenazas integradas.

**Ejemplo:** Palo Alto PA-5200 es un NGFW; sus logs alimentan alertas en SecOps Hub vía SIEM.

---

## O

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

Secuencia automatizada de pasos de respuesta a incidentes (aislar, revocar, escanear).

**Ejemplo:** Admin ejecuta playbook `isolate_host` con `hostname: SRV-FIN-01` → resultado en panel y audit log.

---

### PostgreSQL

Motor de base de datos relacional recomendado para producción (sustituye SQLite).

**Ejemplo:** `DATABASE_URL=postgresql://secops:pass@db:5432/secops_hub` en `.env` de producción.

---

### Proxy (Vite)

Intermediario en desarrollo que redirige peticiones `/api` del frontend al backend.

**Ejemplo:** Navegador llama `localhost:5173/api/incidents/stats` → Vite reenvía a `localhost:5000`.

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

### Revocación (usuario)

Invalidar credenciales y cerrar sesiones activas de un usuario comprometido.

**Ejemplo:** Playbook `revoke_user` con `username: jperez` — simulado hoy; en producción llamaría a AD/Azure AD.

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

Script que inserta datos de demostración al primer arranque (usuarios, incidentes, IOCs, CVEs).

**Ejemplo:** `seed_database()` crea `admin/admin123` y 5 incidentes si la BD está vacía. Desactivar en producción.

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

Código que imita una integración real sin llamar a sistemas externos (demo).

**Ejemplo:** `simulate_virustotal()` calcula score por hash del valor, no consulta VirusTotal real.

---

### SOAR (Security Orchestration, Automation and Response)

Plataforma que automatiza respuesta a incidentes (Splunk Phantom, Cortex XSOAR).

**Ejemplo:** SOAR puede llamar al webhook de SecOps Hub o viceversa en flujos híbridos.

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

Inicio de sesión único con credenciales corporativas (Azure AD, Okta).

**Ejemplo:** Extensión futura: login con SSO en lugar de `admin/admin123` local.

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

Credencial temporal JWT tras autenticación. Distinto de API Key (sistemas) y contraseña.

**Ejemplo:** Token expira a las 8 h → interceptor recibe 401 → redirección a `/login`.

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

Servicio que escanea ficheros y URLs con múltiples motores antivirus.

**Ejemplo:** Enriquecimiento muestra contadores VT: malicious 45, suspicious 12, harmless 30 (simulado en demo).

---

### Vulnerabilidad

Debilidad de seguridad en software/hardware explotable por un atacante.

**Ejemplo:** `CVE-2024-21413` — Outlook MonikerLink RCE, CVSS 9.8, KEV, estado `open`.

---

## W

### Webhook

Callback HTTP: un sistema notifica a otro enviando un POST automático cuando ocurre un evento.

**Ejemplo:** Splunk dispara webhook a `/api/webhooks/alert` al cumplirse una regla de alerta.

---

### WSGI / Gunicorn

Interfaz estándar Python para servidores web. Gunicorn es servidor WSGI para producción Flask.

**Ejemplo:** Producción: `gunicorn -w 4 run:app` en lugar de `python run.py` con debug.

---

## X

### X-API-Key

Cabecera HTTP estándar de facto para enviar API Key en webhooks hacia SecOps Hub.

**Ejemplo:**
```http
X-API-Key: secops-webhook-key-dev
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
| **Roles** | Admin, Analyst |
| **Operaciones SOC** | SOC, SecOps, Consola, Dashboard, Triaje, Runbook, Orquestación, Ingesta |
| **Amenazas** | Malware, Ransomware, Phishing, Trojan, Brute force, Exfiltración, Lateral movement, Zero-day |
| **Indicadores** | IOC, Hash, IP, URL, Veredicto, Risk score, Enriquecimiento, Bloqueo |
| **Vulnerabilidades** | CVE, CVSS, KEV, CISA, Vulnerabilidad, Patch, Severidad |
| **Herramientas SIEM/EDR** | SIEM, Splunk, QRadar, EDR, Defender, CrowdStrike, Sentinel, SOAR |
| **Red y perimetral** | Firewall, NGFW, Palo Alto, pfSense, IDS, IPS, DMZ, VLAN, Syslog |
| **Identidad** | AD, Azure AD, LDAP, SSO, Graph API, Revocación |
| **Integración** | Webhook, API, API Key, X-API-Key, REST, Integración, Simulador |
| **Autenticación** | JWT, Bearer Token, RBAC, Token, CORS |
| **SecOps Hub (app)** | Playbook, Incidente, Alerta, KPI, Audit log, Seed, Dashboard, Drill-down |
| **Fuentes threat intel** | AbuseIPDB, VirusTotal, Threat Intel |
| **Infraestructura** | HTTPS, TLS, PostgreSQL, SQLite, Flask, SPA, Proxy, WSGI, Gunicorn |
| **Cumplimiento** | RGPD, GDPR |
| **Desarrollo** | Blueprint, JSON, DevSecOps, Dark mode |

---

## Referencias cruzadas

- [Manual de usuario — glosario breve](manual-usuario.md#11-glosario)
- [Integración en red](integracion-red.md)
- [Manual de laboratorio](manual-laboratorio.md)
- [Manual de desarrollador](manual-desarrollador.md)
