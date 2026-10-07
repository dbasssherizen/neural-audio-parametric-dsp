#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="anima-sovereign-ai"
REGION="us-central1"
SERVICE_NAME="justin-comm-watcher"

echo "🚀 Deploying ${SERVICE_NAME} to Google Cloud Run in ${PROJECT_ID} (${REGION})..."

gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3

echo "✅ Successfully deployed ${SERVICE_NAME} to Cloud Run!"
