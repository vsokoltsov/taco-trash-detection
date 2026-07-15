# taco-trash-api Helm chart

This chart deploys only the FastAPI inference service. The Streamlit UI is intended to run on Cloud Run.

By default, the API is exposed through a Kubernetes `LoadBalancer` service. The GitHub Actions deployment waits for the assigned external IP and passes `http://<api-load-balancer-ip>` to the Cloud Run UI as `API_URL`.

Example values for GCS-hosted models:

```yaml
image:
  repository: europe-west1-docker.pkg.dev/my-project/taco-trash/taco-trash-api
  tag: latest

serviceAccount:
  annotations:
    iam.gke.io/gcp-service-account: taco-trash-api@my-project.iam.gserviceaccount.com

env:
  STORAGE: gcp
  USE_GPU: "false"
  MASK_RCNN_V1_PATH: gs://my-project-taco-models/models/mask_rcnn_v1.onnx
  YOLO_V8_PATH: gs://my-project-taco-models/models/yolo_v8.onnx
  YOLO_V11_TOP5_PATH: gs://my-project-taco-models/models/yolo_v11_top5.onnx
  FAST_RCNN_PATH: gs://my-project-taco-models/models/fast_rcnn.onnx
```
