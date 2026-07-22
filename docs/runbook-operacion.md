# Runbook operativo — SecOps Hub

Guía rápida para el equipo SOC / DevSecOps (P3).

## Arranque con Docker Compose

```bash
cp .env.docker.example .env
# Editar SECRET_KEY, JWT_SECRET_KEY, WEBHOOK_API_KEY, BOOTSTRAP_ADMIN_PASSWORD
docker compose up -d --build
```

- UI: http://localhost
- API/health: http://localhost/health
- Métricas: http://localhost/metrics
- Prometheus (opcional): `docker compose --profile observability up -d`

## Migraciones (Alembic)

```bash
cd backend
source venv/bin/activate
# Asegura DATABASE_URL en .env
alembic upgrade head
```

En desarrollo `create_all` + `ensure_schema` siguen cubriendo columnas nuevas.

## Rotación de WEBHOOK_API_KEY

1. Admin → **Admin** → Rotar clave
2. Copiar la clave mostrada (solo una vez)
3. Actualizar Alert Action Splunk / Rule Response QRadar
4. Probar: `POST /api/webhooks/alert` con la nueva `X-API-Key`

La clave rotada se guarda en `app_settings` y tiene prioridad sobre `.env`.

## 4-eyes (playbooks destructivos)

Con `PLAYBOOK_FOUR_EYES=true` (por defecto):

1. Admin A pulsa **Solicitar** en un playbook destructivo
2. Queda en cola `pending`
3. Admin B distinto aprueba o rechaza en la misma pantalla
4. Solo tras aprobación se ejecuta el runner (live/simulado)

Desactivar: `PLAYBOOK_FOUR_EYES=false`.

## Cookies httpOnly

```env
AUTH_COOKIE_MODE=true
JWT_COOKIE_SECURE=true   # producción HTTPS
```

El frontend usa `withCredentials` y deja de persistir tokens en `localStorage`.

## SSO OIDC (Entra ID / IdP)

```env
OIDC_ENABLED=true
OIDC_ISSUER=https://login.microsoftonline.com/<tenant-id>/v2.0
OIDC_CLIENT_ID=...
OIDC_CLIENT_SECRET=...
OIDC_REDIRECT_URI=https://secops.empresa.local/api/auth/oidc/callback
OIDC_FRONTEND_REDIRECT=https://secops.empresa.local
OIDC_ADMIN_GROUP=SecOps-Admins   # opcional
```

Login: botón **Continuar con SSO** → `/api/auth/oidc/login`.

## Observabilidad

```bash
docker compose --profile observability up -d
```

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin por defecto)

1. En **Admin**, sección MFA de tu cuenta → Generar secreto
2. Añadir a Google Authenticator / Aegis / etc.
3. Confirmar con un código de 6 dígitos
4. En siguientes logins se pedirá OTP

## LDAP (opcional)

```env
LDAP_ENABLED=true
LDAP_SERVER=ldap://ldap.empresa.local
LDAP_BASE_DN=ou=people,dc=empresa,dc=local
LDAP_USER_DN_TEMPLATE=uid={username},{base_dn}
LDAP_DEFAULT_ROLE=analyst
```

Si el bind LDAP tiene éxito y el usuario no existe localmente, se provisiona automáticamente.

## Refresh tokens

Login devuelve `access_token` + `refresh_token`. El frontend renueva automáticamente ante 401 vía `POST /api/auth/refresh`.

## Monitorización

| Endpoint | Uso |
|----------|-----|
| `/health` | Liveness/readiness (DB) |
| `/metrics` | Prometheus (`secops_http_*`, `secops_incidents_open`, …) |

Importar dashboard Grafana apuntando al job `secops-hub`.

## Incidentes frecuentes

| Síntoma | Acción |
|---------|--------|
| 401 en webhook | Clave rotada o SIEM desactualizado |
| Login LDAP falla | Revisar DN template y conectividad al LDAP |
| `/metrics` vacío en multi-worker | Preferir 1 worker o sidecar; gauges se refrescan por petición |
| Admin 403 | Rol analyst sin permisos — usar cuenta admin |
