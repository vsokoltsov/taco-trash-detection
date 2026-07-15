variable "project_id" {
  description = "GCP project id."
  type        = string
}

variable "name_prefix" {
  description = "Resource name prefix."
  type        = string
}

variable "region" {
  description = "GKE region."
  type        = string
}

variable "network_id" {
  description = "VPC id."
  type        = string
}

variable "subnetwork_id" {
  description = "Subnetwork id."
  type        = string
}

variable "machine_type" {
  description = "Node machine type."
  type        = string
}

variable "min_node_count" {
  description = "Minimum node count."
  type        = number
}

variable "max_node_count" {
  description = "Maximum node count."
  type        = number
}

variable "service_account" {
  description = "Node service account email."
  type        = string
}
