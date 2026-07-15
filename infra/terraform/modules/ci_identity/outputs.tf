output "service_account_email" {
  description = "GitHub Actions publisher service account email."
  value       = google_service_account.github_actions.email
}

output "workload_identity_provider_name" {
  description = "Full Workload Identity Provider resource name for google-github-actions/auth."
  value       = google_iam_workload_identity_pool_provider.github.name
}
