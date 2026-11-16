variable "location" {
  type    = string
  default = "eastus2"
}

variable "environment" {
  type    = string
  default = "dev"
}

locals {
  tags = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "azurerm_resource_group" "this" {
  name     = "rg-lab-${var.environment}"
  location = var.location
  tags     = local.tags
}

resource "azurerm_storage_account" "this" {
  name                            = "stlab${var.environment}001"
  resource_group_name             = azurerm_resource_group.this.name
  location                        = azurerm_resource_group.this.location
  account_tier                    = "Standard"
  account_replication_type        = "GRS"
  https_traffic_only_enabled      = true
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  tags                            = local.tags
}

output "storage_account_id" {
  value = azurerm_storage_account.this.id
}
