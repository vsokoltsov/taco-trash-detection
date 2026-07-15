resource "google_container_cluster" "main" {
  name     = "${var.name_prefix}-gke"
  location = var.region

  network    = var.network_id
  subnetwork = var.subnetwork_id

  remove_default_node_pool = true
  initial_node_count       = 1

  deletion_protection = false

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }
}

resource "google_container_node_pool" "main" {
  name       = "${var.name_prefix}-default"
  location   = var.region
  cluster    = google_container_cluster.main.name
  node_count = var.min_node_count

  autoscaling {
    min_node_count = var.min_node_count
    max_node_count = var.max_node_count
  }

  node_config {
    machine_type    = var.machine_type
    service_account = var.service_account

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]

    labels = {
      workload = "api"
    }
  }
}
