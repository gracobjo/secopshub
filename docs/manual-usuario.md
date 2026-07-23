# Manual de usuario — SecOps Hub

## 1. Introducción

**SecOps Hub** es una consola web de operaciones de ciberseguridad (SOC) que permite monitorizar incidentes, analizar indicadores de compromiso (IOCs), gestionar vulnerabilidades (incluido el catálogo CISA KEV) y ejecutar playbooks de respuesta automatizada.

Este manual está dirigido a **analistas de seguridad** y **administradores** que utilizan la plataforma en su día a día.

---

## 2. Requisitos de acceso

| Requisito | Detalle |
|-----------|---------|
| Navegador | Chrome, Firefox o Edge (versiones recientes) |
| URL desarrollo | http://localhost:5173 |
| URL unificada (build / Docker) | http://localhost:5000 o http://localhost:80 |
| Credenciales | Proporcionadas por el administrador |

### Usuarios de demostración (solo con `ENABLE_SEED=true`)

| Usuario | Contraseña | Rol | Capacidades principales |
|---------|------------|-----|-------------------------|
| `admin` | `admin123` | Administrador | Todo + playbooks, Admin UI, sync KEV, rotar webhook |
| `analyst` | `analyst123` | Analista | Dashboard, IOCs, vulns, PDF; sin ejecutar playbooks |

> En producción use `ENABLE_SEED=false` y cree el admin con bootstrap / script.

---

## 3. Inicio de sesión

1. Abra la URL de la aplicación.
2. Introduzca **usuario** y **contraseña**.
3. Si tiene **MFA** activado, introduzca el código de su app Authenticator.
4. Si la organización tiene **SSO (OIDC)** habilitado, use el botón *Continuar con SSO*.
5. Pulse **Iniciar sesión**.

La sesión usa JWT (access ~8 h). El cliente puede renovar con refresh token antes de pedirle de nuevo la contraseña.

### Cierre de sesión

En la barra lateral, pulse **Cerrar sesión**. Se limpian tokens/cookies.

---

## 4. Interfaz general

```
┌─────────────────────────────────────────────────────────┐
│  SIDEBAR          │  ÁREA PRINCIPAL                     │
│  SecOps Hub       │                                     │
│  • Dashboard      │  Contenido de la sección            │
│  • IOCs           │                                     │
│  • Vulnerabilid.  │                                     │
│  • Playbooks      │                                     │
│  • Admin          │  (solo rol admin)                   │
│  [Usuario/Rol]    │                                     │
│  [Cerrar sesión]  │                                     │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Dashboard

**Ruta:** `/` (Dashboard)

Vista general del estado de seguridad de la organización.

### KPIs (tarjetas superiores)

| KPI | Descripción |
|-----|-------------|
| Alertas activas | Incidentes en estado `open` o `investigating` |
| IPs bloqueadas | IOCs marcados como bloqueados |
| Vulnerabilidades KEV | CVEs en explotación activa (CISA KEV) abiertas |
| Total incidentes | Número total de incidentes registrados |

### Gráficos

- **Distribución por severidad:** barras con incidentes activos por nivel (critical, high, medium, low).
- **Eventos por hora (24h):** línea temporal de actividad reciente.

### Feed de auditoría

Lista las últimas acciones realizadas por usuarios del sistema (enriquecimiento de IOCs, ejecución de playbooks, cambios de incidentes, etc.).

### Detalle de KPIs, gestión de incidentes e informes PDF

Al pulsar cualquier KPI (Alertas activas, IPs bloqueadas, etc.) se abre un modal con el listado detallado.

En **incidentes** puede:

1. Cambiar el **estado** (`open`, `investigating`, `resolved`, `closed`).
2. **Asignar** el incidente a un usuario existente (campo username).
3. Pulsar **Guardar** — se registra en el feed de auditoría y se actualizan los KPIs.
4. Pulsar **PDF** para descargar el informe ejecutivo (`Reporte_Incidente_<ID>.pdf`).

Si cierra un incidente desde «Alertas activas», desaparece de esa lista al guardar.

---

## 6. Triaje de IOCs

**Ruta:** `/iocs`

Módulo para analizar indicadores de compromiso (IPs, hashes, URLs).

### Enriquecer un IOC

1. Pegue o escriba el valor en el campo de texto (IP, hash MD5/SHA1/SHA256 o URL).
2. Pulse **Enriquecer**.
3. Revise el resultado:
   - **Veredicto:** `MALICIOUS`, `SUSPICIOUS` o `CLEAN`
   - **Puntuación de riesgo:** 0–100
   - **VirusTotal / AbuseIPDB:** live si hay API keys configuradas; si no, **simulado** (badge en la UI)
   - **Recomendación:** bloquear o monitorizar

> El modo (`enrichment_mode`) indica si los datos vienen de APIs reales o del simulador pedagógico.

### Tabla de IOCs registrados

Muestra todos los IOCs almacenados con tipo, riesgo, veredicto y estado de bloqueo.

### Bloquear un IOC

Para IOCs con veredicto **malicious** que aún no están bloqueados, aparece el botón **Bloquear** (o **Bloquear en FW** si es una IP).

1. Confirme el diálogo de seguridad.
2. El IOC se marca como bloqueado en SecOps Hub.
3. Si el IOC es una **IP**, se ejecuta además el playbook `block_ip` (firewall/callback si está configurado; si no, modo simulado).
4. La acción queda en el log de auditoría.

> **Acceso:** Requiere rol `analyst` o `admin`.

---

## 7. Vulnerabilidades

**Ruta:** `/vulnerabilities`

Tabla de CVEs con información de severidad, puntuación CVSS, sistemas afectados y estado.

### Filtros

| Filtro | Uso |
|--------|-----|
| Severidad | Desplegable: Todas, Critical, High, Medium, Low |
| Solo CISA KEV | Checkbox para mostrar únicamente vulnerabilidades en explotación activa |

### Columnas

- **CVE:** identificador (ej. `CVE-2024-3400`)
- **Título:** descripción breve
- **Severidad / CVSS:** nivel y puntuación
- **KEV:** badge si está en el catálogo CISA Known Exploited Vulnerabilities
- **Sistemas afectados:** activos impactados
- **Estado:** editable (`open`, `in_progress`, `mitigated`, `accepted`, `closed`)

### Acciones

1. Cambiar el **estado** desde el desplegable de cada fila (analista o admin).
2. **Sync CISA KEV** (solo admin): descarga el feed oficial e inserta/actualiza CVEs explotados activamente.

---

## 8. Playbooks de respuesta

**Ruta:** `/playbooks`

Automatizaciones de respuesta a incidentes.

### Playbooks disponibles

| Playbook | Descripción | Parámetros | Destructivo |
|----------|-------------|------------|:-----------:|
| Aislar Host | Desconecta un host vía EDR (Defender/Falcon) | `hostname`, `device_id` opcional | Sí |
| Revocar Usuario | Revoca sesiones vía Azure AD Graph | `username` | Sí |
| Bloquear IP | Deny list en firewall / callback SOAR | `ip` | Sí |
| Escaneo de Datos | Busca datos sensibles (siempre simulado) | `target` | No |

### Ejecutar un playbook

1. Como **administrador**, rellene parámetros y pulse **Ejecutar** (confirme el diálogo).
2. El backend exige `confirm=true` en acciones destructivas.
3. Sin integración → modo **simulado**; con credenciales → **live**.
4. Si `PLAYBOOK_FOUR_EYES` está activo, las acciones destructivas quedan **pendientes** hasta que **otro** admin apruebe o rechace en la cola de aprobaciones.

> Los **analyst** ven los playbooks pero no los ejecutan.

### Webhook de alertas externas

```http
POST /api/webhooks/alert
Header: X-API-Key: <WEBHOOK_API_KEY>
Content-Type: application/json

{
  "title": "Alerta desde SIEM",
  "severity": "high",
  "source": "Splunk",
  "src_ip": "203.0.113.50",
  "external_id": "splunk-88421"
}
```

Soporta idempotencia (`Idempotency-Key` / `external_id`) para no duplicar incidentes. La clave puede rotarse desde **Admin**.

---

## 9. Administración (`/admin`)

Solo rol **admin**.

| Acción | Descripción |
|--------|-------------|
| Crear usuarios | Username, email, password, rol |
| Listar / editar | Cambiar rol o desactivar (`is_active`) |
| MFA | Setup TOTP (QR / otpauth) y activar |
| Webhook key | Ver meta enmascarada y **rotar** (copiar clave una vez) |

---

## 10. Matriz de permisos por rol

| Funcionalidad | Admin | Analyst |
|---------------|:-----:|:-------:|
| Dashboard / IOCs / Vulns / PDF | ✓ | ✓ |
| Sync CISA KEV | ✓ | ✗ |
| Ejecutar playbooks | ✓ | ✗ |
| Aprobar playbooks 4-eyes | ✓ | ✗ |
| Página Admin / usuarios | ✓ | ✗ |
| Rotar webhook key | ✓ | ✗ |
| Activar MFA propio | ✓ | ✓ |

---

## 11. Resolución de problemas

| Problema | Solución |
|----------|----------|
| Pide código MFA | Introduzca OTP de Authenticator; si perdió el factor, un admin debe desactivar MFA |
| Playbook queda pendiente | Four-eyes activo: otro admin debe aprobar |
| 403 en playbooks / Admin | Su usuario no es admin |
| Tras rotar webhook, SIEM falla | Actualice `X-API-Key` en Splunk/QRadar/Wazuh |
| Token / sesión caducada | El cliente intenta refresh; si falla, vuelva a login |
| Página en blanco en :5000 | Backend activo; en Docker use el puerto del frontend |

---

## 12. Glosario

Consulta el **[Diccionario completo](diccionario.md)** y la **[Guía de carpetas](guia-carpetas.md)** (para no técnicos).

| Término | Definición breve |
|---------|------------------|
| **IOC** | Indicador de compromiso |
| **KEV** | Catálogo CISA de CVEs explotados |
| **Playbook** | Respuesta automatizada |
| **Four-eyes** | Doble autorización admin |
| **MFA / TOTP** | Segundo factor |
| **OIDC / SSO** | Login corporativo |
| **Webhook** | Alerta SIEM → Hub |

Prácticas Jupyter: carpeta [`formacion/`](../formacion/README.md).
