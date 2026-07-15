output "network_id" {
  description = "VPC id."
  value       = google_compute_network.main.id
}

output "network_name" {
  description = "VPC name."
  value       = google_compute_network.main.name
}

output "subnetwork_id" {
  description = "Subnetwork id."
  value       = google_compute_subnetwork.main.id
}

output "subnetwork_name" {
  description = "Subnetwork name."
  value       = google_compute_subnetwork.main.name
}
