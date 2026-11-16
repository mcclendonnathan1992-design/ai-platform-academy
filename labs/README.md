# Labs: learn it from day one, by writing it

The numbered **Modules** teach by running a finished project. The **Labs** are different: you start from a **blank file** and write it yourself, like learning the job from scratch.

Each lab folder has:
- `README.md`: the goal, the task, what the checker looks for, and questions to think about
- `work/`: **your files go here** (empty at first)
- `given/`: starting material, only in some labs
- `solution/`: a reference answer. **Write yours first**, then compare

## The loop
1. Read the lab README. Write your files in `work/`.
2. `make lab-check LAB=05` tells you which requirements pass or fail.
3. If the real tool is installed (terraform, docker, bicep), the checker runs it too.
4. Compare with `solution/`. Write in your notes what was different and why.
5. Commit your `work/` folder. Your Git history is your practice log.

## Path (about 30–45 minutes a day)
| Week | Labs | Skill |
|---|---|---|
| 1 | 01, 02 | Docker images and Compose |
| 2 | 03, 04 | Terraform and state (no Azure needed) |
| 3 | 05 | Terraform on Azure: networking |
| 4 | 06, 07, 08 | Bicep, ARM parameters, modules |
| 5 | 09, 10 | AKS + ACR, in Terraform and Bicep |
| 6 | 11 | Kubernetes manifests |
| 7 | 12 | Azure Virtual Desktop |
| 8 | 13 | Troubleshooting drills |
| 9–10 | 14 | Capstone enclave |

Pair each lab with the matching Module (03 containers, 04 Kubernetes, 05 Terraform) and the AZ-104 topics for the same week.

## Azure access and cost rules
Most labs need **no Azure account**: they are graded by reading your files and by `terraform validate` / `az bicep build`, which are offline.

To deploy for real:
- Use a **personal practice subscription** (the Azure free account has a starter credit), **not your employer's tenant**, unless your team gave you a sandbox subscription for this.
- Create a **budget alert** first (Cost Management → Budgets → Add).
- Sign in with `az login --use-device-code`.
- Always run `what-if` / `terraform plan` before the real deploy.
- **Destroy the same day**: `terraform destroy` or `az group delete -n <rg> --yes`.
- Free or near-free: VNets, NSGs, storage, Key Vault, resource groups. **Costs real money:** AKS nodes, Log Analytics ingestion, AVD session-host VMs, Premium ACR.

## Rules for yourself
- Never commit `.tfstate`, `*.tfvars` with secrets, `.env`, or passwords.
- Never paste real tenant IDs, subscription IDs, or internal names from work into this public repo.
