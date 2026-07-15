# App Engine UI deployment

The Streamlit UI is deployed separately from the API. The API runs on GKE through the Helm chart, while App Engine serves the UI.

The deployable `app.yaml` must stay in the repository root because App Engine deploys the directory that contains `app.yaml`.

Before deploying, update `API_URL` in `app.yaml` to the public GKE Ingress URL of the FastAPI service.

Manual deployment:

```bash
gcloud app deploy app.yaml --project <project_id>
```

Terraform only creates the App Engine application. It does not deploy App Engine service versions.
