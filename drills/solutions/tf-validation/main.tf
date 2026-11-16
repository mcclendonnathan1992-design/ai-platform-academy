variable "environment" {
  type = string

  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "environment must be dev, test or prod."
  }
}

variable "admin_password" {
  type      = string
  sensitive = true
}

output "environment" {
  value = var.environment
}
