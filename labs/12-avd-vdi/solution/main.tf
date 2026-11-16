terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

variable "subscription_id" {
  description = "Azure subscription ID."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
  default     = "eastus"
}

variable "users_group_object_id" {
  description = "Entra ID group whose members may sign in to the desktop."
  type        = string
}

resource "azurerm_resource_group" "this" {
  name     = "rg-avd-lab"
  location = var.location
}

resource "azurerm_virtual_desktop_host_pool" "this" {
  name                     = "hp-lab"
  location                 = azurerm_resource_group.this.location
  resource_group_name      = azurerm_resource_group.this.name
  type                     = "Pooled"
  load_balancer_type       = "BreadthFirst"
  maximum_sessions_allowed = 10
  start_vm_on_connect      = true
  custom_rdp_properties    = "targetisaadjoined:i:1;enablerdsaadauth:i:1;"
}

resource "azurerm_virtual_desktop_host_pool_registration_info" "this" {
  hostpool_id     = azurerm_virtual_desktop_host_pool.this.id
  expiration_date = timeadd(plantimestamp(), "48h")
}

resource "azurerm_virtual_desktop_application_group" "desktop" {
  name                = "dag-lab"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  type                = "Desktop"
  host_pool_id        = azurerm_virtual_desktop_host_pool.this.id
}

resource "azurerm_virtual_desktop_workspace" "this" {
  name                = "ws-lab"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
}

resource "azurerm_virtual_desktop_workspace_application_group_association" "this" {
  workspace_id         = azurerm_virtual_desktop_workspace.this.id
  application_group_id = azurerm_virtual_desktop_application_group.desktop.id
}

resource "azurerm_role_assignment" "desktop_users" {
  scope                = azurerm_virtual_desktop_application_group.desktop.id
  role_definition_name = "Desktop Virtualization User"
  principal_id         = var.users_group_object_id
}
