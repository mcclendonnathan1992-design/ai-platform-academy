# 05 · Terraform

**Goal:** manage the *platform layer* as code. Maps to IaC for the platform-engineering role and to AZ-104 resource deployment.

## Ideas
Providers, state, plan/apply, variables, `terraform import`, Helm releases as resources. Split: Terraform owns namespace and add-ons; kustomize/Argo own the app.

## Lab
1. `cd terraform/local && terraform init`
2. `terraform import kubernetes_namespace.ai_lab ai-lab`
3. `terraform plan` (labels will be added). Apply.
4. `terraform apply -var install_monitoring=true`, then apply `k8s/observability/servicemonitor.yaml`.
5. Pin chart versions via `chart_versions`.
6. Read `terraform/azure-aks`. Run `plan` only. It costs money if applied; destroy immediately if you do.

## Checkpoint
`make verify-05`

## Stretch
Move state to a remote backend (Azure Storage) and explain locking.
