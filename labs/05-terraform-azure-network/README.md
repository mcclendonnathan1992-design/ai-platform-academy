# Lab 05 · Terraform on Azure: resource group, VNet, subnets, NSG

**Why it matters:** this is the skeleton of every enclave: a network with deny-by-default rules, built the same way every time.

## Task
In `work/`, split into files like a real repo:
- `versions.tf`: Terraform + **azurerm `~> 4.0`**, `provider "azurerm"` with `features {}` and `subscription_id = var.subscription_id` (v4 requires it)
- `backend.tf`: `backend "azurerm" {}` with **no values** (partial config: account details go in at `terraform init -backend-config=...`, never in Git)
- `variables.tf`: `subscription_id`, `location` (default), `environment`, and `subnets` (a `map(string)`), all with descriptions
- `main.tf`: a `locals` block with `tags`; **resource group**, **virtual network**, **subnets via `for_each`**, a **network security group** with an allow-HTTPS rule and a **deny-all inbound at priority 4096**, and a **subnet↔NSG association** (for_each)
- `outputs.tf`: the VNet ID
- `.gitignore` for state and tfvars

## Check (no Azure login needed)
```
make lab-check LAB=05
cd labs/05-terraform-azure-network/work && terraform init -backend=false && terraform validate
```

## Run it for real (optional, free resources, but still destroy afterwards)
```
az login --use-device-code
az account show --query id -o tsv      # use this for subscription_id
terraform init -backend=false
terraform plan -var subscription_id=<id>
terraform apply -var subscription_id=<id>
terraform destroy -var subscription_id=<id>
```
VNets and NSGs are free. See `labs/README.md` for cost rules.

## Think about
- Why is the NSG deny rule at 4096?
- What does `for_each` give you over `count` when a subnet is removed from the map?
- Where would the state live in production, and who needs access to it?

## Stretch
Add a second environment with `-var-file`, then turn the network into a module (Lab 04 pattern).
