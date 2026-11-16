# Lab 11 · Kubernetes manifests from a blank file

**Why it matters:** AKS is Kubernetes. You must be able to write and read these files without a template.

## Task
In `work/app.yaml` (multi-document YAML, separated by `---`) write everything needed to run `nginxinc/nginx-unprivileged:1.27` (listens on **8080**):
1. **ServiceAccount** `web` with `automountServiceAccountToken: false`
2. **ConfigMap** `web-config`
3. **Deployment** `web`: 2 replicas, labels that match the selector, **pod** `runAsNonRoot` + seccomp `RuntimeDefault`, **container** `allowPrivilegeEscalation: false`, read-only root filesystem, drop ALL capabilities, a **named port**, **liveness and readiness probes**, **requests and limits**, config from the ConfigMap, and `API_KEY` from a **`secretKeyRef`** (never a literal secret)
4. **Service** `web` selecting the pods
5. **PodDisruptionBudget** so at least 1 pod stays up
6. **NetworkPolicy**: a default-deny ingress for the namespace and an allow from the `ingress-nginx` namespace to port 8080
7. **Role + RoleBinding** letting the ServiceAccount read ConfigMaps only

## Check
```
make lab-check LAB=11
```
(the checker also validates each object against the Kubernetes 1.31 API schema)

## Run it for real (your kind cluster from Module 04)
```
kubectl create namespace lab11
kubectl -n lab11 create secret generic web-secrets --from-literal=api-key=not-a-real-key
kubectl -n lab11 apply -f labs/11-k8s-from-scratch/work/app.yaml
kubectl -n lab11 get pods
kubectl -n lab11 auth can-i get secrets --as=system:serviceaccount:lab11:web      # should be "no"
```

## Think about
- Why a named port instead of a number in the Service and probes?
- Why do the Service selector and the Deployment's pod labels both have to match?
- What does the default-deny policy do on a cluster whose CNI doesn't enforce NetworkPolicy?

## Stretch
Add an `Ingress` and an HPA. Break each thing on purpose and read the events.
