#!/usr/bin/env bash
set -euo pipefail
RG=rg-lab07

az group create --name "$RG" --location eastus

# Always preview first.
az deployment group what-if --resource-group "$RG" --template-file template.json --parameters @parameters.json

az deployment group create --resource-group "$RG" --template-file template.json --parameters @parameters.json
