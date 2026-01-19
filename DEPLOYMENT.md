# Deployment Guide: GitHub → Google Cloud Run

This guide explains how to set up continuous deployment from GitHub to Google Cloud Run.

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **GitHub repository** with your code
3. **gcloud CLI** installed locally (optional, for setup)

## Setup Instructions

### 1. Set up Google Cloud Project

```bash
# Install gcloud CLI if not already installed
# https://cloud.google.com/sdk/docs/install

# Login to Google Cloud
gcloud auth login

# Create a new project (or use existing)
gcloud projects create toolssreekar2858 --name="JobSearch API"

# Set the project
gcloud config set project toolssreekar2858

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  containerregistry.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com
```

### 2. Create Artifact Registry Repository

```bash
# Create a Docker repository in Artifact Registry
gcloud artifacts repositories create jobsearch-api \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker repository for JobSearch API"
```

### 3. Create Service Account for GitHub Actions

```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Deployment"

# Grant necessary permissions
gcloud projects add-iam-policy-binding toolssreekar2858 \
  --member="serviceAccount:github-actions@toolssreekar2858.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding toolssreekar2858 \
  --member="serviceAccount:github-actions@toolssreekar2858.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding toolssreekar2858 \
  --member="serviceAccount:github-actions@toolssreekar2858.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Create and download key
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions@toolssreekar2858.iam.gserviceaccount.com
```

### 4. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

1. **GCP_PROJECT_ID**: Your Google Cloud project ID
2. **GCP_SA_KEY**: Contents of the `key.json` file (entire JSON)

**Security Note:** Delete the `key.json` file after adding it to GitHub secrets!

```bash
rm key.json
```

### 5. Update Workflow Configuration

Edit `.github/workflows/deploy.yml` and update:

```yaml
env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  SERVICE_NAME: jobsearch-api
  REGION: us-central1 # Change to your preferred region (e.g., europe-west1, asia-east1)
```

Available regions: https://cloud.google.com/run/docs/locations

### 6. Push to GitHub

```bash
git add .
git commit -m "Add Cloud Run deployment"
git push origin main
```

GitHub Actions will automatically:

1. Build the Docker image
2. Push to Google Artifact Registry
3. Deploy to Cloud Run
4. Output the deployment URL

### 7. Access Your API

After deployment completes:

- Check the GitHub Actions logs for the deployment URL
- Or run: `gcloud run services describe jobsearch-api --region us-central1 --format 'value(status.url)'`

Your API will be available at: `https://jobsearch-api-XXXXXXXXXX-uc.a.run.app`

## Environment Variables

To add environment variables (API keys, database URLs, etc.):

```bash
gcloud run services update jobsearch-api \
  --region us-central1 \
  --set-env-vars="API_KEY=your-key,DATABASE_URL=your-db-url"
```

Or add them in `.github/workflows/deploy.yml`:

```yaml
--set-env-vars="API_KEY=${{ secrets.API_KEY }},DATABASE_URL=${{ secrets.DATABASE_URL }}"
```

## Cost Optimization

Cloud Run charges only when your service is processing requests:

```bash
# Set minimum instances to 0 (default)
gcloud run services update jobsearch-api \
  --region us-central1 \
  --min-instances 0 \
  --max-instances 10

# For production with consistent traffic, keep warm instances:
gcloud run services update jobsearch-api \
  --region us-central1 \
  --min-instances 1 \
  --max-instances 20
```

## Monitoring

View logs:

```bash
gcloud run services logs read jobsearch-api --region us-central1 --limit 50
```

Or view in Google Cloud Console:

- https://console.cloud.google.com/run

## Troubleshooting

### Build fails

- Check GitHub Actions logs
- Verify all dependencies in `requirements.txt`

### Deployment fails

- Check service account permissions
- Verify Artifact Registry repository exists
- Check Cloud Run API is enabled

### Service crashes

- View logs: `gcloud run services logs read jobsearch-api --region us-central1`
- Check memory/CPU limits
- Verify PORT environment variable is used

### Cold starts are slow

- Playwright browser installation takes time
- Consider keeping min-instances at 1 for production
- Or use a smaller base image with pre-installed browsers

## CI/CD Best Practices

1. **Staging Environment**: Create a separate Cloud Run service for staging

   ```bash
   # In deploy.yml, add branches for staging
   on:
     push:
       branches:
         - main      # production
         - staging   # staging environment
   ```

2. **Health Checks**: Add a health endpoint

   ```python
   @app.get("/health")
   async def health():
       return {"status": "healthy"}
   ```

3. **Secrets Management**: Use Google Secret Manager for sensitive data
   ```bash
   gcloud run services update jobsearch-api \
     --region us-central1 \
     --update-secrets=API_KEY=api-key:latest
   ```

## Manual Deployment (without GitHub)

If you want to deploy manually:

```bash
# Build locally
docker build -t gcr.io/toolssreekar2858/jobsearch-api .

# Push to Container Registry
docker push gcr.io/toolssreekar2858/jobsearch-api

# Deploy
gcloud run deploy jobsearch-api \
  --image gcr.io/toolssreekar2858/jobsearch-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Next Steps

- Set up custom domain: https://cloud.google.com/run/docs/mapping-custom-domains
- Add authentication: https://cloud.google.com/run/docs/authenticating/overview
- Set up monitoring alerts: https://cloud.google.com/run/docs/monitoring
- Configure CDN: https://cloud.google.com/cdn/docs/setting-up-cdn-with-serverless
