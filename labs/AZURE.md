# Real Azure track: deploy it, look at it, destroy it

The checkers read your files. This track makes it real: you deploy to **your own personal Azure subscription**, see the resources in the portal, then delete them the same day. Practising the full cycle (plan → deploy → verify → destroy) is the actual job skill.

## Ground rules
1. **Personal subscription only.** Never your employer's or a customer's tenant. Never paste real tenant IDs, subscription IDs, or internal names into this repo.
2. **Budget alert first** (once): Azure portal → Cost Management → Budgets → Add. Set about $10/month with alerts at 50% and 90%, sent to your email.
3. **Name every resource group `rg-lab-<something>`.** The cleanup tool only ever deletes groups with that prefix.
4. **Destroy the same day.** `terraform destroy`, then run the sweep as a safety net.
5. Costs real money: AKS nodes, AVD session hosts, Log Analytics ingestion, Premium ACR. Near-free: resource groups, VNets, NSGs, storage, Key Vault.

## One-time setup (5 minutes)
```
az login --use-device-code          # open the link on any device, enter the code
make az-preflight                   # shows which subscription you are about to use
```
Read the subscription name it prints. If it is not your personal one, stop and run `az account set --subscription "<name>"`.

## The daily cycle
```
make az-preflight                                   # right account? budget set?
cd labs/05-terraform-azure-network/work
terraform init -backend=false
terraform plan  -var subscription_id=<your-id>      # read it: what will be created?
terraform apply -var subscription_id=<your-id>
# look in the portal, or:  az network vnet list -o table
terraform destroy -var subscription_id=<your-id>
cd ../../.. && make az-sweep                        # lists anything left behind (dry run)
make az-sweep-delete                                # deletes leftovers (you must type yes)
```

## Order (cheap first)
| Step | Lab | What you deploy | Cost |
|---|---|---|---|
| 1 | 05 | Resource group, VNet, subnets, NSG | free |
| 2 | 06 | Storage account (Bicep): `az deployment group what-if`, then `create` | cents |
| 3 | 07 | Parameter file + Key Vault reference, with `what-if` first | cents |
| 4 | 08 | Bicep modules: deny-by-default spoke network | free |
| 5 | 09 or 10 | AKS + ACR. **1 small node, deploy in the morning, destroy at lunch** | a few dollars/day |
| 6 | 12 | AVD host pool, app group, workspace (skip the session-host VM at first) | free to cents |

## When something goes wrong
- **`terraform destroy` fails:** read the error, fix the dependency, run it again. Then `make az-sweep`.
- **You forgot to destroy:** `make az-sweep-delete` the next morning. Check Cost Management the same day.
- **Quota or region errors:** try another region (`eastus2`, `centralus`) or a smaller VM size.
- **Not sure it is gone:** `az group list -o table` should show no `rg-lab-*` groups.
