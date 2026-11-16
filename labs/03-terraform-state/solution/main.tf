terraform {
  required_version = ">= 1.6"
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

variable "environment" {
  description = "Environment name used in file contents."
  type        = string
  default     = "dev"
}

resource "random_pet" "name" {
  length = 2
}

resource "local_file" "config" {
  filename = "${path.module}/out/${random_pet.name.id}.txt"
  content  = "env=${var.environment}\nname=${random_pet.name.id}\n"
}

output "file_path" {
  description = "Where the generated file lives."
  value       = local_file.config.filename
}
