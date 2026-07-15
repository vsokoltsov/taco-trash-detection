variable "project_id" {
  description = "GCP project id."
  type        = string
}

variable "location_id" {
  description = "App Engine location id."
  type        = string
}

variable "create" {
  description = "Whether to create the App Engine application."
  type        = bool
}
