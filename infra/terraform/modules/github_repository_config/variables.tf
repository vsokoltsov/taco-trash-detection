variable "repository_name" {
  description = "GitHub repository name without owner."
  type        = string
}

variable "actions_variables" {
  description = "GitHub Actions repository variables to create or update."
  type        = map(string)
}
