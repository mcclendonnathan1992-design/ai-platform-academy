terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  subscription_id = "11111111-2222-3333-4444-555555555555"
}

resource "azurerm_resource_group" "this" {
  name     = "rg-drill"
  location = var.location
}

resource "azurerm_storage_account" "this" {
  name                     = "stdrill${var.suffix}"
  resource_group_name      = azurerm_resource_group.this.name
  location                 = azurerm_resource_group.this.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}
