variable "subscription_id" {
  description = "Azure subscription ID to deploy into."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
  default     = "eastus"
}

variable "environment" {
  description = "dev, test or prod."
  type        = string
  default     = "dev"
}

variable "subnets" {
  description = "Subnet name to CIDR."
  type        = map(string)
  default = {
    workload = "10.10.1.0/24"
    mgmt     = "10.10.2.0/24"
  }
}
