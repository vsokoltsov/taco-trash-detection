resource "google_app_engine_application" "main" {
  count = var.create ? 1 : 0

  project     = var.project_id
  location_id = var.location_id
}
