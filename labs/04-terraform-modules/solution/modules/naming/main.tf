variable "workload" {
  description = "Short workload name."
  type        = string
}

variable "environment" {
  description = "dev, test or prod."
  type        = string

  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "environment must be dev, test or prod."
  }
}

locals {
  prefix = "${var.workload}-${var.environment}"
}

output "prefix" {
  description = "Naming prefix."
  value       = local.prefix
}
