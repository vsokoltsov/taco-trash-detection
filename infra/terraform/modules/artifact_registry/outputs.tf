output "repository_name" {
  description = "Artifact Registry repository id."
  value       = google_artifact_registry_repository.docker.repository_id
}

output "repository_url" {
  description = "Docker repository URL prefix."
  value       = "${google_artifact_registry_repository.docker.location}-docker.pkg.dev/${google_artifact_registry_repository.docker.project}/${google_artifact_registry_repository.docker.repository_id}"
}
