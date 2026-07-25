locals {
  resource_prefix   = "${var.name_prefix}-${var.environment}"
  model_bucket_name = var.model_bucket_name != "" ? var.model_bucket_name : "${var.project_id}-${var.name_prefix}-models"
  api_url           = var.api_url != "" ? var.api_url : "http://${module.network.api_ingress_ip_address}"
  github_repo_parts = split("/", var.github_repository)
  github_owner      = local.github_repo_parts[0]
  github_repo_name  = local.github_repo_parts[1]
}

module "project_services" {
  source = "./modules/project_services"

  project_id = var.project_id
}

module "network" {
  source = "./modules/network"

  name_prefix = local.resource_prefix
  region      = var.region

  depends_on = [module.project_services]
}

module "artifact_registry" {
  source = "./modules/artifact_registry"

  name_prefix = var.name_prefix
  region      = var.region

  depends_on = [module.project_services]
}

module "model_bucket" {
  source = "./modules/storage_bucket"

  bucket_name   = local.model_bucket_name
  region        = var.region
  force_destroy = var.model_bucket_force_destroy

  depends_on = [module.project_services]
}

module "gke" {
  source = "./modules/gke"

  project_id      = var.project_id
  name_prefix     = local.resource_prefix
  region          = var.region
  network_id      = module.network.network_id
  subnetwork_id   = module.network.subnetwork_id
  machine_type    = var.gke_node_machine_type
  min_node_count  = var.gke_min_node_count
  max_node_count  = var.gke_max_node_count
  service_account = module.runtime_identity.gke_node_service_account_email

  depends_on = [module.project_services]
}

module "runtime_identity" {
  source = "./modules/runtime_identity"

  project_id                 = var.project_id
  name_prefix                = local.resource_prefix
  model_bucket_name          = module.model_bucket.bucket_name
  kubernetes_namespace       = var.gke_namespace
  kubernetes_service_account = var.gke_service_account_name
}

resource "google_service_account_iam_member" "api_workload_identity" {
  service_account_id = module.runtime_identity.api_service_account_name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${var.gke_namespace}/${var.gke_service_account_name}]"

  depends_on = [module.gke]
}

module "ci_identity" {
  source = "./modules/ci_identity"

  project_id        = var.project_id
  name_prefix       = local.resource_prefix
  github_repository = var.github_repository
  github_branches   = var.github_deploy_branches
  repository_name   = module.artifact_registry.repository_name
  repository_region = var.region
}

module "github_repository_config" {
  count  = var.configure_github_actions_variables ? 1 : 0
  source = "./modules/github_repository_config"

  repository_name = local.github_repo_name
  actions_variables = {
    GCP_PROJECT_ID                 = var.project_id
    GCP_REGION                     = var.region
    ARTIFACT_REGISTRY_REPOSITORY   = module.artifact_registry.repository_name
    GCP_WORKLOAD_IDENTITY_PROVIDER = module.ci_identity.workload_identity_provider_name
    GCP_SERVICE_ACCOUNT            = module.ci_identity.service_account_email
    GKE_CLUSTER_NAME               = module.gke.cluster_name
    GKE_LOCATION                   = module.gke.location
    GKE_NAMESPACE                  = var.gke_namespace
    API_GOOGLE_SERVICE_ACCOUNT     = module.runtime_identity.api_service_account_email
    API_INGRESS_IP_NAME            = module.network.api_ingress_ip_name
    MODEL_BUCKET_NAME              = module.model_bucket.bucket_name
    API_URL                        = local.api_url
    CLOUD_RUN_UI_SERVICE_NAME      = var.cloud_run_ui_service_name
  }
}

module "app_engine" {
  source = "./modules/app_engine"

  project_id  = var.project_id
  location_id = var.app_engine_location_id
  create      = var.create_app_engine_application

  depends_on = [module.project_services]
}
