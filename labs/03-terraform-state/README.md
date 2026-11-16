# Lab 03 · Terraform and state, from day one (no Azure needed)

**Why it matters:** state is the part of Terraform that bites in real jobs. You will practice it safely with the `local` and `random` providers: free, offline-ish, and every command behaves like it does on Azure.

## Part A: write it
In `work/main.tf`:
- a `terraform` block with `required_version` and **pinned** `required_providers` (`hashicorp/local`, `hashicorp/random`)
- a `variable "environment"` with `description`, `type`, and a `default`
- `random_pet.name` and a `local_file.config` that writes `env=<environment>` and the pet name into `out/<pet>.txt`
- an `output "file_path"` with a description
- a `.gitignore` that keeps **state, `.terraform/`, and `*.tfvars`** out of Git

```
cd labs/03-terraform-state/work
terraform init
terraform fmt && terraform validate
terraform plan
terraform apply
```

## Part B: state drills (do each, write one sentence on what you saw)
1. `terraform state list` and `terraform state show local_file.config`
2. Delete `out/*.txt` by hand, run `terraform plan`. Terraform notices the **drift**. Apply to fix it.
3. Change the variable: `terraform apply -var environment=prod`. What changed, and what did not?
4. `terraform apply -replace=random_pet.name`. Why did the file change too?
5. `terraform state rm local_file.config`, then `terraform plan`. What does Terraform now want to do? Then **re-adopt** the file instead: `terraform import local_file.config <path>` (read the provider docs for the import ID).
6. `terraform state mv random_pet.name random_pet.renamed`. Update the code to match. A clean plan means you did it right.
7. Open `terraform.tfstate` in an editor. Find the pet name. Now you know why state must never go in Git and why remote state needs locking.

## Check
```
make lab-check LAB=03
```
(also runs `terraform fmt -check` and `validate` if Terraform is installed)

## Stretch
Add a `sensitive = true` output and see how it appears in the plan, the CLI, and the state file.
