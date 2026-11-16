# Partial configuration: the storage account details are passed at init time, never committed:
#   terraform init -backend-config="resource_group_name=..." -backend-config="storage_account_name=..." \
#     -backend-config="container_name=tfstate" -backend-config="key=lab05.tfstate"
terraform {
  backend "azurerm" {}
}
