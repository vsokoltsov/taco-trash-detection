# Terraform infrastructure

This directory provisions the GCP infrastructure needed by the project:

- required Google APIs;
- VPC and subnet for GKE;
- GKE cluster for the FastAPI inference API;
- Artifact Registry Docker repository;
- Cloud Storage bucket for ONNX model files;
- Google service accounts and Workload Identity binding for API pods;
- GitHub Actions Workload Identity for Docker image publishing;
- App Engine application initialization for the Streamlit UI.

Terraform intentionally does **not** deploy Helm releases and does **not** deploy the App Engine service.

Typical manual flow:

```bash
cd infra/terraform
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

The CI workflow uploads models from Google Drive to the bucket automatically. For a manual upload:

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

Terraform reserves a global static IP for the API ingress and exports `api_url`.
If `api_url` is empty in `terraform.tfvars`, GitHub Actions deploys the UI with `http://<reserved-api-ingress-ip>`.
For production, set `api_url` to a stable HTTPS domain and point that domain to `api_ingress_ip_address`.

## GitHub Actions deployment

The `ci_identity` module creates a dedicated Google service account for GitHub Actions and grants it permissions to publish the Docker image, upload model artifacts, deploy the API to GKE, and deploy the Streamlit UI to App Engine.

The workflow `.github/workflows/ci.yml` runs lint, type checks, tests, publishes the API image, syncs model artifacts, and deploys the API/UI on every push to an allowed branch.

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
