variable "project_id" {
  description = "GCP project id."
  type        = string
}

variable "name_prefix" {
  description = "Resource name prefix."
  type        = string
}

variable "github_repository" {
  description = "GitHub repository allowed to impersonate the service account, for example owner/repository."
  type        = string
}

variable "github_branches" {
  description = "GitHub branches allowed to impersonate the service account."
  type        = list(string)
}

variable "repository_name" {
  description = "Artifact Registry repository id."
  type        = string
}

variable "repository_region" {
  description = "Artifact Registry repository location."
  type        = string
}
