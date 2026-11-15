# 07 · Platform engineering: security, policy, golden paths

**Goal:** make the right way the easy way. Covers RBAC, policy-as-code, golden paths and an internal developer portal.

## Lab
1. `kubectl apply -f k8s/security/rbac.yaml`; check with `kubectl auth can-i get pods -n ai-lab --as=jane --as-group=ai-developers`.
2. `terraform apply -var install_kyverno=true`, apply `k8s/security/kyverno-policies.yaml`, then `kubectl get policyreport -A`. Fix violations, then switch a policy to `Enforce`.
3. `python scripts/new_service.py hello-api --dest /tmp` and read what you got for free.
4. Read `platform/backstage/`. A Backstage template wraps the same golden path; running Backstage itself is a stretch goal.

## Checkpoint
`make verify-07`

## Stretch
Add a policy requiring a `team` label and extend the golden path to satisfy it.
