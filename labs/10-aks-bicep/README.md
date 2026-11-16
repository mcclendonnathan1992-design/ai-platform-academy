# Lab 10 · The same AKS + ACR in Bicep

**Why it matters:** you will meet both languages. Writing the same design twice is the fastest way to learn how they map.

## Task
In `work/main.bicep` build the **same** architecture as Lab 09:
- Log Analytics workspace (`Microsoft.OperationalInsights/workspaces`)
- Container registry (`Microsoft.ContainerRegistry/registries`) with `adminUserEnabled: false`
- AKS (`Microsoft.ContainerService/managedClusters`) with a **SystemAssigned** identity, `disableLocalAccounts: true`, `aadProfile` (**managed**, **enableAzureRBAC**, admin group IDs from a param), `apiServerAccessProfile.enablePrivateCluster: true`, overlay networking with a network policy, an agent pool, and the `omsagent` addon wired to the workspace
- A **role assignment** (`Microsoft.Authorization/roleAssignments`) giving the **kubelet identity** the `AcrPull` role (`7f951dda-4ed3-4680-a7ca-43fe172d538d`) on the registry
  - its `name` must be built with `guid(...)`
  - `scope:` is the registry resource (this is a Bicep extension-resource pattern)

## Check
```
make lab-check LAB=10
az bicep build --file labs/10-aks-bicep/work/main.bicep
```

## Compare with Lab 09
Make a two-column table: Terraform attribute → Bicep property for each hardening setting. Keep it in your notes. The names differ more than the ideas do.

## Stretch
Add `az deployment group what-if` output for a fake subscription to your notes and explain each line.
