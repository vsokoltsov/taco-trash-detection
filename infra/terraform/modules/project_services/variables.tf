variable "project_id" {
  description = "GCP project id."
  type        = string
}

variable "services" {
  description = "Google APIs to enable."
  type        = set(string)
  default = [
    "appengine.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "compute.googleapis.com",
    "container.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "storage.googleapis.com",
  ]
}
