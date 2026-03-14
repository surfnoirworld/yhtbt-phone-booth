#!/bin/bash
# YHTBT Phone Booth — Cloud Run Deploy Script
# Usage: ./deploy.sh <project_id> <api_key>

set -e

PROJECT_ID=${1:?"Usage: ./deploy.sh <project_id> <api_key>"}
API_KEY=${2:?"Usage: ./deploy.sh <project_id> <api_key>"}
REGION="us-east1"
SERVICE_NAME="yhtbt-phone-booth"

echo "=== YHTBT Phone Booth Deploy ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo ""

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling APIs..."
gcloud services enable run.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Create Firestore database if it doesn't exist
echo "Setting up Firestore..."
gcloud firestore databases create --location=$REGION 2>/dev/null || echo "Firestore already exists"

# Grant required permissions to default compute service account
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SA" --role="roles/logging.logWriter" --quiet
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SA" --role="roles/storage.objectAdmin" --quiet
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SA" --role="roles/artifactregistry.writer" --quiet
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SA" --role="roles/datastore.user" --quiet

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_API_KEY=$API_KEY,GOOGLE_GENAI_USE_VERTEXAI=FALSE" \
  --memory 1Gi \
  --timeout 300 \
  --session-affinity

echo ""
echo "=== Deploy Complete ==="
echo "Service URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
echo ""
echo "WebSocket endpoint: wss://<service-url>/ws/{caller_id}"