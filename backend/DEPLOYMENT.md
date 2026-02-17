# Backend Deployment Guide

This guide covers deploying the Auto Structure Analysis backend to Google Cloud Run.

## Prerequisites

1. Google Cloud Project with billing enabled
2. `gcloud` CLI installed and configured
3. Docker installed (for local testing)

## Configuration

### Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and configure:

- `API_KEY_ENABLED`: Set to `true` to require API key authentication
- `API_KEY`: Your secret API key (generate a strong random string)
- `CORS_ORIGINS`: Comma-separated list of allowed origins
- `RATE_LIMIT_PER_MINUTE`: Requests per minute per IP (default: 30)
- `MAX_UPLOAD_SIZE_MB`: Maximum file upload size (default: 10)

## Local Testing

### Run with Docker

```bash
# Build the image
docker build -t auto-structure-backend .

# Run locally
docker run -p 8000:8000 \
  -e API_KEY_ENABLED=false \
  -e CORS_ORIGINS="http://localhost:5173,http://localhost:3000" \
  auto-structure-backend

# Test the endpoint
curl http://localhost:8000/health
```

### Run with uv (Development)

```bash
# Install dependencies
uv sync

# Run the server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Deployment Options

### Option 1: Google Cloud Build (Recommended)

1. Set your GCP project:

```bash
gcloud config set project YOUR_PROJECT_ID
```

2. Enable required APIs:

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

3. Deploy using Cloud Build:

```bash
gcloud builds submit --config cloudbuild.yaml ..
```

This will:
- Build the Docker image
- Push to Google Container Registry
- Deploy to Cloud Run

### Option 2: GitHub Actions

1. Add secrets to your GitHub repository:
   - `GCP_PROJECT_ID`: Your Google Cloud project ID
   - `GCP_SA_KEY`: Service account JSON key with Cloud Run Admin and Storage Admin roles

2. Push to main branch:

```bash
git push origin main
```

The workflow will automatically deploy on changes to `backend/`.

### Option 3: Manual Deployment

1. Build and push the image:

```bash
# Authenticate Docker with GCR
gcloud auth configure-docker

# Build the image
docker build -t gcr.io/YOUR_PROJECT_ID/auto-structure-analysis-backend:latest .

# Push to GCR
docker push gcr.io/YOUR_PROJECT_ID/auto-structure-analysis-backend:latest
```

2. Deploy to Cloud Run:

```bash
gcloud run deploy auto-structure-analysis-backend \
  --image gcr.io/YOUR_PROJECT_ID/auto-structure-analysis-backend:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --max-instances 10 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars CORS_ORIGINS=https://johntfoster.github.io,http://localhost:5173 \
  --set-env-vars RATE_LIMIT_ENABLED=true \
  --set-env-vars API_KEY_ENABLED=true \
  --set-env-vars API_KEY=your-secret-key-here
```

## Post-Deployment

### Get Service URL

```bash
gcloud run services describe auto-structure-analysis-backend \
  --region us-central1 \
  --format 'value(status.url)'
```

### View Logs

```bash
gcloud run services logs read auto-structure-analysis-backend \
  --region us-central1 \
  --limit 50
```

### Update Environment Variables

```bash
gcloud run services update auto-structure-analysis-backend \
  --region us-central1 \
  --update-env-vars RATE_LIMIT_PER_MINUTE=60
```

## Security Considerations

1. **API Key Authentication**: Enable `API_KEY_ENABLED=true` for production and generate a strong API key
2. **CORS**: Update `CORS_ORIGINS` to only include your production frontend domain
3. **Rate Limiting**: Adjust `RATE_LIMIT_PER_MINUTE` based on expected traffic
4. **File Upload**: Keep `MAX_UPLOAD_SIZE_MB` reasonable (10MB is recommended)
5. **HTTPS**: Cloud Run provides HTTPS by default - always use it

## Monitoring

### Health Check

```bash
curl https://your-service-url/health
```

### Metrics

View metrics in Google Cloud Console:
- Request count and latency
- Error rates
- Instance count
- Memory and CPU usage

## Troubleshooting

### Container fails to start

Check logs:
```bash
gcloud run services logs read auto-structure-analysis-backend --region us-central1
```

### Out of memory errors

Increase memory:
```bash
gcloud run services update auto-structure-analysis-backend \
  --region us-central1 \
  --memory 4Gi
```

### Slow cold starts

Increase minimum instances:
```bash
gcloud run services update auto-structure-analysis-backend \
  --region us-central1 \
  --min-instances 1
```

## Database

The backend uses SQLite for persistent storage. In Cloud Run, the database is stored in the container's filesystem and is **ephemeral** (resets on deployment).

For production, consider:

1. **Cloud SQL**: Migrate to PostgreSQL for persistent storage
2. **Firestore**: Use Firestore for document-based storage
3. **Cloud Storage**: Store database file in a bucket (with file locking considerations)

To switch to Firestore, update `DATABASE_URL` environment variable and implement Firestore client in `app/database.py`.

## Cost Optimization

- Use `--min-instances 0` to scale to zero when idle
- Set `--max-instances` to prevent runaway costs
- Monitor usage in Cloud Console billing section
- Consider Cloud Run's free tier: 2 million requests/month
