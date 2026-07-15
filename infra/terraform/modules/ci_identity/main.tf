locals {
  pool_id            = substr(replace("${var.name_prefix}-github", "-", ""), 0, 32)
  provider_id        = "github"
  service_account_id = substr(replace("${var.name_prefix}-github-actions", "-", ""), 0, 30)
  allowed_refs       = [for branch in var.github_branches : "refs/heads/${branch}"]
}

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = local.pool_id
  display_name              = "GitHub Actions"
  description               = "OIDC pool for GitHub Actions image publishing."
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = local.provider_id
  display_name                       = "GitHub"
  description                        = "GitHub Actions OIDC provider."

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }

  attribute_condition = "assertion.repository == '${var.github_repository}' && assertion.ref in ${jsonencode(local.allowed_refs)}"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account" "github_actions" {
  account_id   = local.service_account_id
  display_name = "TACO Trash GitHub Actions publisher"
}

resource "google_service_account_iam_member" "github_actions_oidc" {
  service_account_id = google_service_account.github_actions.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repository}"
}

resource "google_artifact_registry_repository_iam_member" "github_actions_writer" {
  project    = var.project_id
  location   = var.repository_region
  repository = var.repository_name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "github_actions_deploy_roles" {
  for_each = toset([
    "roles/container.admin",
    "roles/iam.serviceAccountUser",
    "roles/run.admin",
    "roles/storage.admin",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}
