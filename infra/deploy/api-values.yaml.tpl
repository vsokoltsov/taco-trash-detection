image:
  repository: "${IMAGE_REPOSITORY}"
  tag: "${IMAGE_TAG}"

serviceAccount:
  create: true
  name: "taco-trash-api"
  annotations:
    iam.gke.io/gcp-service-account: "${API_GOOGLE_SERVICE_ACCOUNT}"

service:
  type: LoadBalancer

ingress:
  enabled: false

env:
  STORAGE: "gcp"
  USE_GPU: "false"
  MASK_RCNN_V1_PATH: "gs://${MODEL_BUCKET_NAME}/models/mask_rcnn_v1.pt"
  YOLO_V8_PATH: "gs://${MODEL_BUCKET_NAME}/models/yolo_v8.onnx"
  YOLO_V11_TOP5_PATH: "gs://${MODEL_BUCKET_NAME}/models/yolo_v11_top5.onnx"
  FAST_RCNN_PATH: "gs://${MODEL_BUCKET_NAME}/models/fast_rcnn.onnx"
