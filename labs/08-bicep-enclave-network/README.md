# Lab 08 · Bicep modules: a deny-by-default spoke network

**Why it matters:** an enclave is a network with explicit allow rules and a deny at the bottom. This lab builds one spoke with modules, the way you would split a real template.

## Task
In `work/` write three files:

**`modules/nsg.bicep`**: params `name`, `location`, `allowedSourcePrefix`. One NSG with an **allow 443 from `allowedSourcePrefix`** rule and a **deny-all-inbound at priority 4096**. Output its `id`.

**`modules/vnet.bicep`**: params `name`, `location`, `addressPrefix`, `subnets` (an `array` of `{ name, prefix }`), `nsgId`. A VNet whose subnets are built with a **loop** (`[for s in subnets: {...}]`), each attached to the NSG. Output its `id`.

**`main.bicep`**: `targetScope`, params (with a default `subnets` array of two subnets), then a **`module nsg`** and a **`module vnet`** that consumes `nsg.outputs.id`. Output the VNet ID.

## Check
```
make lab-check LAB=08
az bicep build --file labs/08-bicep-enclave-network/work/main.bicep
```

## Think about
- Why does `main.bicep` get the NSG ID from the module output instead of building the string by hand? (Bicep infers `dependsOn` from the reference.)
- What is the blast radius if someone adds an allow rule with priority 50?
- How would you add Azure Policy to *prevent* an NSG without a deny rule?

## Stretch
Add a hub VNet and **VNet peering** both ways. Peering is two resources, one per direction.
