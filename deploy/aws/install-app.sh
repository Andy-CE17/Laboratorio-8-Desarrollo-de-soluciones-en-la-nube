#!/usr/bin/env bash
set -euo pipefail

# Uso en Amazon Linux 2023: sudo bash install-app.sh web-server-1
# Antes, coloca app.zip y app.env en /opt/tecnostock.
instance_name="${1:?Indica web-server-1 o web-server-2}"
base=/opt/tecnostock
test -f "$base/app.zip" || { echo "Falta $base/app.zip" >&2; exit 1; }
test -f "$base/app.env" || { echo "Falta $base/app.env" >&2; exit 1; }
chmod 600 "$base/app.env"

dnf install -y docker unzip
systemctl enable --now docker
mkdir -p "$base/source"
unzip -oq "$base/app.zip" -d "$base/source"
cd "$base/source"
docker build -t tecnostock:lab7 .

# La migración es idempotente. Ejecutarla en ambas EC2 permite reiniciar
# cualquiera de ellas sin depender de una máquina de administración.
docker run --rm --env-file "$base/app.env" tecnostock:lab7 python manage.py migrate --noinput
docker rm -f tecnostock 2>/dev/null || true
docker run -d --name tecnostock --restart unless-stopped \
  --env-file "$base/app.env" \
  -e "INSTANCE_NAME=$instance_name" \
  -p 80:8000 tecnostock:lab7

echo "Comprobando /health/"
health_host=$(sed -n 's/^DJANGO_ALLOWED_HOSTS=\([^,]*\).*/\1/p' "$base/app.env")
for attempt in {1..30}; do
  if curl --fail --silent -H "Host: $health_host" http://127.0.0.1/health/; then
    echo
    exit 0
  fi
  sleep 2
done
docker logs --tail 100 tecnostock >&2
exit 1
