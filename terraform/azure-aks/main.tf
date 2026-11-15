# OPTIONAL and COSTS MONEY if applied. Default workflow: terraform plan only, then destroy.
terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

resource "random_string" "suffix" {
  length  = 5
  special = false
  upper   = false
}

resource "azurerm_resource_group" "this" {
  name     = "rg-${var.prefix}"
  location = var.location
}

resource "azurerm_container_registry" "this" {
  name                = "acr${var.prefix}${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  sku                 = "Basic"
}

resource "azurerm_log_analytics_workspace" "this" {
  name                = "log-${var.prefix}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_kubernetes_cluster" "this" {
  name                = "aks-${var.prefix}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  dns_prefix          = var.prefix

  default_node_pool {
    name       = "system"
    node_count = 1
    vm_size    = var.vm_size
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin      = "azure"
    network_plugin_mode = "overlay"
  }

  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id
  }
}

resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.this.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.this.kubelet_identity[0].object_id
}
