#!/usr/bin/env bash
# Helper script to set or verify the Telegram Bot Webhook
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Usage: ./set_webhook.sh <SERVICE_URL> [BOT_TOKEN]"
  echo "Example: ./set_webhook.sh https://omnichannel-gateway-75904656792.us-central1.run.app"
  exit 1
fi

SERVICE_URL="$1"
BOT_TOKEN="${2:-${TELEGRAM_BOT_TOKEN:-}}"

if [ -z "$BOT_TOKEN" ]; then
  echo "⚠️ TELEGRAM_BOT_TOKEN not provided as argument or environment variable."
  echo "Please export TELEGRAM_BOT_TOKEN or pass as second argument."
  exit 1
fi

WEBHOOK_URL="${SERVICE_URL}/webhook/telegram"
echo "🔗 Registering Telegram Webhook: ${WEBHOOK_URL}..."

curl -s "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook?url=${WEBHOOK_URL}" | jq . || curl -s "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook?url=${WEBHOOK_URL}"
echo ""
echo "ℹ️ Checking Webhook Info:"
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo" | jq . || curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
echo ""
