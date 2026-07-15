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

output "api_ingress_ip_name" {
  description = "Reserved global static IP name for the API ingress."
  value       = google_compute_global_address.api_ingress.name
}

output "api_ingress_ip_address" {
  description = "Reserved global static IP address for the API ingress."
  value       = google_compute_global_address.api_ingress.address
}

output "subnetwork_name" {
  description = "Subnetwork name."
  value       = google_compute_subnetwork.main.name
}
