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

## Practice tools
| Command | What it does |
|---|---|
| `make lab-check LAB=05` | grade your files (also runs terraform/bicep/docker and the policy scan if installed) |
| `make reset-lab LAB=05` | archive your attempt to `.attempts/` and restore a blank `work/` so you can redo the lab |
| `make break-lab LAB=05` | copy the solution into `work/` with 3 hidden bugs: find and fix them (`ARGS="--bugs 2 --seed 7"` to tune) |
| `make reveal LAB=05` | show which bugs were planted |
| `make drill` / `make drill-check` | today's 20-minute timed drill, from a blank file (`make drill-stats` for your streak) |
| `make clean` | free disk space: Docker cache, `.terraform` folders, caches; shows free space |
| `make install-checkov` | adds the security policy scan to `lab-check` (a few hundred MB, optional) |
| `make az-preflight`, `make az-sweep` | real-Azure safety rails: see [AZURE.md](AZURE.md) |

Good loop for a lab you already did once: `make reset-lab`, redo it faster, then `make break-lab` and fix the bugs without looking at the solution.

## Azure access and cost rules
Most labs need **no Azure account**: they are graded by reading your files and by `terraform validate` / `az bicep build`, which are offline.

To deploy for real, follow [AZURE.md](AZURE.md). The short version:
- Use a **personal practice subscription** (the Azure free account has a starter credit), **not your employer's tenant**, unless your team gave you a sandbox subscription for this.
- Create a **budget alert** first (Cost Management → Budgets → Add).
- Sign in with `az login --use-device-code`.
- Always run `what-if` / `terraform plan` before the real deploy.
- **Destroy the same day**: `terraform destroy` or `az group delete -n <rg> --yes`.
- Free or near-free: VNets, NSGs, storage, Key Vault, resource groups. **Costs real money:** AKS nodes, Log Analytics ingestion, AVD session-host VMs, Premium ACR.

## Rules for yourself
- Never commit `.tfstate`, `*.tfvars` with secrets, `.env`, or passwords.
- Never paste real tenant IDs, subscription IDs, or internal names from work into this public repo.
