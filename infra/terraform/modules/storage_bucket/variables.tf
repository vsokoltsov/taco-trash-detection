variable "bucket_name" {
  description = "Cloud Storage bucket name."
  type        = string
}

variable "region" {
  description = "Cloud Storage location."
  type        = string
}

variable "force_destroy" {
  description = "Whether Terraform may delete the bucket even when it contains model objects."
  type        = bool
  default     = false
}
