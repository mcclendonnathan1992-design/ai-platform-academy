output "acr_login_server" {
  description = "Registry login server."
  value       = azurerm_container_registry.this.login_server
}

output "aks_name" {
  description = "Cluster name."
  value       = azurerm_kubernetes_cluster.this.name
}
