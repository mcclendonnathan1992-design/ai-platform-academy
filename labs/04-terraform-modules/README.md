# Lab 04 · Modules, `for_each`, locals, validation, tfvars

**Why it matters:** real Azure work is the same pattern repeated across environments. Modules and `for_each` are how you avoid copy-paste.

## Task (no Azure needed)
In `work/` build:
- `modules/naming/main.tf` taking `workload` and `environment`. The **environment variable has a `validation` block** that only allows `dev`, `test` or `prod`. A `locals` block builds a `prefix` and an `output "prefix"` exposes it.
- root `main.tf` with pinned providers, `variable "environments"` (a `set(string)`), and a `module "naming"` that uses **`for_each`** over it
- a `locals` block with a `tags` map
- a `local_file.inventory` using `for_each` over the module outputs, writing a JSON file per environment
- an `output "prefixes"` using a `for` expression
- `dev.tfvars` with `environments = ["dev","test"]`

```
cd labs/04-terraform-modules/work
terraform init && terraform apply -var-file=dev.tfvars
terraform apply -var 'environments=["prod","staging"]'      # watch validation reject "staging"
```

## Think about
- Why `set(string)` for `for_each`?
- What happens in the plan when you **remove** "test" from the set?
- `each.key` vs `each.value`: which is which?

## Check
```
make lab-check LAB=04
```

## Stretch
Add a second module that creates the inventory file, so the root only wires modules together.
