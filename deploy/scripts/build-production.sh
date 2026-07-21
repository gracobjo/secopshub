#!/usr/bin/env bash
# Compila el frontend y verifica dependencias del backend para producción.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "==> Compilando frontend..."
cd "$ROOT/frontend"
npm ci
npm run build

echo "==> Verificando backend..."
cd "$ROOT/backend"
if [[ ! -d venv ]]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "Listo. Siguiente paso (Fase 1):"
echo "  1. Copiar proyecto a /opt/secops-hub"
echo "  2. Configurar backend/.env (claves >= 32 chars, ENABLE_SEED=false)"
echo "  3. Instalar deploy/systemd/secops-hub.service"
echo "  4. Instalar deploy/nginx/secops-hub.conf o deploy/caddy/Caddyfile"
echo "  5. systemctl enable --now secops-hub && systemctl reload nginx"
