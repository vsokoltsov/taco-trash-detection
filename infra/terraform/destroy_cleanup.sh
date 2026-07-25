#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-taco-trash-detection}"
REGION="${REGION:-europe-west1}"
GKE_CLUSTER_NAME="${GKE_CLUSTER_NAME:-taco-trash-prod-gke}"
GKE_LOCATION="${GKE_LOCATION:-europe-west1}"
GKE_NAMESPACE="${GKE_NAMESPACE:-taco-trash}"
HELM_RELEASE_NAME="${HELM_RELEASE_NAME:-taco-trash-api}"
CLOUD_RUN_UI_SERVICE_NAME="${CLOUD_RUN_UI_SERVICE_NAME:-taco-trash-ui}"

echo "Cleaning resources created outside Terraform."
echo "Project: ${PROJECT_ID}"

if rtk gcloud run services describe "${CLOUD_RUN_UI_SERVICE_NAME}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" >/dev/null 2>&1; then
  echo "Deleting Cloud Run service: ${CLOUD_RUN_UI_SERVICE_NAME}"
  rtk gcloud run services delete "${CLOUD_RUN_UI_SERVICE_NAME}" \
    --region "${REGION}" \
    --project "${PROJECT_ID}" \
    --quiet
else
  echo "Cloud Run service not found: ${CLOUD_RUN_UI_SERVICE_NAME}"
fi

if rtk gcloud container clusters describe "${GKE_CLUSTER_NAME}" \
  --location "${GKE_LOCATION}" \
  --project "${PROJECT_ID}" >/dev/null 2>&1; then
  echo "Fetching GKE credentials for cluster: ${GKE_CLUSTER_NAME}"
  rtk gcloud container clusters get-credentials "${GKE_CLUSTER_NAME}" \
    --location "${GKE_LOCATION}" \
    --project "${PROJECT_ID}"

  if rtk helm status "${HELM_RELEASE_NAME}" --namespace "${GKE_NAMESPACE}" >/dev/null 2>&1; then
    echo "Uninstalling Helm release: ${HELM_RELEASE_NAME}"
    rtk helm uninstall "${HELM_RELEASE_NAME}" --namespace "${GKE_NAMESPACE}"
  else
    echo "Helm release not found: ${HELM_RELEASE_NAME}"
  fi

  echo "Waiting for API LoadBalancer service to disappear."
  rtk kubectl wait \
    --for=delete service/"${HELM_RELEASE_NAME}" \
    --namespace "${GKE_NAMESPACE}" \
    --timeout=10m || true

  echo "Deleting namespace if it is empty or only contains project resources: ${GKE_NAMESPACE}"
  rtk kubectl delete namespace "${GKE_NAMESPACE}" --ignore-not-found=true --wait=true --timeout=10m || true
else
  echo "GKE cluster not found: ${GKE_CLUSTER_NAME}"
fi

APP_ENGINE_STATE_ADDRESS='module.app_engine.google_app_engine_application.main[0]'
TERRAFORM_STATE_LIST="$(rtk terraform state list || true)"

if [[ "${TERRAFORM_STATE_LIST}" == *"${APP_ENGINE_STATE_ADDRESS}"* ]]; then
  echo "Removing undeletable App Engine application from Terraform state: ${APP_ENGINE_STATE_ADDRESS}"
  rtk terraform state rm "${APP_ENGINE_STATE_ADDRESS}"
else
  echo "App Engine application is not present in Terraform state."
fi

echo "Cleanup complete. You can now run Terraform destroy."
