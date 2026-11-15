variable "subscription_id" {
  type = string
}

variable "prefix" {
  description = "Lowercase letters/digits only, used in resource names."
  type        = string
  default     = "aiacademy"
}

variable "location" {
  type    = string
  default = "eastus"
}

variable "vm_size" {
  type    = string
  default = "Standard_B2s"
}
