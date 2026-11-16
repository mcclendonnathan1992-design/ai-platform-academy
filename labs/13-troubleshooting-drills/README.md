# Lab 13 · Troubleshooting drills: find and fix the bugs

**Why it matters:** on the job you fix other people's files far more often than you write new ones. Each file in `given/` has **three real bugs**.

## Task
Copy the four files into `work/` and fix them **in place**. Do not look at `solution/` until you are done.
```
cp labs/13-troubleshooting-drills/given/* labs/13-troubleshooting-drills/work/
```
Tools that find bugs:
- `Dockerfile`: read it top to bottom. Pinned tag? Root user? Shell vs exec form? Remote `ADD`?
- `main.tf`: `terraform init -backend=false && terraform validate` (it names undeclared variables); search for hardcoded IDs; check the provider block
- `main.bicep`: `az bicep build`, then ask: is the name globally unique? Is anything insecure?
- `app.yaml`: `kubectl apply --dry-run=client -f app.yaml`, then `kubectl describe`/endpoints. A Service with no endpoints means a selector mismatch.

## Write down
For each bug: what the symptom would be in production, and how you'd have found it without being told.

## Check
```
make lab-check LAB=13
```

## Stretch
Ask a teammate (or your tutor) to introduce three new bugs into the *solution* files and fix them blind.
