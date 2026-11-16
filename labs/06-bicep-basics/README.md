# Lab 06 · Bicep from scratch: parameters, variables, resources, outputs

**Why it matters:** Bicep is Azure's native IaC language and compiles to the same ARM JSON your portal deployments use. Reading and writing it is core to enclave work.

## Task
In `work/` write `main.bicep` and `main.bicepparam`.

`main.bicep` must have:
- `targetScope = 'resourceGroup'`
- `param location string = resourceGroup().location`
- `param namePrefix string` with `@minLength` and `@maxLength`
- `param skuName string` with `@allowed([...])` and a default
- a `var` that builds a globally unique storage account name with `uniqueString(resourceGroup().id)` and fits the 3–24 character rule
- a **storage account** (`Microsoft.Storage/storageAccounts`) with **TLS 1.2 minimum, blob public access off, HTTPS only**
- outputs for the storage account `id` and `name`
- `@description(...)` decorators on every param

`main.bicepparam` starts with `using './main.bicep'` and sets the params.

## Check
```
make lab-check LAB=06
az bicep build --file labs/06-bicep-basics/work/main.bicep     # compiles to ARM JSON
```
Open the JSON it prints. That is what Azure actually receives.

## Run it for real (optional, storage costs pennies)
```
az group create -n rg-lab06 -l eastus
az deployment group what-if -g rg-lab06 -p main.bicepparam
az deployment group create  -g rg-lab06 -p main.bicepparam
az group delete -n rg-lab06 --yes
```

## Think about
- What does `what-if` show that `create` doesn't?
- Why `uniqueString(resourceGroup().id)` and not a random value?
- Bicep is declarative and idempotent: what happens if you run `create` twice?

## Stretch
Add a blob container resource as a `parent:` child of the storage account.
