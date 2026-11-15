output "acr_login_server" {
  value = azurerm_container_registry.this.login_server
}

output "aks_name" {
  value = azurerm_kubernetes_cluster.this.name
}
