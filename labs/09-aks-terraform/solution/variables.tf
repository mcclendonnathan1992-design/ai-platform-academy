variable "subscription_id" {
  description = "Azure subscription ID."
  type        = string
}

variable "prefix" {
  description = "Lowercase letters and digits used in names."
  type        = string
  default     = "lab09"
}

variable "location" {
  description = "Azure region."
  type        = string
  default     = "eastus"
}

variable "vm_size" {
  description = "System node pool VM size."
  type        = string
  default     = "Standard_B2s"
}

variable "admin_group_object_ids" {
  description = "Entra ID group object IDs that get cluster admin."
  type        = list(string)
}
