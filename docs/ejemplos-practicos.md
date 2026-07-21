# Ejemplos prácticos y casos de prueba — SecOps Hub

Documento de escenarios operativos alineados con la **implementación real** de la plataforma. Indica qué funciona hoy, qué está simulado y cómo reproducir cada caso paso a paso.

---

## 0. Validación del escenario propuesto (malware / C2)

El escenario de *"Detección y Contención de una Infección por Malware"* describe un flujo SOC **conceptualmente correcto**, pero varios detalles **no coinciden** con el código actual:

| Paso del escenario | ¿Correcto? | Realidad en SecOps Hub |
|--------------------|:----------:|------------------------|
| Webhook desde SIEM | ✅ Parcial | Endpoint existe; el JSON del ejemplo usa campos incorrectos |
| API Key en webhook | ✅ | Header `X-API-Key`, valor demo: `secops-webhook-key-dev` |
| Login analyst + JWT | ✅ | Funciona con `analyst` / `analyst123` |
| KPI Alertas activas sube | ✅ | Tras webhook se incrementa el contador |
| "Tabla actividad tiempo real" | ⚠️ | No hay tabla live en dashboard; hay KPIs + feed auditoría. Incidentes en modal al pulsar KPI |
| Enriquecer IP en IOCs | ✅ | Funciona; botón **Enriquecer** (no "Analizar e Investigar") |
| VirusTotal + AbuseIPDB reales | ❌ | **Simulado** — score determinístico, no consulta APIs externas |
| "Categoría Cobalt Strike" | ❌ | No se muestra categoría de malware, solo veredicto y score |
| "Aplicar Bloqueo Preventivo" → firewall | ❌ | Botón **Bloquear** marca IOC en BD; **no** bloquea firewall real |
| Filtrar vulns por IP 10.0.1.50 | ❌ | No existe filtro por activo/IP; solo severidad y KEV |
| CVE-2023-34362 en catálogo | ❌ | No está en seed; hay otros CVEs KEV demo |
| Analyst ejecuta playbook | ❌ | Solo **admin** puede ejecutar playbooks |
| Playbook aísla vía SSH/iptables | ❌ | **Simulado** — devuelve mensaje de éxito, sin conexión SSH |
| Consola en vivo del playbook | ✅ Parcial | Panel de resultados estático tras ejecución, no streaming |

**Conclusión:** el flujo **Ingesta → Triaje → Análisis → Contención → Auditoría** es el diseño objetivo y el recorrido UI es válido como **simulación de laboratorio**. Para reproducción fiel, usa los ejemplos corregidos de este documento.

---

## Escenario 1 — Malware / C2 (versión corregida y ejecutable)

### Contexto

Servidor interno `10.0.1.50` con tráfico C2 hacia `198.51.100.45`. Reproduce el escenario original adaptado a la API real.

### Paso 1 — Ingesta (webhook)

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/webhooks/alert" `
  -Method POST -ContentType "application/json" `
  -Headers @{ "X-API-Key" = "secops-webhook-key-dev" } `
  -Body '{"title":"Tráfico C2 detectado desde 10.0.1.50","description":"Conexiones salientes desde 10.0.1.50 hacia 198.51.100.45. Posible comando y control.","severity":"high","source":"SIEM-Sensor-Red"}'
```

**Resultado esperado:** HTTP 201, incidente creado con `status: open`.

**Errores frecuentes:**

| Error | Causa |
|-------|-------|
| 401 | API Key incorrecta o ausente |
| severity `High` → medium | Severidad debe ser **minúsculas**: `high` |
| Campos `source_ip` ignorados | La API usa `title` + `description`, no `source_ip` |

### Paso 2 — Triaje (analista)

1. Login: http://localhost:5173 → `analyst` / `analyst123`
2. Dashboard → KPI **Alertas activas** → clic → ver incidente *Tráfico C2 detectado*
3. **Exportar PDF** (opcional) → descarga `Reporte_Incidente_<ID>.pdf`

### Paso 3 — Enriquecimiento IOC

1. Ir a **IOCs**
2. Pegar: `198.51.100.45`
3. Pulsar **Enriquecer**

**Resultado esperado:**

| Campo | Valor |
|-------|-------|
| Tipo | `ip` |
| Score | 0–100 (determinístico para esa IP) |
| Veredicto | `malicious`, `suspicious` o `clean` |
| AbuseIPDB | Datos simulados |

Si veredicto = `malicious` → pulsar **Bloquear** en la tabla.

### Paso 4 — Vulnerabilidades (análisis)

1. Ir a **Vulnerabilidades**
2. Activar **Solo CISA KEV**
3. Revisar CVEs abiertas (p. ej. `CVE-2024-3400`, `CVE-2023-4966`)

> No hay filtro por IP del servidor. El analista correlaciona manualmente con `affected_systems`.

### Paso 5 — Contención (admin)

1. Cerrar sesión → login `admin` / `admin123`
2. **Playbooks** → *Aislar Host*
3. Parámetro `hostname`: `SRV-WEB-050` (representando 10.0.1.50)
4. **Ejecutar**

**Resultado esperado:** *"Host SRV-WEB-050 aislado correctamente"* + entrada en feed de auditoría.

---

## Escenario 2 — Brute force desde IP externa

### Caso de prueba

```bash
curl -X POST http://localhost:5000/api/webhooks/alert \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secops-webhook-key-dev" \
  -d '{"title":"Brute force SSH","description":"847 intentos fallidos desde 203.0.113.77 contra servidor bastion","severity":"high","source":"Splunk"}'
```

### Acciones del analista

1. Dashboard → ver incremento en alertas activas
2. IOCs → enriquecer `203.0.113.77`
3. Si malicious → bloquear
4. Exportar PDF del incidente

### Resultado de validación

- [ ] Incidente visible en modal KPI
- [ ] IOC persistido tras enriquecimiento
- [ ] Audit log registra enriquecimiento/bloqueo
- [ ] PDF contiene cronología e IOCs asociados

---

## Escenario 3 — Phishing con URL maliciosa

### Webhook

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/webhooks/alert" `
  -Method POST -ContentType "application/json" `
  -Headers @{ "X-API-Key" = "secops-webhook-key-dev" } `
  -Body '{"title":"Phishing CEO fraud","description":"Usuario reportó email con enlace http://evil-phish.example/login","severity":"medium","source":"Email Gateway"}'
```

### IOC

Enriquecer en IOCs (si la URL es reconocida como tipo `url`):

```
http://evil-phish.example/login
```

**Nota:** URLs deben empezar por `http` para detectarse como tipo `url`.

---

## Escenario 4 — Exfiltración de datos (DLP)

Usa el incidente **precargado** del seed o crea uno nuevo:

```json
{
  "title": "Exfiltración DLP — SRV-FIN-01",
  "description": "Transferencia 2.3GB desde SRV-FIN-01 a 198.51.100.77",
  "severity": "critical",
  "source": "DLP"
}
```

### Flujo completo (Lab integrado)

| # | Actor | Acción |
|---|-------|--------|
| 1 | SIEM | Webhook crea incidente |
| 2 | analyst | Enriquece `198.51.100.77` |
| 3 | analyst | Bloquea IOC si malicious |
| 4 | analyst | Revisa KEV abiertas |
| 5 | admin | Playbook *Aislar Host* → `SRV-FIN-01` |
| 6 | admin | Playbook *Escaneo de Datos* → `SRV-FIN-01` |
| 7 | analyst | Exporta PDF del incidente |

---

## Escenario 5 — Escalada de privilegios (EDR)

Incidente seed: *"Escalada de privilegios detectada"* (EDR, high, open).

### Casos de prueba API

```powershell
# Login analyst
$login = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/auth/login" `
  -Method POST -ContentType "application/json" `
  -Body '{"username":"analyst","password":"analyst123"}'

# Listar incidentes activos
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/incidents?status=active" `
  -Headers @{ Authorization = "Bearer $($login.access_token)" }

# Intentar playbook como analyst (debe fallar 403)
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/playbooks/run" `
  -Method POST -ContentType "application/json" `
  -Headers @{ Authorization = "Bearer $($login.access_token)" } `
  -Body '{"playbook_id":"revoke_user","params":{"username":"jperez"}}'
```

**Resultado esperado del último paso:** Error 403.

---

## Escenario 6 — Exportación de informe PDF

### Desde la UI

1. Dashboard → KPI **Total incidentes** o **Alertas activas**
2. Clic en **Exportar PDF** en cualquier fila
3. Se descarga `Reporte_Incidente_<ID>.pdf`

### Desde API

```powershell
$login = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/auth/login" `
  -Method POST -ContentType "application/json" `
  -Body '{"username":"admin","password":"admin123"}'

Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/incidents/1/report/pdf" `
  -Headers @{ Authorization = "Bearer $($login.access_token)" } `
  -OutFile "Reporte_Incidente_1.pdf"
```

### Contenido del PDF

| Sección | Fuente de datos |
|---------|-----------------|
| Cabecera corporativa | Plantilla ReportLab |
| Resumen ejecutivo | Tabla `incidents` |
| Cronología | Incidente + `audit_logs` relacionados |
| IOCs | IPs/hashes en descripción o ventana temporal |
| Contención | Audit logs con playbooks/bloqueos |
| Firma analista | Claim JWT `username` |

---

## Matriz de casos de prueba

| ID | Caso | Entrada | Resultado esperado | Rol |
|----|------|---------|-------------------|-----|
| TC-01 | Login válido | admin/admin123 | JWT + redirect dashboard | admin |
| TC-02 | Login inválido | wrong/wrong | 401, mensaje error | — |
| TC-03 | Webhook válido | JSON + API Key | 201, incidente creado | — |
| TC-04 | Webhook sin API Key | JSON sin header | 401 | — |
| TC-05 | Severity inválida | `"severity":"urgent"` | Normaliza a `medium` | — |
| TC-06 | KPI alertas activas | Clic KPI | Modal con incidentes open/investigating | analyst |
| TC-07 | Enriquecer IP | 198.51.100.45 | Veredicto + score | analyst |
| TC-08 | Enriquecer hash SHA1 | da39a3ee... | Tipo sha1 | analyst |
| TC-09 | Bloquear IOC | IOC malicious | blocked=true, KPI IPs +1 | analyst |
| TC-10 | Filtro KEV | kev_only=true | Solo CVEs KEV | analyst |
| TC-11 | Playbook admin | isolate_host | 200, completed | admin |
| TC-12 | Playbook analyst | isolate_host | 403 Forbidden | analyst |
| TC-13 | Export PDF | GET /incidents/1/report/pdf | PDF descargado | analyst/admin |
| TC-14 | Token expirado | Request sin JWT | 401 → redirect login | — |
| TC-15 | Revocar usuario | revoke_user + jperez | Mensaje éxito simulado | admin |

---

## Payload webhook — plantilla correcta

```json
{
  "title": "Título breve del incidente",
  "description": "Detalle: IPs, hosts, hashes, contexto",
  "severity": "critical",
  "source": "Nombre del sistema origen"
}
```

| Campo | Obligatorio | Valores |
|-------|:-----------:|---------|
| `title` | Recomendado | Texto libre (default: "Alerta recibida vía Webhook") |
| `description` | Opcional | Texto libre; incluir IPs para correlación IOC/PDF |
| `severity` | Opcional | `critical`, `high`, `medium`, `low` (minúsculas) |
| `source` | Opcional | Ej: Splunk, QRadar, EDR, DLP |

**Header obligatorio:** `X-API-Key: secops-webhook-key-dev`

---

## Comparativa: laboratorio vs producción en red

| Capacidad | Hoy (demo) | Producción (ver integracion-red.md) |
|-----------|------------|-------------------------------------|
| Webhook SIEM | ✅ Real | ✅ Mismo endpoint |
| Dashboard KPI | ✅ Real | ✅ |
| Drill-down KPI | ✅ Real | ✅ |
| Enriquecimiento IOC | ⚠️ Simulado | AbuseIPDB + VirusTotal API |
| Bloqueo IOC | ⚠️ Solo BD | API firewall |
| Playbooks | ⚠️ Simulado | EDR / AD / SSH |
| Filtro vuln por activo | ❌ | CMDB / asset inventory |
| PDF informes | ✅ Real | ✅ |
| Tiempo real (WebSocket) | ❌ | Extensión futura |

---

## Scripts de prueba rápida (PowerShell)

Guardar como `scripts/test-scenario-malware.ps1`:

```powershell
$base = "http://127.0.0.1:5000"
$key = "secops-webhook-key-dev"

# 1. Webhook
$alert = Invoke-RestMethod -Uri "$base/api/webhooks/alert" -Method POST `
  -ContentType "application/json" -Headers @{ "X-API-Key" = $key } `
  -Body '{"title":"Test C2","description":"10.0.1.50 -> 198.51.100.45","severity":"high","source":"Test"}'
Write-Host "Incidente creado: ID $($alert.incident.id)"

# 2. Login analyst
$login = Invoke-RestMethod -Uri "$base/api/auth/login" -Method POST `
  -ContentType "application/json" -Body '{"username":"analyst","password":"analyst123"}'
$headers = @{ Authorization = "Bearer $($login.access_token)" }

# 3. Enriquecer IOC
$ioc = Invoke-RestMethod -Uri "$base/api/iocs/enrich" -Method POST `
  -ContentType "application/json" -Headers $headers `
  -Body '{"value":"198.51.100.45"}'
Write-Host "IOC veredicto: $($ioc.verdict) score: $($ioc.risk_score)"

# 4. PDF
$id = $alert.incident.id
Invoke-WebRequest -Uri "$base/api/incidents/$id/report/pdf" -Headers $headers `
  -OutFile "Reporte_Incidente_$id.pdf"
Write-Host "PDF generado: Reporte_Incidente_$id.pdf"
```

---

## Referencias

- [Manual de laboratorio](manual-laboratorio.md) — Labs 1–8
- [Integración en red](integracion-red.md) — Splunk, QRadar, EDR
- [Diccionario](diccionario.md) — Términos SOC
- [Manual de usuario](manual-usuario.md) — Uso de la consola
