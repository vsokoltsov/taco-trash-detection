variable "project_id" {
  description = "GCP project id."
  type        = string
}

variable "region" {
  description = "Default GCP region."
  type        = string
  default     = "europe-west1"
}

variable "zone" {
  description = "Default GCP zone."
  type        = string
  default     = "europe-west1-b"
}

variable "environment" {
  description = "Environment name used in resource names."
  type        = string
  default     = "prod"
}

variable "name_prefix" {
  description = "Prefix used for all resources."
  type        = string
  default     = "taco-trash"
}

variable "gke_namespace" {
  description = "Kubernetes namespace used by the API Helm release."
  type        = string
  default     = "taco-trash"
}

variable "gke_service_account_name" {
  description = "Kubernetes service account used by the API pods."
  type        = string
  default     = "taco-trash-api"
}

variable "gke_node_machine_type" {
  description = "GKE node machine type."
  type        = string
  default     = "e2-standard-4"
}

variable "gke_min_node_count" {
  description = "Minimum number of GKE nodes."
  type        = number
  default     = 1
}

variable "gke_max_node_count" {
  description = "Maximum number of GKE nodes."
  type        = number
  default     = 3
}

variable "model_bucket_name" {
  description = "Optional explicit model bucket name. If empty, a project-based name is used."
  type        = string
  default     = ""
}

variable "app_engine_location_id" {
  description = "App Engine location id. App Engine apps cannot be moved after creation."
  type        = string
  default     = "europe-west"
}

variable "create_app_engine_application" {
  description = "Whether Terraform should create the App Engine application."
  type        = bool
  default     = true
}

variable "github_repository" {
  description = "GitHub repository allowed to publish images through Workload Identity, for example owner/repository."
  type        = string
  default     = "vsokoltsov/taco-trash-detection"
}

variable "github_deploy_branches" {
  description = "GitHub branches allowed to publish images."
  type        = list(string)
  default     = ["main", "master"]
}

variable "configure_github_actions_variables" {
  description = "Whether Terraform should create GitHub Actions repository variables for image publishing."
  type        = bool
  default     = true
}

variable "api_url" {
  description = "Public API URL used by the Streamlit UI. If empty, Terraform uses the reserved API ingress IP."
  type        = string
  default     = ""
}

variable "cloud_run_ui_service_name" {
  description = "Cloud Run service name for the Streamlit UI."
  type        = string
  default     = "taco-trash-ui"
}
