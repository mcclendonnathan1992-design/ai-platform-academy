# 04 · Kubernetes

**Goal:** deploy the stack to a local kind cluster. Maps to CKA workloads, services, config and scaling.

## Ideas
Deployments, Services, ConfigMaps, PVCs, Jobs, probes, resource requests/limits, HPA, PDB, NetworkPolicy, ResourceQuota, kustomize overlays.

## Lab
1. `make kind-up`
2. `docker build -t ai-gateway:dev app && kind load docker-image ai-gateway:dev --name ai-lab`
3. `kubectl create namespace ai-lab` (Module 05 adopts it into Terraform)
4. `kubectl apply -k k8s/overlays/dev -n ai-lab`
5. `kubectl -n ai-lab get pods -w`. The model-pull Job takes a while.
6. `kubectl -n ai-lab port-forward svc/gateway 8080:80` then call `/v1/chat`.
7. Break it: set a bad `MODEL` in the ConfigMap, restart, and read `kubectl describe` and logs to diagnose.
8. Kill a gateway pod and watch recovery. Why does `readyz` matter here?

## Checkpoint
`make verify-04`

## Stretch
HPA needs metrics-server; install it on kind and generate load with `scripts/benchmark.py`.
