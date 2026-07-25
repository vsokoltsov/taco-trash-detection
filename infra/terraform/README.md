# Terraform infrastructure

This directory provisions the GCP infrastructure needed by the project:

- required Google APIs;
- VPC and subnet for GKE;
- GKE cluster for the FastAPI inference API;
- Artifact Registry Docker repository;
- Cloud Storage bucket for ONNX model files;
- Google service accounts and Workload Identity binding for API pods;
- GitHub Actions Workload Identity for Docker image publishing;
- Cloud Run API enablement for the Streamlit UI deployment.

Terraform intentionally does **not** deploy Helm releases and does **not** deploy the Cloud Run UI service.

Typical manual flow:

```bash
cd infra/terraform
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

## Destroying infrastructure

Some runtime resources are created by deployment tooling rather than Terraform:

- the API Helm release in GKE;
- the Kubernetes `LoadBalancer` service and its GCP forwarding-rule resources;
- the Streamlit UI Cloud Run service.

Clean those resources before `terraform destroy`:

```bash
cd infra/terraform
chmod +x destroy_cleanup.sh
PROJECT_ID=<project_id> ./destroy_cleanup.sh
terraform destroy -var-file=terraform.tfvars
```

The cleanup script also removes the App Engine application from Terraform state. App Engine applications cannot be deleted from a GCP project, so Terraform must not try to destroy that resource directly.

The model bucket is configured with `model_bucket_force_destroy = true` by default so Terraform can delete uploaded model artifacts during destroy.

If `configure_github_actions_variables = true`, export a GitHub token before destroy as well. Terraform needs it to delete repository variables managed by the GitHub provider:

```bash
export GITHUB_TOKEN=<token-with-repository-actions-variable-permissions>
```

Upload models to the bucket before deploying the API:

```bash
gsutil cp models/mask_rcnn_v1.pt gs://<model_bucket_name>/models/mask_rcnn_v1.pt
gsutil cp models/yolo_v8.onnx gs://<model_bucket_name>/models/yolo_v8.onnx
gsutil cp models/yolo_v11_top5.onnx gs://<model_bucket_name>/models/yolo_v11_top5.onnx
gsutil cp models/fast_rcnn.onnx gs://<model_bucket_name>/models/fast_rcnn.onnx
```

Build and push the API image:

```bash
gcloud auth configure-docker <region>-docker.pkg.dev
docker build -t <region>-docker.pkg.dev/<project_id>/taco-trash/taco-trash-api:<tag> .
docker push <region>-docker.pkg.dev/<project_id>/taco-trash/taco-trash-api:<tag>
```

Use Terraform outputs in Helm values:

```yaml
serviceAccount:
  name: taco-trash-api
  annotations:
    iam.gke.io/gcp-service-account: <api_google_service_account_email>

env:
  STORAGE: gcp
  MASK_RCNN_V1_PATH: gs://<model_bucket_name>/models/mask_rcnn_v1.pt
  YOLO_V8_PATH: gs://<model_bucket_name>/models/yolo_v8.onnx
  YOLO_V11_TOP5_PATH: gs://<model_bucket_name>/models/yolo_v11_top5.onnx
  FAST_RCNN_PATH: gs://<model_bucket_name>/models/fast_rcnn.onnx
```

The API is deployed by Helm after Terraform finishes. GitHub Actions exposes it as a Kubernetes `LoadBalancer` service, waits for the assigned external IP, and passes that URL to the Cloud Run UI as `API_URL`.

The old App Engine URL is not used for the Streamlit UI. Use the Cloud Run service URL printed by the `Show UI URL` workflow step or by:

```bash
gcloud run services describe taco-trash-ui \
  --region <region> \
  --project <project_id> \
  --format='value(status.url)'
```

## GitHub Actions deployment

The `ci_identity` module creates a dedicated Google service account for GitHub Actions and grants it permissions to publish Docker images, deploy the API to GKE, and deploy the Streamlit UI to Cloud Run.

The workflow `.github/workflows/ci.yml` runs lint, type checks, tests, publishes the API image, and deploys the API/UI on every push to an allowed branch.

- `<region>-docker.pkg.dev/<project_id>/<repo>/taco-trash-api:<commit-sha>`;
- `<region>-docker.pkg.dev/<project_id>/<repo>/taco-trash-api:latest`.

Terraform can create these GitHub repository variables automatically through the `github_repository_config` module:

| GitHub variable | Value |
|:--|:--|
| `GCP_PROJECT_ID` | `project_id` |
| `GCP_REGION` | `region` |
| `ARTIFACT_REGISTRY_REPOSITORY` | `artifact_registry_repository` output |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `github_actions_workload_identity_provider` output |
| `GCP_SERVICE_ACCOUNT` | `github_actions_service_account_email` output |

To allow Terraform to update repository variables, export a GitHub token before running Terraform:

```bash
export GITHUB_TOKEN=<token-with-repository-actions-variable-permissions>
```

Set this flag to disable GitHub repository variable management:

```hcl
configure_github_actions_variables = false
```

The Workload Identity Provider is restricted to the configured repository and branch:

```hcl
github_repository    = "vsokoltsov/taco-trash-detection"
github_deploy_branches = ["main", "master"]
```
