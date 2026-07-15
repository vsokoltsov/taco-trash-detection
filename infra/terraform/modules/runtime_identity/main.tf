resource "google_service_account" "gke_nodes" {
  account_id   = substr(replace("${var.name_prefix}-gke-nodes", "-", ""), 0, 30)
  display_name = "TACO Trash GKE node service account"
}

resource "google_service_account" "api" {
  account_id   = substr(replace("${var.name_prefix}-api", "-", ""), 0, 30)
  display_name = "TACO Trash API runtime service account"
}

resource "google_project_iam_member" "gke_node_roles" {
  for_each = toset([
    "roles/artifactregistry.reader",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}

resource "google_storage_bucket_iam_member" "api_model_viewer" {
  bucket = var.model_bucket_name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.api.email}"
}
