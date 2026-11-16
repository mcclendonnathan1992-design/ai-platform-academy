# Lab 14 · Capstone: a small enclave, in code

**Why it matters:** this is a portfolio piece and a rehearsal for your real deployment work. It mirrors the kind of design in your Jira/Confluence enclave: a locked-down network, a private AKS cluster, a registry, a vault, logging, and a virtual desktop for admins.

There is **no solution**. Design it, write it, defend it.

## Task
In `work/` create:
```
terraform/    azurerm: rg, vnet + subnets + NSG (deny-all inbound), Log Analytics, ACR, hardened AKS (Lab 09 settings), Key Vault, AVD host pool (Lab 12)
bicep/        main.bicep + modules/: at least the network and NSG (Lab 08 pattern)
docker/       Dockerfile for a small app (Lab 01 standards)
k8s/          manifests for that app (Lab 11 standards)
README.md     architecture diagram (ASCII or mermaid), what each piece does, a cost estimate, and how to tear it down
```
Key Vault must use **RBAC authorization** and **purge protection**.

## Check
```
make lab-check LAB=14
```

## Present it
Explain it out loud in five minutes: what talks to what, what is denied by default, where secrets live, how you would deploy it through change control (`what-if` → approval → deploy), and what you would monitor.

## Stretch
Add Azure Policy (as code) that denies public IPs on the VNet and requires tags.
