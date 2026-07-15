output "cluster_name" {
  description = "GKE cluster name."
  value       = google_container_cluster.main.name
}

output "location" {
  description = "GKE cluster location."
  value       = google_container_cluster.main.location
}

output "endpoint" {
  description = "GKE cluster endpoint."
  value       = google_container_cluster.main.endpoint
  sensitive   = true
}
