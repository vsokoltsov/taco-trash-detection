output "artifact_registry_repository" {
  description = "Artifact Registry Docker repository name."
  value       = module.artifact_registry.repository_name
}

output "artifact_registry_repository_url" {
  description = "Artifact Registry Docker repository URL prefix."
  value       = module.artifact_registry.repository_url
}

output "model_bucket_name" {
  description = "Cloud Storage bucket for ONNX models."
  value       = module.model_bucket.bucket_name
}

output "gke_cluster_name" {
  description = "GKE cluster name."
  value       = module.gke.cluster_name
}

output "gke_location" {
  description = "GKE cluster location."
  value       = module.gke.location
}

output "api_google_service_account_email" {
  description = "Google service account to annotate on the Helm Kubernetes service account."
  value       = module.runtime_identity.api_service_account_email
}

output "helm_service_account_annotation" {
  description = "Workload Identity annotation for Helm values."
  value       = "iam.gke.io/gcp-service-account: ${module.runtime_identity.api_service_account_email}"
}

output "github_actions_service_account_email" {
  description = "Service account used by GitHub Actions to publish Docker images."
  value       = module.ci_identity.service_account_email
}

output "github_actions_workload_identity_provider" {
  description = "Workload Identity Provider resource name for google-github-actions/auth."
  value       = module.ci_identity.workload_identity_provider_name
}

output "github_actions_variable_names" {
  description = "GitHub Actions variables managed by Terraform."
  value       = var.configure_github_actions_variables ? module.github_repository_config[0].actions_variable_names : []
}
