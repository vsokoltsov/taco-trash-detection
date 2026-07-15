resource "github_actions_variable" "variables" {
  for_each = var.actions_variables

  repository    = var.repository_name
  variable_name = each.key
  value         = each.value
}
