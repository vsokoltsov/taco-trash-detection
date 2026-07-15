resource "google_storage_bucket" "models" {
  name                        = var.bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age                = 30
      num_newer_versions = 3
      with_state         = "ARCHIVED"
    }

    action {
      type = "Delete"
    }
  }
}
