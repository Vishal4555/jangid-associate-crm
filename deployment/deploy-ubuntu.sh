#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR=/var/www/jangid-associate-crm
SERVICE_NAME=jangid-associate-crm-api
SITE_NAME=jangid-associate-crm

cd "$APP_DIR/frontend"
npm ci
npm run build

sudo install -D -m 644 "$APP_DIR/deployment/nginx/$SITE_NAME.conf" \
  "/etc/nginx/sites-available/$SITE_NAME"
sudo install -D -m 644 "$APP_DIR/deployment/systemd/$SERVICE_NAME.service" \
  "/etc/systemd/system/$SERVICE_NAME.service"
sudo ln -sfn "/etc/nginx/sites-available/$SITE_NAME" \
  "/etc/nginx/sites-enabled/$SITE_NAME"
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl reload nginx

curl --fail --silent --show-error http://127.0.0.1:8000/openapi.json >/dev/null
assert_json_api_response() {
  local endpoint="$1"
  local response
  response=$(curl --silent --output /dev/null --write-out '%{http_code} %{content_type}' \
    --header 'Accept: application/json' "http://127.0.0.1${endpoint}")

  case "$response" in
    200\ application/json*|401\ application/json*) ;;
    *)
      echo "Expected a JSON response from ${endpoint}, received: ${response}" >&2
      exit 1
      ;;
  esac
}

login_status=$(curl --silent --output /dev/null --write-out '%{http_code}' \
  --request POST http://127.0.0.1:8000/api/auth/login \
  --header 'Content-Type: application/json' \
  --data '{"username":"route-check","password":"invalid-password"}')
test "$login_status" = 401
assert_json_api_response /api/masters/banks
assert_json_api_response /api/masters/branches
echo "Deployment complete. The browser API base URL is /api."
