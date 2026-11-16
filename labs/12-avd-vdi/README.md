# Lab 12 · Azure Virtual Desktop (VDI) in Terraform

**Why it matters:** AVD is the VDI you deploy and support. You need to know its five moving parts and how a user ends up with a desktop.

## The model
`Host pool` (the pool of session-host VMs and its rules) → `Application group` (what users get: a full **Desktop** or RemoteApps) → `Workspace` (what users see in the client) ← **association**. Users get access through a **role assignment** on the application group.

## Task
In `work/main.tf` write:
1. `azurerm` provider (`~> 4.0`) and variables: `subscription_id`, `location`, `users_group_object_id`
2. a resource group
3. **host pool**: `Pooled`, `BreadthFirst`, a `maximum_sessions_allowed`, `start_vm_on_connect`, and `custom_rdp_properties` that include **`enablerdsaadauth:i:1`** (Entra ID sign-in)
4. **registration info** with an expiration date (session hosts use this token to join)
5. **application group** of type `Desktop` tied to the host pool
6. **workspace**, and the **workspace ↔ application group association**
7. a **role assignment**: `Desktop Virtualization User` on the application group for the Entra group

## Check
```
make lab-check LAB=12
```

## Think about
- What would you check first if a user sees the workspace but no desktop? (Role assignment, then session-host health.)
- Why does the registration token expire?
- Pooled vs Personal host pools: when would you pick each?
- What is *not* in this lab that a working AVD needs? (Session-host VMs, domain/Entra join, the agent. See stretch.)

## Stretch
Add session hosts: `azurerm_windows_virtual_machine`, the `AADLoginForWindows` extension, and the DSC extension that installs the AVD agent with the registration token.
