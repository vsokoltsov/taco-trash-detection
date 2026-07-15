output "gke_node_service_account_email" {
  description = "GKE node service account email."
  value       = google_service_account.gke_nodes.email
}

output "api_service_account_email" {
  description = "API runtime Google service account email."
  value       = google_service_account.api.email
}

output "api_service_account_name" {
  description = "API runtime Google service account resource name."
  value       = google_service_account.api.name
}
