# 06 · CI/CD and GitOps

**Goal:** every push is tested; the cluster follows Git.

## Lab
1. Push this repo to GitHub; watch `.github/workflows/ci.yml` run.
2. Tag `v0.1.0` to build and push an image to GHCR (`image.yml`).
3. `terraform apply -var install_argocd=true`, edit `gitops/argocd/application.yaml` with your repo URL, apply it.
4. Change replicas in `k8s/overlays/dev`, push, watch Argo sync. Then `kubectl scale` by hand and watch self-heal revert it.

## Checkpoint
`make verify-06`

## Stretch
Add an image-tag bump step so a release updates the overlay automatically.
