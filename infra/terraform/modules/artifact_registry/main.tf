resource "google_artifact_registry_repository" "docker" {
  location      = var.region
  repository_id = var.name_prefix
  description   = "Docker images for TACO trash detection services."
  format        = "DOCKER"
}
