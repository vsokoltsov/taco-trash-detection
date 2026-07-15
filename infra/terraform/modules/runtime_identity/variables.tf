variable "project_id" {
  description = "GCP project id."
  type        = string
}

variable "name_prefix" {
  description = "Resource name prefix."
  type        = string
}

variable "model_bucket_name" {
  description = "Model bucket name."
  type        = string
}

variable "kubernetes_namespace" {
  description = "Kubernetes namespace for the API service account."
  type        = string
}

variable "kubernetes_service_account" {
  description = "Kubernetes service account name for API pods."
  type        = string
}
