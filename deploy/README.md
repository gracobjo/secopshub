# Despliegue en producción — SecOps Hub

Guía para **Fase 1** del roadmap: servidor en red corporativa, TLS, reverse proxy y backend WSGI.

## Arquitectura

```
                    ┌─────────────────────────────────────┐
  SIEM / Analistas  │  Nginx o Caddy (:443 HTTPS)         │
  (VLAN SOC / VPN)  │  ├─ /          → frontend/dist      │
                    │  └─ /api/*     → Gunicorn :5000     │
                    └─────────────────────────────────────┘
                                      │
                              127.0.0.1:5000 (solo localhost)
                                      │
                              PostgreSQL (opcional Fase 1)
```

El backend **no se expone** directamente a la red: solo el reverse proxy escucha en `:443`.

---

## Requisitos del servidor

| Componente | Versión mínima |
|------------|----------------|
| SO | Ubuntu 22.04+ / RHEL 8+ / Debian 12+ |
| Python | 3.11+ |
| Node.js | 18+ (solo para compilar frontend) |
| Nginx **o** Caddy | Última estable |
| PostgreSQL | 14+ (recomendado producción) |

---

## Paso 1 — Compilar y copiar

```bash
# En máquina de build o en el servidor
git clone https://github.com/gracobjo/secopshub.git /opt/secops-hub
cd /opt/secops-hub
chmod +x deploy/scripts/build-production.sh
./deploy/scripts/build-production.sh
```

Windows (solo build del frontend):

```powershell
.\deploy\scripts\build-production.ps1
```

---

## Paso 2 — Variables de entorno

```bash
cp backend/.env.example backend/.env
nano backend/.env
```

**Obligatorio en producción:**

```env
FLASK_ENV=production
BEHIND_PROXY=true
ENABLE_SEED=false

SECRET_KEY=<generar: openssl rand -hex 32>
JWT_SECRET_KEY=<generar: openssl rand -hex 32>
WEBHOOK_API_KEY=<generar: openssl rand -hex 32>

DATABASE_URL=postgresql://secops:PASSWORD@localhost:5432/secops_hub
```

Generar claves (≥ 32 caracteres):

```bash
openssl rand -hex 32
```

---

## Paso 3 — Gunicorn (systemd)

```bash
sudo useradd -r -s /bin/false secops || true
sudo mkdir -p /var/log/secops-hub
sudo chown secops:secops /var/log/secops-hub

sudo cp deploy/systemd/secops-hub.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable secops-hub
sudo systemctl start secops-hub
sudo systemctl status secops-hub
```

Comprobar API local:

```bash
curl -s http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"..."}' 
# (con usuarios reales, no demo si ENABLE_SEED=false)
```

---

## Paso 4 — Reverse proxy

### Opción A: Nginx (CA interna o certificados propios)

```bash
# Ajustar server_name, ssl_certificate y root en el conf
sudo cp deploy/nginx/secops-hub.conf /etc/nginx/sites-available/secops-hub
sudo ln -sf /etc/nginx/sites-available/secops-hub /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**Let's Encrypt** (dominio público):

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d secops.empresa.com
```

**CA interna:** colocar certificado y clave en las rutas del `.conf` o usar certificados de la PKI corporativa.

### Opción B: Caddy (TLS automático)

```bash
sudo apt install caddy
sudo cp deploy/caddy/Caddyfile /etc/caddy/Caddyfile
# Editar dominio y rutas
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Para dominios `.local` sin DNS público, usar `tls internal` en el Caddyfile.

---

## Paso 5 — Firewall del servidor

```bash
# Solo analistas y SIEM (ajustar IPs/subredes)
sudo ufw allow from 10.10.20.0/24 to any port 443 proto tcp comment "VLAN SOC"
sudo ufw allow from 10.10.30.0/24 to any port 443 proto tcp comment "VPN analistas"
sudo ufw deny 5000/tcp
sudo ufw enable
```

El puerto **5000 no debe ser accesible** desde fuera; solo `127.0.0.1`.

---

## Paso 6 — Verificación

```bash
# Health check HTTPS
curl -k https://secops.empresa.local/api/integrations/status \
  -H "Authorization: Bearer <TOKEN>"

# Webhook de prueba (Fase 2)
curl -X POST https://secops.empresa.local/api/webhooks/alert \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <WEBHOOK_API_KEY>" \
  -d '{"title":"Test SIEM","severity":"high","source":"Splunk"}'
```

Abrir `https://secops.empresa.local` en navegador desde VLAN analistas.

---

## Rate limiting

Incluido en `deploy/nginx/secops-hub.conf`:

| Ruta | Límite |
|------|--------|
| `/api/webhooks/*` | 30 req/min por IP |
| `/api/*` | 120 req/min por IP |

Caddy: ver `deploy/caddy/Caddyfile`. Rate limiting incluido en Nginx; en Caddy requiere plugin `caddy-ratelimit` o usar Nginx.

---

## Backup PostgreSQL

```bash
# Cron diario (ejemplo)
0 2 * * * pg_dump -U secops secops_hub | gzip > /backup/secops_$(date +\%Y\%m\%d).sql.gz
```

---

## Referencias

- [Roadmap por fases](../docs/roadmap-integracion.md)
- [Integración SIEM Splunk/QRadar](../docs/integracion-red.md)
- [Manual desarrollador](../docs/manual-desarrollador.md)
