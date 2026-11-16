# Lab 09 · AKS + ACR in Terraform, hardened for an enclave

**Why it matters:** this is your job in one file set: a private, Entra-integrated AKS cluster that can pull images from a registry with no passwords anywhere.

## Task
In `work/` write `versions.tf`, `variables.tf`, `main.tf`, `outputs.tf` that create:
1. a **resource group** and a **Log Analytics workspace**
2. a **container registry** with `admin_enabled = false` (no shared admin password)
3. an **AKS cluster** with:
   - `private_cluster_enabled = true` and `local_account_disabled = true`
   - a **system-assigned identity**
   - **Entra ID RBAC**: an `azure_active_directory_role_based_access_control` block with `azure_rbac_enabled = true` and `admin_group_object_ids` from a variable
   - `network_plugin = "azure"`, `network_plugin_mode = "overlay"`, and a network policy
   - an `oms_agent` block sending logs to the workspace
4. an **`AcrPull` role assignment** from the cluster's **kubelet identity** to the registry
5. outputs for the registry login server and cluster name; no GUIDs hardcoded anywhere

## Check
```
make lab-check LAB=09
cd labs/09-aks-terraform/work && terraform init -backend=false && terraform validate
```

## Do NOT apply this casually
AKS and a Log Analytics workspace cost money, and a **private** cluster is unreachable from outside its network. Validate and read the plan; only apply in a subscription with a budget alert, and destroy the same day. See `labs/README.md`.

## Think about
- Why a **kubelet** identity for AcrPull and not the cluster identity?
- What does `local_account_disabled` stop, and what do you use instead to get `kubectl` access?
- What breaks if you forget `skip_service_principal_aad_check`?
- Which of these settings would your security team ask about first?

## Stretch
Add a user node pool in a separate `azurerm_kubernetes_cluster_node_pool` and move the system pool to `only_critical_addons_enabled`.
