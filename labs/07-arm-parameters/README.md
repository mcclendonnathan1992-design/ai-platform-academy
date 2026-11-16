# Lab 07 · ARM parameter files, Key Vault secrets, and `what-if`

**Why it matters:** in a controlled environment you deploy the *same template* with different *parameter files*, and passwords never appear in either. This is how change tickets get approved: someone reads the what-if.

## Task
`given/template.json` is an ARM template with five parameters. Read it: which have **no default** (you must supply them), and which is a `securestring`?

In `work/` write:
1. `parameters.json` with the correct **deployment parameters schema** (`deploymentParameters.json#`), `contentVersion`, and a value for **every parameter that has no default**.
   - The `securestring` parameter must **not** contain a plaintext `value`. Use a **Key Vault reference** (`"reference": {"keyVault": {"id": ...}, "secretName": ...}`).
2. `deploy.sh` that creates the resource group, runs **`az deployment group what-if` first**, then **`az deployment group create`**, both with `--template-file template.json --parameters @parameters.json`.

Copy `given/template.json` into `work/` so the script runs from one folder.

## Check
```
make lab-check LAB=07
```
(also runs `bash -n deploy.sh` to catch syntax errors)

## Think about
- Why does a Key Vault reference need the vault's **resource ID** and not just its name?
- Which identity must have *Key Vault template deployment access* enabled and `get` on secrets?
- What would you put in a second file, `parameters.prod.json`?

## Stretch
Write the Bicep equivalent of the template and use a `.bicepparam` with `getSecret()`.
