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
| URL alternativa | http://localhost:5000 (build de producción) |
| Credenciales | Proporcionadas por el administrador del sistema |

### Usuarios de demostración

| Usuario | Contraseña | Rol | Capacidades principales |
|---------|------------|-----|-------------------------|
| `admin` | `admin123` | Administrador | Todo lo del analista + ejecutar playbooks + registrar usuarios (API) |
| `analyst` | `analyst123` | Analista | Dashboard, IOCs, vulnerabilidades, consulta de playbooks |

> **Nota de seguridad:** Cambie las contraseñas demo antes de usar la plataforma en un entorno real.

---

## 3. Inicio de sesión

1. Abra la URL de la aplicación en el navegador.
2. Introduzca su **usuario** y **contraseña**.
3. Pulse **Iniciar sesión**.

Si las credenciales son incorrectas, verá el mensaje *"Credenciales inválidas"*. Si cierra sesión o el token expira (8 horas), será redirigido automáticamente al login.

### Cierre de sesión

En la barra lateral inferior, pulse **Cerrar sesión**. El token JWT se elimina del navegador.

---

## 4. Interfaz general

La aplicación usa un diseño **dark mode** orientado a entornos SOC:

```
┌─────────────────────────────────────────────────────────┐
│  SIDEBAR          │  ÁREA PRINCIPAL                     │
│  ─────────        │  ───────────────                    │
│  SecOps Hub       │  Título de la sección               │
│                   │  Contenido (tarjetas, tablas,       │
│  • Dashboard      │  gráficos, formularios)             │
│  • IOCs           │                                     │
│  • Vulnerabilid.  │                                     │
│  • Playbooks      │                                     │
│                   │                                     │
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
   - **VirusTotal (simulado):** detecciones maliciosas, sospechosas, limpias
   - **AbuseIPDB (simulado):** solo para direcciones IP
   - **Recomendación:** bloquear o monitorizar

### Tabla de IOCs registrados

Muestra todos los IOCs almacenados con tipo, riesgo, veredicto y estado de bloqueo.

### Bloquear un IOC

Para IOCs con veredicto **malicious** que aún no están bloqueados, aparece el botón **Bloquear**. Al pulsarlo, el IOC queda marcado como bloqueado y se registra en el log de auditoría.

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
- **Estado:** open, in_progress, mitigated, etc.

---

## 8. Playbooks de respuesta

**Ruta:** `/playbooks`

Automatizaciones de respuesta a incidentes.

### Playbooks disponibles

| Playbook | Descripción | Parámetros |
|----------|-------------|------------|
| Aislar Host | Desconecta un host de la red | `hostname` |
| Revocar Usuario | Revoca credenciales y sesiones | `username` |
| Escaneo de Datos | Busca datos sensibles expuestos | `target` |

### Ejecutar un playbook

1. Si es **administrador**, rellene los parámetros opcionales.
2. Pulse **Ejecutar**.
3. El resultado aparece en la sección *Resultados de ejecución*.

> Los usuarios con rol **analyst** pueden ver los playbooks pero **no ejecutarlos**. El botón aparece deshabilitado.

### Webhook de alertas externas

Sistemas externos (SIEM, EDR, etc.) pueden enviar alertas mediante:

```http
POST /api/webhooks/alert
Header: X-API-Key: secops-webhook-key-dev
Content-Type: application/json

{
  "title": "Alerta desde SIEM",
  "description": "Detalle del evento",
  "severity": "high",
  "source": "Splunk"
}
```

Las alertas recibidas se registran como nuevos incidentes en el dashboard.

---

## 9. Matriz de permisos por rol

| Funcionalidad | Admin | Analyst |
|---------------|:-----:|:-------:|
| Ver dashboard | ✓ | ✓ |
| Ver vulnerabilidades | ✓ | ✓ |
| Enriquecer / bloquear IOCs | ✓ | ✓ |
| Consultar playbooks | ✓ | ✓ |
| **Ejecutar playbooks** | ✓ | ✗ |
| Registrar usuarios (API) | ✓ | ✗ |

---

## 10. Resolución de problemas

| Problema | Solución |
|----------|----------|
| Redirige al login constantemente | Token expirado (8 h) o inválido; vuelva a iniciar sesión |
| Error 403 en IOCs | Su usuario no tiene rol analyst/admin |
| No puedo ejecutar playbooks | Solo administradores pueden ejecutarlos |
| Página en blanco en :5000 | Asegúrese de que el backend está activo; use :5173 en desarrollo |
| Gráficos vacíos | Compruebe que hay datos de incidentes en la base de datos |

---

## 11. Glosario

| Término | Definición |
|---------|------------|
| **IOC** | Indicador de compromiso (IP, hash, URL maliciosa) |
| **KEV** | Known Exploited Vulnerabilities — catálogo CISA de CVEs explotados activamente |
| **Playbook** | Secuencia automatizada de respuesta a incidentes |
| **SOC** | Security Operations Center — centro de operaciones de seguridad |
| **JWT** | JSON Web Token — credencial de sesión tras el login |
| **RBAC** | Control de acceso basado en roles (admin / analyst) |
