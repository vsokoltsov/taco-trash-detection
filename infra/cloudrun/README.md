# Cloud Run UI Deployment

The Streamlit UI is deployed to Cloud Run from `Dockerfile.ui`.

The CI workflow builds and pushes the UI image to Artifact Registry, then deploys it with:

```bash
gcloud run deploy <service-name> \
  --image <artifact-registry-image>:<commit-sha> \
  --region <region> \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars API_URL=<api-url>
```

Cloud Run is used instead of App Engine because Streamlit requires a working WebSocket endpoint at `/_stcore/stream`.
