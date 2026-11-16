terraform {
  required_version = ">= 1.6"
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

variable "environments" {
  description = "Environments to create."
  type        = set(string)
}

variable "workload" {
  description = "Workload name."
  type        = string
  default     = "enclave"
}

module "naming" {
  source      = "./modules/naming"
  for_each    = var.environments
  workload    = var.workload
  environment = each.key
}

locals {
  tags = {
    owner   = "platform"
    workload = var.workload
  }
}

resource "local_file" "inventory" {
  for_each = module.naming
  filename = "${path.module}/out/${each.value.prefix}.json"
  content  = jsonencode({ name = each.value.prefix, tags = local.tags })
}

output "prefixes" {
  description = "Prefix per environment."
  value       = { for k, m in module.naming : k => m.prefix }
}
