variable "workloads" {
  type = map(string)
  default = {
    web = "eastus2"
    api = "eastus2"
    db  = "centralus"
  }
}

locals {
  tags = {
    managed_by = "terraform"
  }
}

resource "azurerm_resource_group" "this" {
  for_each = var.workloads
  name     = "rg-lab-${each.key}"
  location = each.value
  tags     = local.tags
}

output "resource_group_ids" {
  value = { for k, rg in azurerm_resource_group.this : k => rg.id }
}
