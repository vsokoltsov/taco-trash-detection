output "app_engine_location_id" {
  description = "App Engine location id."
  value       = var.create ? google_app_engine_application.main[0].location_id : null
}
