output "actions_variable_names" {
  description = "Created GitHub Actions repository variable names."
  value       = keys(github_actions_variable.variables)
}
