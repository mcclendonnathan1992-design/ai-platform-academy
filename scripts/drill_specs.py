"""The daily 20-minute drills. Each is a small task written from a blank file.

A Drill names the one file you write (in drills/work/<id>/), what the prompt says, and the checks.
Reference answers live in drills/solutions/<id>/ and are tested, but you do not read them first.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from labkit import (
    Check, Ctx, bicep_blocks, bicep_text, check, dockerfile_instructions, load_json, load_yaml_docs, tf_blocks, tf_text,
)


@dataclass
class Drill:
    id: str
    title: str
    file: str
    prompt: str
    checks: list[Check]


def t(desc, fn) -> Check:
    return check(desc, fn)


# ---------------------------------------------------------------- helpers


def _ins(ctx: Ctx):
    return dockerfile_instructions(ctx.root / "Dockerfile")


def _tf(ctx: Ctx, kind: str, label: str):
    return [b for b in tf_blocks(tf_text(ctx)) if b.kind == kind and b.labels[:1] == (label,)]


def _tf_res(ctx: Ctx, rtype: str) -> str:
    body = "\n".join(b.body for b in _tf(ctx, "resource", rtype))
    if not body:
        raise ValueError(f'no resource "{rtype}"')
    return body


def _need(body: str, pattern: str, msg: str):
    return True if re.search(pattern, body, re.S) else msg


def _bicep_body(ctx: Ctx, prefix: str) -> str:
    bodies = [b.body for b in bicep_blocks(bicep_text(ctx)) if b.kind == "resource" and b.labels[1].lower().startswith(prefix.lower() + "@")]
    if not bodies:
        raise ValueError(f"no resource {prefix}")
    return "\n".join(bodies)


def _docs(ctx: Ctx) -> list[dict]:
    return load_yaml_docs(ctx, "*.yaml", "*.yml")


def _kind(ctx: Ctx, kind: str) -> dict:
    for d in _docs(ctx):
        if d.get("kind") == kind:
            return d
    raise ValueError(f"no {kind}")


# ---------------------------------------------------------------- the drills


def _docker_ok_base(c: Ctx):
    images = [a.split()[0] for n, a in _ins(c) if n == "FROM"]
    return True if images and all(":" in i and not i.endswith(":latest") for i in images) else "pin the base image tag"


def _docker_user(c: Ctx):
    users = [a for n, a in _ins(c) if n == "USER"]
    return True if users and users[-1].split(":")[0].isdigit() and users[-1].split(":")[0] != "0" else "USER must be a numeric non-root id"


def _docker_cmd_exec(c: Ctx):
    cmds = [a for n, a in _ins(c) if n == "CMD"]
    if not cmds or not cmds[-1].startswith("["):
        return "CMD must be exec form"
    return True if "uvicorn" in cmds[-1] else "CMD must start uvicorn"


D1 = Drill("dockerfile-api", "Dockerfile for a FastAPI service", "Dockerfile",
           "Write Dockerfile: pinned python slim base, install requirements.txt before copying code, numeric non-root USER, EXPOSE 8000, exec-form CMD that starts uvicorn main:app on 0.0.0.0:8000.", [
    t("base image pinned", _docker_ok_base),
    t("requirements copied before the code", lambda c: (lambda i: next((k for k, (n, a) in enumerate(i) if n == "COPY" and "requirements" in a), 99) < next((k for k, (n, a) in enumerate(i) if n == "COPY" and "requirements" not in a), 100) or "COPY requirements first")(_ins(c))),
    t("numeric non-root user", _docker_user),
    t("EXPOSE 8000", lambda c: any(n == "EXPOSE" and "8000" in a for n, a in _ins(c)) or "EXPOSE 8000"),
    t("CMD exec form with uvicorn", _docker_cmd_exec),
])


def _compose(c: Ctx):
    docs = _docs(c)
    if not docs:
        raise ValueError("no yaml")
    return docs[0]


D2 = Drill("compose-redis", "Compose: app + Redis with a healthcheck", "docker-compose.yml",
           "Write docker-compose.yml: service api (build: ., port 8000:8000, env REDIS_HOST=cache) and service cache (redis with a pinned tag, named volume, healthcheck). api must wait until cache is healthy. Declare the volume at the top level.", [
    t("two services api and cache", lambda c: {"api", "cache"} <= set(_compose(c).get("services", {})) or "services api and cache"),
    t("redis tag pinned", lambda c: bool(re.match(r"redis:[\w.\-]+$", str(_compose(c)["services"]["cache"].get("image", "")))) and not str(_compose(c)["services"]["cache"]["image"]).endswith(":latest") or "pin redis:<tag>"),
    t("cache has a healthcheck", lambda c: "healthcheck" in _compose(c)["services"]["cache"] or "add healthcheck"),
    t("api waits for service_healthy", lambda c: _compose(c)["services"]["api"].get("depends_on", {}).get("cache", {}).get("condition") == "service_healthy" or "depends_on cache condition: service_healthy"),
    t("named volume declared and used", lambda c: bool(_compose(c).get("volumes")) and any(":" in str(v) and not str(v).startswith(("/", ".")) for v in _compose(c)["services"]["cache"].get("volumes", [])) or "named volume on cache"),
])

D3 = Drill("tf-storage", "Terraform: a locked-down storage account", "main.tf",
           "Write main.tf: variables location and environment; resource group; storage account with HTTPS only, TLS1_2 minimum, no public blob access, GRS replication, and tags from a locals block; output the storage account id.", [
    t("variables location and environment", lambda c: all(_tf(c, "variable", v) for v in ("location", "environment")) or "declare both variables"),
    t("resource group", lambda c: bool(_tf_res(c, "azurerm_resource_group")) or "rg"),
    t("https only", lambda c: _need(_tf_res(c, "azurerm_storage_account"), r"https_traffic_only_enabled\s*=\s*true", "https_traffic_only_enabled = true")),
    t("TLS 1.2", lambda c: _need(_tf_res(c, "azurerm_storage_account"), r'min_tls_version\s*=\s*"TLS1_2"', 'min_tls_version = "TLS1_2"')),
    t("no public blob access", lambda c: _need(_tf_res(c, "azurerm_storage_account"), r"allow_nested_items_to_be_public\s*=\s*false", "allow_nested_items_to_be_public = false")),
    t("GRS", lambda c: _need(_tf_res(c, "azurerm_storage_account"), r'account_replication_type\s*=\s*"GRS"', 'account_replication_type = "GRS"')),
    t("tags from locals", lambda c: (bool(_tf(c, "locals", "")) or any(b.kind == "locals" for b in tf_blocks(tf_text(c)))) and "local.tags" in tf_text(c) or "locals { tags } used as local.tags"),
    t("output the id", lambda c: bool(_tf(c, "output", "storage_account_id")) or 'output "storage_account_id"'),
])

D4 = Drill("tf-nsg", "Terraform: deny-by-default NSG", "main.tf",
           "Write main.tf with an azurerm_network_security_group (use a variable for the resource group name): allow TCP 443 inbound from a variable source prefix at priority 100, deny all inbound at priority 4096.", [
    t("NSG exists", lambda c: bool(_tf_res(c, "azurerm_network_security_group")) or "nsg"),
    t("allow 443 at priority 100", lambda c: _need(_tf_res(c, "azurerm_network_security_group"), r'priority\s*=\s*100\b.*?"443"|"443".*?priority\s*=\s*100\b', "allow rule: priority 100, port 443")),
    t("allow source is a variable", lambda c: _need(_tf_res(c, "azurerm_network_security_group"), r"source_address_prefix\s*=\s*var\.", "source_address_prefix = var.<x>")),
    t("deny all inbound at 4096", lambda c: _need(_tf_res(c, "azurerm_network_security_group"), r'priority\s*=\s*4096.*?access\s*=\s*"Deny"|access\s*=\s*"Deny".*?priority\s*=\s*4096', "Deny rule at priority 4096")),
    t("resource group from a variable", lambda c: _need(_tf_res(c, "azurerm_network_security_group"), r"resource_group_name\s*=\s*var\.", "resource_group_name = var.<x>")),
])

D5 = Drill("bicep-storage", "Bicep: a locked-down storage account", "main.bicep",
           "Write main.bicep: params storageName (3–24 chars, with @minLength/@maxLength) and location (default resourceGroup().location); a Standard_GRS StorageV2 account with HTTPS only, TLS 1.2, blob public access off; output its id.", [
    t("storageName param with length limits", lambda c: bool(re.search(r"@minLength\(3\)", bicep_text(c))) and bool(re.search(r"@maxLength\(24\)", bicep_text(c))) or "@minLength(3) @maxLength(24)"),
    t("location param defaults to the resource group", lambda c: "resourceGroup().location" in bicep_text(c) or "default to resourceGroup().location"),
    t("StorageV2, Standard_GRS", lambda c: _need(_bicep_body(c, "Microsoft.Storage/storageAccounts"), r"Standard_GRS.*StorageV2|StorageV2.*Standard_GRS", "sku Standard_GRS and kind StorageV2")),
    t("HTTPS only", lambda c: _need(_bicep_body(c, "Microsoft.Storage/storageAccounts"), r"supportsHttpsTrafficOnly:\s*true", "supportsHttpsTrafficOnly: true")),
    t("TLS 1.2", lambda c: _need(_bicep_body(c, "Microsoft.Storage/storageAccounts"), r"minimumTlsVersion:\s*'TLS1_2'", "minimumTlsVersion: 'TLS1_2'")),
    t("no public blob access", lambda c: _need(_bicep_body(c, "Microsoft.Storage/storageAccounts"), r"allowBlobPublicAccess:\s*false", "allowBlobPublicAccess: false")),
    t("output id", lambda c: bool(re.search(r"^\s*output\s+\w+\s+string\s*=", bicep_text(c), re.M)) or "output <name> string = ....id"),
])

D6 = Drill("bicep-keyvault", "Bicep: Key Vault with RBAC and purge protection", "main.bicep",
           "Write main.bicep: a Key Vault (standard SKU, tenantId from subscription().tenantId) with RBAC authorization, soft delete, purge protection and public network access disabled.", [
    t("vault exists", lambda c: bool(_bicep_body(c, "Microsoft.KeyVault/vaults")) or "vault"),
    t("standard SKU", lambda c: _need(_bicep_body(c, "Microsoft.KeyVault/vaults"), r"name:\s*'standard'", "sku name: 'standard'")),
    t("tenantId from subscription()", lambda c: "subscription().tenantId" in bicep_text(c) or "tenantId: subscription().tenantId"),
    t("RBAC authorization", lambda c: _need(_bicep_body(c, "Microsoft.KeyVault/vaults"), r"enableRbacAuthorization:\s*true", "enableRbacAuthorization: true")),
    t("soft delete + purge protection", lambda c: _need(_bicep_body(c, "Microsoft.KeyVault/vaults"), r"enableSoftDelete:\s*true.*enablePurgeProtection:\s*true|enablePurgeProtection:\s*true.*enableSoftDelete:\s*true", "enableSoftDelete and enablePurgeProtection true")),
    t("public access disabled", lambda c: _need(_bicep_body(c, "Microsoft.KeyVault/vaults"), r"publicNetworkAccess:\s*'Disabled'", "publicNetworkAccess: 'Disabled'")),
])


def _params(c: Ctx) -> dict:
    return load_json(c.root / "parameters.json")


D7 = Drill("arm-params", "ARM parameter file with a Key Vault reference", "parameters.json",
           "Write parameters.json (deployment parameters schema, contentVersion 1.0.0.0) with vmName and adminUsername as values and adminPassword as a Key Vault reference (id + secretName). No plaintext password.", [
    t("deployment parameters schema", lambda c: "deploymentParameters.json" in _params(c).get("$schema", "") or "use the deploymentParameters.json $schema"),
    t("contentVersion 1.0.0.0", lambda c: _params(c).get("contentVersion") == "1.0.0.0" or "contentVersion 1.0.0.0"),
    t("vmName and adminUsername values", lambda c: all("value" in _params(c)["parameters"].get(k, {}) for k in ("vmName", "adminUsername")) or "value for each"),
    t("adminPassword is a Key Vault reference", lambda c: (lambda r: "id" in r.get("keyVault", {}) and bool(r.get("secretName")))(_params(c)["parameters"]["adminPassword"].get("reference", {})) or "reference.keyVault.id and reference.secretName"),
    t("no plaintext value for adminPassword", lambda c: "value" not in _params(c)["parameters"]["adminPassword"] or "remove the value"),
])


def _deploy(c: Ctx):
    docs = [d for d in _docs(c) if d.get("kind") == "Deployment"]
    if not docs:
        raise ValueError("no Deployment")
    return docs[0]


def _container(c: Ctx) -> dict:
    return _deploy(c)["spec"]["template"]["spec"]["containers"][0]


D8 = Drill("k8s-deployment", "Deployment + Service, production habits", "app.yaml",
           "Write app.yaml: a Deployment (2 replicas, pinned image tag, readiness and liveness probes, CPU/memory requests and limits, runAsNonRoot, no privilege escalation) and a Service whose selector matches the pod labels.", [
    t("2 replicas", lambda c: _deploy(c)["spec"]["replicas"] == 2 or "replicas: 2"),
    t("image pinned", lambda c: ":" in _container(c)["image"] and not _container(c)["image"].endswith(":latest") or "pin the tag"),
    t("readiness and liveness probes", lambda c: all(k in _container(c) for k in ("readinessProbe", "livenessProbe")) or "both probes"),
    t("requests and limits", lambda c: all(k in _container(c).get("resources", {}) for k in ("requests", "limits")) or "resources requests and limits"),
    t("runAsNonRoot, no privilege escalation", lambda c: (_container(c).get("securityContext", {}).get("allowPrivilegeEscalation") is False) and (_container(c).get("securityContext", {}).get("runAsNonRoot") is True or _deploy(c)["spec"]["template"]["spec"].get("securityContext", {}).get("runAsNonRoot") is True) or "runAsNonRoot: true and allowPrivilegeEscalation: false"),
    t("Service selector matches pod labels", lambda c: all(_deploy(c)["spec"]["template"]["metadata"]["labels"].get(k) == v for k, v in _kind(c, "Service")["spec"]["selector"].items()) or "selector must match the pod template labels"),
])


def _netpols(c: Ctx):
    return [d for d in _docs(c) if d.get("kind") == "NetworkPolicy"]


D9 = Drill("k8s-netpol", "NetworkPolicy: default deny + one allow", "netpol.yaml",
           "Write netpol.yaml in namespace ai-lab: a default-deny policy for all ingress (empty podSelector), and a second policy that allows ingress to pods labeled app=gateway on TCP 8080 only from pods labeled app=ingress.", [
    t("two NetworkPolicies", lambda c: len(_netpols(c)) >= 2 or "two NetworkPolicy documents"),
    t("default deny: empty podSelector, Ingress, no rules", lambda c: any(p["spec"].get("podSelector") == {} and "Ingress" in p["spec"].get("policyTypes", []) and not p["spec"].get("ingress") for p in _netpols(c)) or "empty podSelector, policyTypes [Ingress], no ingress rules"),
    t("allow policy targets app=gateway", lambda c: any(p["spec"].get("podSelector", {}).get("matchLabels") == {"app": "gateway"} for p in _netpols(c)) or "podSelector matchLabels app: gateway"),
    t("allows only from app=ingress on 8080", lambda c: any(json.dumps(p["spec"].get("ingress", [])).count("ingress") >= 1 and "8080" in json.dumps(p["spec"].get("ingress", [])) for p in _netpols(c)) or "from podSelector app: ingress, port 8080"),
    t("namespace ai-lab", lambda c: bool(_netpols(c)) and all(p["metadata"].get("namespace") == "ai-lab" for p in _netpols(c)) or "namespace: ai-lab"),
])

D10 = Drill("tf-for-each", "Terraform: three resource groups with for_each", "main.tf",
            "Write main.tf: variable workloads (map of string to string: name -> location), and a resource group for each entry using for_each with common tags from locals; output a map of name -> id.", [
    t("variable workloads is a map(string)", lambda c: _need(" ".join(b.body for b in _tf(c, "variable", "workloads")), r"map\(string\)", "type = map(string)")),
    t("for_each on the resource group", lambda c: _need(_tf_res(c, "azurerm_resource_group"), r"for_each\s*=\s*var\.workloads", "for_each = var.workloads")),
    t("uses each.key and each.value", lambda c: _need(_tf_res(c, "azurerm_resource_group"), r"each\.key.*each\.value|each\.value.*each\.key", "use each.key and each.value")),
    t("tags from locals", lambda c: "local.tags" in tf_text(c) or "tags = local.tags"),
    t("output is a for expression", lambda c: bool(re.search(r"output\s+\"\w+\".*?\bfor\s+\w+", tf_text(c), re.S)) or "output { for k, v in azurerm_resource_group.x : k => v.id }"),
])

D11 = Drill("tf-validation", "Terraform: validated variables", "main.tf",
            "Write main.tf with: variable environment (string, validated so only dev, test or prod are allowed with a clear error_message), variable admin_password (sensitive = true, no default), and an output that echoes the environment.", [
    t("environment validation with contains()", lambda c: _need(" ".join(b.body for b in _tf(c, "variable", "environment")), r"validation\s*\{.*contains\(.*\).*error_message", "validation { condition = contains([...], var.environment) error_message = ... }")),
    t("allowed values dev, test, prod", lambda c: all(v in " ".join(b.body for b in _tf(c, "variable", "environment")) for v in ('"dev"', '"test"', '"prod"')) or "list dev, test, prod"),
    t("admin_password sensitive, no default", lambda c: (lambda body: "sensitive" in body and "true" in body and "default" not in body)(" ".join(b.body for b in _tf(c, "variable", "admin_password"))) or "sensitive = true and no default"),
    t("an output exists", lambda c: any(b.kind == "output" for b in tf_blocks(tf_text(c))) or "add an output"),
])

D12 = Drill("dockerfile-multistage", "Multi-stage Dockerfile that copies only what it needs", "Dockerfile",
            "Write a two-stage Dockerfile: stage 'build' (pinned python) pip-installs requirements into /install with --no-cache-dir; final stage (pinned slim) copies from the build stage, copies app.py, runs as numeric user 10001, has a HEALTHCHECK, and an exec-form CMD.", [
    t("two stages, one named build", lambda c: sum(1 for n, _ in _ins(c) if n == "FROM") == 2 and any(re.search(r"\bAS\s+build\b", a, re.I) for n, a in _ins(c) if n == "FROM") or "two FROM lines; the first AS build"),
    t("bases pinned", _docker_ok_base),
    t("pip --no-cache-dir", lambda c: any(n == "RUN" and "--no-cache-dir" in a for n, a in _ins(c)) or "pip install --no-cache-dir"),
    t("COPY --from=build", lambda c: any(n == "COPY" and "--from=build" in a for n, a in _ins(c)) or "COPY --from=build"),
    t("USER 10001", lambda c: any(n == "USER" and a.split(":")[0] == "10001" for n, a in _ins(c)) or "USER 10001"),
    t("HEALTHCHECK", lambda c: any(n == "HEALTHCHECK" for n, _ in _ins(c)) or "add HEALTHCHECK"),
    t("exec-form CMD", lambda c: any(n == "CMD" and a.startswith("[") for n, a in _ins(c)) or 'CMD ["python", "app.py"]'),
])

DRILLS: dict[str, Drill] = {d.id: d for d in (D1, D2, D3, D4, D5, D6, D7, D8, D9, D10, D11, D12)}
