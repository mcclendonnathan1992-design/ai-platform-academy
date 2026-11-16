"""What each lab's checker looks for. One entry per lab: LABS["05"] -> Spec."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from labkit import (
    GUID, Check, Ctx, Result, bicep_blocks, bicep_has_resource, bicep_resource_has, bicep_text, bicep_tool,
    check, dockerfile_instructions, load_json, load_yaml_docs, run_tool, strip_comments, terraform_tool,
    tf_blocks, tf_declares, terraform_plan_tool, checkov_tool, CHECKOV_SKIPS, tf_has_resource, tf_resource_has, tf_syntax, tf_text,
)


@dataclass
class Spec:
    title: str
    checks: list[Check]
    tools: list[Callable[[Ctx], Result | list[Result]]] = field(default_factory=list)


def t(desc: str, fn) -> Check:
    return check(desc, fn)


def has(ctx: Ctx, pattern: str) -> bool:
    return bool(re.search(pattern, tf_text(ctx), re.S))


# ------------------------------------------------------------------ Dockerfile helpers

def _df(ctx: Ctx) -> list[tuple[str, str]]:
    path = ctx.root / "Dockerfile"
    if not path.exists():
        raise FileNotFoundError("Dockerfile not found in work/")
    return dockerfile_instructions(path)


def _from_images(ins) -> list[str]:
    images, stages = [], set()
    for name, args in ins:
        if name != "FROM":
            continue
        parts = [p for p in args.split() if not p.startswith("--")]
        image = parts[0]
        if len(parts) >= 3 and parts[1].upper() == "AS":
            stages.add(parts[2])
        if image not in stages and image != "scratch":
            images.append(image)
    return images


def _pinned(ctx: Ctx):
    bad = [i for i in _from_images(_df(ctx)) if "@sha256:" not in i and (":" not in i or i.endswith(":latest"))]
    return True if not bad and _from_images(_df(ctx)) else f"not pinned: {bad or 'no FROM'}"


def _req_first(ctx: Ctx):
    copies = [a for n, a in _df(ctx) if n == "COPY" and "--from" not in a]
    req = [i for i, a in enumerate(copies) if "requirements" in a]
    other = [i for i, a in enumerate(copies) if "requirements" not in a]
    if not req:
        return "no COPY of requirements.txt"
    return True if not other or min(req) < min(other) else "code is copied before requirements.txt"


def _nonroot(ctx: Ctx):
    users = [a for n, a in _df(ctx) if n == "USER"]
    if not users:
        return "no USER instruction (container runs as root)"
    return True if re.fullmatch(r"[1-9]\d*(:\d+)?", users[-1]) else f"USER {users[-1]!r} is not a numeric non-root id"


def _cmd_exec(ctx: Ctx):
    cmds = [a for n, a in _df(ctx) if n in ("CMD", "ENTRYPOINT")]
    return True if cmds and cmds[-1].startswith("[") else "CMD/ENTRYPOINT should be exec form: [\"python\", \"app.py\"]"


def _no_remote_add(ctx: Ctx):
    return True if not any(n == "ADD" and re.search(r"https?://", a) for n, a in _df(ctx)) else "ADD with a URL: use curl in RUN with a checksum, or COPY"


def _docker_build(ctx: Ctx):
    if not (ctx.root / "app.py").exists():
        return Result("docker build succeeds", None, "copy given/* into work/ to enable this check")
    return run_tool("docker build succeeds", "docker", ["build", "-q", "-t", "lab:check", "."], ctx.root, timeout=300)


LAB01 = Spec("Dockerfile from scratch", [
    t("Dockerfile exists", lambda c: (c.root / "Dockerfile").exists() or "write work/Dockerfile"),
    t("base image(s) pinned to a tag (not latest)", _pinned),
    t("multi-stage build (2+ FROM)", lambda c: len([1 for n, _ in _df(c) if n == "FROM"]) >= 2 or "use a builder stage"),
    t("requirements copied before the code", _req_first),
    t("runs as a numeric non-root user", _nonroot),
    t("EXPOSE 8080", lambda c: any(n == "EXPOSE" and "8080" in a for n, a in _df(c)) or "add EXPOSE 8080"),
    t("HEALTHCHECK present", lambda c: any(n == "HEALTHCHECK" for n, _ in _df(c)) or "add a HEALTHCHECK"),
    t("CMD in exec form", _cmd_exec),
    t("no ADD from a URL", _no_remote_add),
    t(".dockerignore exists", lambda c: (c.root / ".dockerignore").exists() or "write .dockerignore"),
], [_docker_build])


# ------------------------------------------------------------------ Compose

def _compose(ctx: Ctx) -> dict:
    import yaml

    path = ctx.root / "docker-compose.yml"
    if not path.exists():
        raise FileNotFoundError("write work/docker-compose.yml")
    return yaml.safe_load(path.read_text())


def _svc(ctx: Ctx, name: str) -> dict:
    services = _compose(ctx).get("services", {})
    if name not in services:
        raise KeyError(f"service {name!r} missing")
    return services[name]


def _cache_pinned(ctx: Ctx):
    image = _svc(ctx, "cache").get("image", "")
    return True if ":" in image and not image.endswith(":latest") else f"pin the redis tag (got {image!r})"


def _named_volume(ctx: Ctx):
    top = _compose(ctx).get("volumes") or {}
    mounts = [v for v in _svc(ctx, "cache").get("volumes", []) if isinstance(v, str)]
    return True if any(m.split(":")[0] in top for m in mounts) else "cache must mount a top-level named volume"


def _depends_healthy(ctx: Ctx):
    dep = _svc(ctx, "api").get("depends_on")
    ok = isinstance(dep, dict) and dep.get("cache", {}).get("condition") == "service_healthy"
    return True if ok else "api.depends_on.cache.condition must be service_healthy"


def _shared_network(ctx: Ctx):
    top = _compose(ctx).get("networks") or {}
    api, cache = _svc(ctx, "api").get("networks", []), _svc(ctx, "cache").get("networks", [])
    shared = (set(api) & set(cache)) & set(top)
    return True if shared else "define a top-level network and attach both services to it"


def _env_file(ctx: Ctx):
    files = _svc(ctx, "api").get("env_file")
    files = [files] if isinstance(files, str) else files
    if not files:
        return "api needs env_file"
    ok = any((ctx.root / f).exists() or (ctx.root / (f + ".example")).exists() for f in files)
    return True if ok else f"create {files[0]} (or {files[0]}.example) with a fake value"


LAB02 = Spec("Docker Compose from scratch", [
    t("docker-compose.yml parses and has api + cache", lambda c: bool(_svc(c, "api")) and bool(_svc(c, "cache")) or "need both services"),
    t("cache image has a pinned tag", _cache_pinned),
    t("cache uses a named volume", _named_volume),
    t("cache has a healthcheck", lambda c: bool(_svc(c, "cache").get("healthcheck")) or "add healthcheck"),
    t("api waits for cache to be healthy", _depends_healthy),
    t("both services share a user-defined network", _shared_network),
    t("api reads secrets from an env_file that exists", _env_file),
    t("api has build or image", lambda c: ("build" in _svc(c, "api") or "image" in _svc(c, "api")) or "api needs build: or image:"),
    t("no privileged containers", lambda c: not any(s.get("privileged") for s in _compose(c)["services"].values()) or "remove privileged: true"),
])


# ------------------------------------------------------------------ Terraform labs

def _pinned_providers(ctx: Ctx):
    tf = [b for b in tf_blocks(tf_text(ctx)) if b.kind == "terraform"]
    body = "\n".join(b.body for b in tf)
    if "required_version" not in body:
        return "terraform block needs required_version"
    n_src = len(re.findall(r"\bsource\s*=", body))
    n_ver = len(re.findall(r"\bversion\s*=", body))
    return True if n_src and n_ver >= n_src else "every required_provider needs a version constraint"


def _var_ok(ctx: Ctx, name: str, *attrs: str):
    for b in tf_blocks(tf_text(ctx)):
        if b.kind == "variable" and b.labels[:1] == (name,):
            missing = [a for a in attrs if not re.search(rf"\b{a}\s*=", b.body)]
            return True if not missing else f"variable {name} is missing {missing}"
    return f'declare variable "{name}"'


def _output_ok(ctx: Ctx, name: str):
    for b in tf_blocks(tf_text(ctx)):
        if b.kind == "output" and b.labels[:1] == (name,):
            return True if "description" in b.body else f"output {name} needs a description"
    return f'declare output "{name}"'


def _gitignore(ctx: Ctx):
    p = ctx.root / ".gitignore"
    if not p.exists():
        return "write .gitignore"
    text = p.read_text()
    return True if "tfstate" in text and ".terraform" in text else ".gitignore must exclude *.tfstate and .terraform/"


def _no_guid(ctx: Ctx):
    return True if not GUID.search(tf_text(ctx)) else "hardcoded GUID found: use a variable"


LAB03 = Spec("Terraform and state", [
    t("HCL syntax is valid", tf_syntax),
    t("terraform block: required_version + pinned providers", _pinned_providers),
    t("variable environment: description, type, default", lambda c: _var_ok(c, "environment", "description", "type", "default")),
    t("resource random_pet", lambda c: tf_has_resource(c, "random_pet") or "add random_pet"),
    t("resource local_file writes the environment", lambda c: tf_resource_has(c, "local_file", r"var\.environment")),
    t("output file_path with a description", lambda c: _output_ok(c, "file_path")),
    t(".gitignore keeps state out of Git", _gitignore),
], [terraform_tool])


def _module_for_each(ctx: Ctx):
    for b in tf_blocks(tf_text(ctx)):
        if b.kind == "module" and b.labels[:1] == ("naming",):
            if not re.search(r'source\s*=\s*"\./modules/', b.body):
                return 'module "naming" source must be ./modules/...'
            return True if "for_each" in b.body else "module needs for_each"
    return 'declare module "naming"'


def _validation_block(ctx: Ctx):
    for b in tf_blocks(tf_text(ctx)):
        if b.kind == "variable" and b.labels[:1] == ("environment",) and re.search(r"validation\s*\{", b.body) and "contains(" in b.body:
            return True
    return 'variable "environment" needs a validation block using contains()'


LAB04 = Spec("Terraform modules, for_each, validation", [
    t("HCL syntax is valid", tf_syntax),
    t("modules/naming/ exists", lambda c: c.exists("modules/naming/*.tf") or "create modules/naming/main.tf"),
    t("environment variable validated with contains()", _validation_block),
    t("module naming uses for_each and a local source", _module_for_each),
    t("root variable environments is set(string)", lambda c: has(c, r'variable\s+"environments".*?type\s*=\s*set\(string\)') or "type = set(string)"),
    t("locals block defines tags", lambda c: any(b.kind == "locals" and "tags" in b.body for b in tf_blocks(tf_text(c))) or "add locals { tags = ... }"),
    t("local_file uses for_each", lambda c: tf_resource_has(c, "local_file", r"for_each")),
    t("output prefixes uses a for expression", lambda c: has(c, r'output\s+"prefixes".*?\bfor\s+\w+') or "use { for k, m in ... }"),
    t("dev.tfvars sets environments", lambda c: bool(re.search(r"environments\s*=", c.text("*.tfvars"))) or "write dev.tfvars"),
], [terraform_tool])


def _azurerm_provider(ctx: Ctx):
    blocks = [b for b in tf_blocks(tf_text(ctx)) if b.kind == "provider" and b.labels[:1] == ("azurerm",)]
    if not blocks:
        return 'add provider "azurerm"'
    body = blocks[0].body
    if "features" not in body:
        return "provider azurerm needs features {}"
    return True if re.search(r"subscription_id\s*=\s*var\.", body) else "subscription_id = var.subscription_id"


def _backend_partial(ctx: Ctx):
    for b in tf_blocks(tf_text(ctx)):
        if b.kind == "terraform":
            m = re.search(r'backend\s+"azurerm"\s*\{(.*?)\}', b.body, re.S)
            if m:
                return True if not m.group(1).strip() else "backend values must come from -backend-config, not the file"
    return 'add terraform { backend "azurerm" {} }'


def _azurerm_v4(ctx: Ctx):
    return True if re.search(r'hashicorp/azurerm"\s*\n?\s*version\s*=\s*"~>\s*4', tf_text(ctx)) else 'pin azurerm "~> 4.0"'


LAB05 = Spec("Terraform on Azure: network", [
    t("HCL syntax is valid", tf_syntax),
    t("azurerm pinned to ~> 4", _azurerm_v4),
    t("provider azurerm: features + subscription_id variable", _azurerm_provider),
    t("backend azurerm is partial (no values committed)", _backend_partial),
    t("variables: subscription_id, location, environment, subnets", lambda c: all(tf_declares(c, "variable", v) for v in ("subscription_id", "location", "environment", "subnets")) or "declare all four"),
    t("subnets variable is a map(string)", lambda c: has(c, r'variable\s+"subnets".*?type\s*=\s*map\(string\)') or "type = map(string)"),
    t("resource group + virtual network", lambda c: (tf_has_resource(c, "azurerm_resource_group") and tf_has_resource(c, "azurerm_virtual_network")) or "need both"),
    t("subnets created with for_each", lambda c: tf_resource_has(c, "azurerm_subnet", r"for_each")),
    t("NSG denies all inbound at priority 4096", lambda c: tf_resource_has(c, "azurerm_network_security_group", r'priority\s*=\s*4096.*?access\s*=\s*"Deny"|access\s*=\s*"Deny".*?priority\s*=\s*4096')),
    t("subnet-NSG association uses for_each", lambda c: tf_resource_has(c, "azurerm_subnet_network_security_group_association", r"for_each")),
    t("locals block with tags", lambda c: any(b.kind == "locals" and "tags" in b.body for b in tf_blocks(tf_text(c))) or "add locals tags"),
    t("an output exists", lambda c: any(b.kind == "output" for b in tf_blocks(tf_text(c))) or "add outputs.tf"),
    t("no hardcoded GUIDs", _no_guid),
    t(".gitignore keeps state out of Git", _gitignore),
], [terraform_tool])


# ------------------------------------------------------------------ Bicep labs

def _b(ctx: Ctx, pattern: str, msg: str):
    return True if re.search(pattern, bicep_text(ctx), re.S) else msg


def _bicepparam(ctx: Ctx):
    files = ctx.files("*.bicepparam")
    if not files:
        return "write main.bicepparam"
    return True if re.search(r"^\s*using\s+'", files[0].read_text(), re.M) else "bicepparam must start with using './main.bicep'"


def _all_params_described(ctx: Ctx):
    text = bicep_text(ctx)
    return True if len(re.findall(r"@description", text)) >= len(re.findall(r"^\s*param\s", text, re.M)) else "add @description to every param"


LAB06 = Spec("Bicep basics", [
    t("main.bicep exists", lambda c: c.exists("main.bicep") or "write work/main.bicep"),
    t("targetScope = 'resourceGroup'", lambda c: _b(c, r"targetScope\s*=\s*'resourceGroup'", "add targetScope")),
    t("location param defaults to resourceGroup().location", lambda c: _b(c, r"param\s+location\s+string\s*=\s*resourceGroup\(\)\.location", "param location string = resourceGroup().location")),
    t("namePrefix has @minLength and @maxLength", lambda c: _b(c, r"@minLength[\s\S]{0,160}?@maxLength[\s\S]{0,160}?param\s+namePrefix|@maxLength[\s\S]{0,160}?@minLength[\s\S]{0,160}?param\s+namePrefix", "decorate namePrefix")),
    t("skuName uses @allowed", lambda c: _b(c, r"@allowed[\s\S]{0,200}?param\s+skuName", "decorate skuName with @allowed")),
    t("every param has @description", _all_params_described),
    t("storage name built with uniqueString()", lambda c: _b(c, r"uniqueString\(", "use uniqueString(resourceGroup().id)")),
    t("storage account resource", lambda c: bicep_has_resource(c, "Microsoft.Storage/storageAccounts") or "add the storage account"),
    t("TLS 1.2 minimum", lambda c: bicep_resource_has(c, "Microsoft.Storage/storageAccounts", r"minimumTlsVersion:\s*'TLS1_2'")),
    t("blob public access off", lambda c: bicep_resource_has(c, "Microsoft.Storage/storageAccounts", r"allowBlobPublicAccess:\s*false")),
    t("HTTPS only", lambda c: bicep_resource_has(c, "Microsoft.Storage/storageAccounts", r"supportsHttpsTrafficOnly:\s*true")),
    t("at least two outputs", lambda c: len(re.findall(r"^\s*output\s+\w+", bicep_text(c), re.M)) >= 2 or "add id and name outputs"),
    t("main.bicepparam starts with using", _bicepparam),
], [bicep_tool])


def _lab07_template(ctx: Ctx) -> dict:
    for p in (ctx.root.parent / "given" / "template.json", ctx.root / "template.json"):
        if p.exists():
            return load_json(p)
    raise FileNotFoundError("template.json not found (see labs/07-arm-parameters/given)")


def _params(ctx: Ctx) -> dict:
    p = ctx.root / "parameters.json"
    if not p.exists():
        raise FileNotFoundError("write work/parameters.json")
    return load_json(p)


def _required_present(ctx: Ctx):
    template, params = _lab07_template(ctx)["parameters"], _params(ctx).get("parameters", {})
    required = [k for k, v in template.items() if "defaultValue" not in v]
    missing = [k for k in required if k not in params]
    return True if not missing else f"missing values for {missing}"


def _no_extra(ctx: Ctx):
    template, params = _lab07_template(ctx)["parameters"], _params(ctx).get("parameters", {})
    extra = [k for k in params if k not in template]
    return True if not extra else f"parameters not in the template: {extra}"


def _secure_uses_kv(ctx: Ctx):
    template, params = _lab07_template(ctx)["parameters"], _params(ctx).get("parameters", {})
    for name, spec in template.items():
        if spec.get("type", "").lower() == "securestring":
            entry = params.get(name, {})
            if "value" in entry:
                return f"{name} is a securestring: no plaintext value, use a Key Vault reference"
            kv = entry.get("reference", {}).get("keyVault", {})
            if not (kv.get("id", "").lower().find("/providers/microsoft.keyvault/vaults/") >= 0 and entry["reference"].get("secretName")):
                return f"{name}: reference.keyVault.id must be a vault resource ID and secretName is required"
    return True


def _deploy_text(ctx: Ctx) -> str:
    p = ctx.root / "deploy.sh"
    if not p.exists():
        raise FileNotFoundError("write work/deploy.sh")
    return p.read_text()


def _whatif_first(ctx: Ctx):
    s = _deploy_text(ctx)
    w, c = s.find("az deployment group what-if"), s.find("az deployment group create")
    if w < 0 or c < 0:
        return "deploy.sh needs both 'az deployment group what-if' and 'az deployment group create'"
    return True if w < c else "run what-if BEFORE create"


LAB07 = Spec("ARM parameters, Key Vault, what-if", [
    t("parameters.json is valid JSON with the parameters schema", lambda c: "deploymentParameters.json" in _params(c).get("$schema", "") or "use the deploymentParameters.json schema"),
    t("contentVersion present", lambda c: bool(_params(c).get("contentVersion")) or "add contentVersion"),
    t("every parameter without a default has a value", _required_present),
    t("no parameters the template doesn't declare", _no_extra),
    t("securestring uses a Key Vault reference, not a value", _secure_uses_kv),
    t("deploy.sh runs what-if before create", _whatif_first),
    t("deploy.sh passes --parameters @parameters.json", lambda c: _deploy_text(c).count("--parameters @parameters.json") >= 2 or "both commands need --parameters @parameters.json"),
    t("deploy.sh has no plaintext password", lambda c: not re.search(r"(?i)password\s*=\s*\S", _deploy_text(c)) or "remove the password from deploy.sh"),
], [lambda c: run_tool("deploy.sh syntax (bash -n)", "bash", ["-n", "deploy.sh"], c.root)])


def _modules(ctx: Ctx):
    mods = [b for b in bicep_blocks(ctx.text("main.bicep")) if b.kind == "module"]
    ok = len(mods) >= 2 and all("modules/" in b.labels[1] for b in mods)
    return True if ok else "main.bicep needs 2 module blocks pointing at modules/*.bicep"


LAB08 = Spec("Bicep modules: deny-by-default spoke", [
    t("modules/nsg.bicep and modules/vnet.bicep exist", lambda c: (c.exists("modules/nsg.bicep") and c.exists("modules/vnet.bicep")) or "create both modules"),
    t("NSG has deny-all inbound at priority 4096", lambda c: bool(re.search(r"priority:\s*4096[\s\S]{0,200}?access:\s*'Deny'|access:\s*'Deny'[\s\S]{0,200}?priority:\s*4096", c.text("modules/nsg.bicep"))) or "add deny rule at 4096"),
    t("NSG allows 443 from a parameter", lambda c: bool(re.search(r"destinationPortRange:\s*'443'", c.text("modules/nsg.bicep"))) and "allowedSourcePrefix" in c.text("modules/nsg.bicep") or "allow 443 from allowedSourcePrefix"),
    t("NSG module outputs its id", lambda c: bool(re.search(r"^\s*output\s+id\s", c.text("modules/nsg.bicep"), re.M)) or "output id"),
    t("VNet module takes a subnets array", lambda c: bool(re.search(r"param\s+subnets\s+array", c.text("modules/vnet.bicep"))) or "param subnets array"),
    t("VNet module builds subnets with a loop", lambda c: "[for " in c.text("modules/vnet.bicep") or "use [for s in subnets: {...}]"),
    t("VNet module attaches the NSG", lambda c: "networkSecurityGroup" in c.text("modules/vnet.bicep") or "attach networkSecurityGroup to each subnet"),
    t("main.bicep calls two modules", _modules),
    t("main.bicep passes the NSG output into the VNet module", lambda c: bool(re.search(r"\w+\.outputs\.id", c.text("main.bicep"))) or "use nsg.outputs.id"),
    t("main.bicep has targetScope", lambda c: "targetScope" in c.text("main.bicep") or "add targetScope"),
], [bicep_tool])


# ------------------------------------------------------------------ AKS labs

AKS = "azurerm_kubernetes_cluster"

LAB09 = Spec("AKS + ACR in Terraform, hardened", [
    t("HCL syntax is valid", tf_syntax),
    t("resource group, Log Analytics, ACR, AKS exist", lambda c: all(tf_has_resource(c, r) for r in ("azurerm_resource_group", "azurerm_log_analytics_workspace", "azurerm_container_registry", AKS)) or "need all four resources"),
    t("ACR admin account disabled", lambda c: tf_resource_has(c, "azurerm_container_registry", r"admin_enabled\s*=\s*false")),
    t("AKS is a private cluster", lambda c: tf_resource_has(c, AKS, r"private_cluster_enabled\s*=\s*true")),
    t("AKS local accounts disabled", lambda c: tf_resource_has(c, AKS, r"local_account_disabled\s*=\s*true")),
    t("AKS uses a system-assigned identity", lambda c: tf_resource_has(c, AKS, r'identity\s*\{[^}]*type\s*=\s*"SystemAssigned"')),
    t("Entra ID RBAC enabled with admin groups from a variable", lambda c: tf_resource_has(c, AKS, r"azure_active_directory_role_based_access_control\s*\{[^}]*azure_rbac_enabled\s*=\s*true[^}]*admin_group_object_ids\s*=\s*var\.|azure_active_directory_role_based_access_control\s*\{[^}]*admin_group_object_ids\s*=\s*var\.[^}]*azure_rbac_enabled\s*=\s*true")),
    t("Azure CNI overlay networking with a network policy", lambda c: tf_resource_has(c, AKS, r'network_plugin\s*=\s*"azure"') is True and tf_resource_has(c, AKS, r'network_plugin_mode\s*=\s*"overlay"') is True and tf_resource_has(c, AKS, r"network_policy\s*=") is True or "network_profile needs azure + overlay + network_policy"),
    t("oms_agent sends logs to the workspace", lambda c: tf_resource_has(c, AKS, r"oms_agent\s*\{[^}]*log_analytics_workspace_id")),
    t("AcrPull role assignment to the kubelet identity", lambda c: tf_resource_has(c, "azurerm_role_assignment", r'"AcrPull"') is True and tf_resource_has(c, "azurerm_role_assignment", r"kubelet_identity") is True or "role assignment: AcrPull + kubelet_identity"),
    t("admin_group_object_ids variable declared", lambda c: tf_declares(c, "variable", "admin_group_object_ids") or "declare the variable"),
    t("outputs for registry and cluster", lambda c: sum(1 for b in tf_blocks(tf_text(c)) if b.kind == "output") >= 2 or "add 2 outputs"),
    t("no hardcoded GUIDs", _no_guid),
], [terraform_tool])

ACR_PULL = "7f951dda-4ed3-4680-a7ca-43fe172d538d"
MC = "Microsoft.ContainerService/managedClusters"

LAB10 = Spec("AKS + ACR in Bicep, hardened", [
    t("main.bicep exists", lambda c: c.exists("main.bicep") or "write work/main.bicep"),
    t("Log Analytics workspace", lambda c: bicep_has_resource(c, "Microsoft.OperationalInsights/workspaces") or "add workspace"),
    t("ACR with admin user disabled", lambda c: bicep_resource_has(c, "Microsoft.ContainerRegistry/registries", r"adminUserEnabled:\s*false")),
    t("AKS with a system-assigned identity", lambda c: bicep_resource_has(c, MC, r"type:\s*'SystemAssigned'")),
    t("AKS local accounts disabled", lambda c: bicep_resource_has(c, MC, r"disableLocalAccounts:\s*true")),
    t("AKS is a private cluster", lambda c: bicep_resource_has(c, MC, r"enablePrivateCluster:\s*true")),
    t("Entra ID managed + Azure RBAC + admin groups param", lambda c: bicep_resource_has(c, MC, r"aadProfile:\s*\{[^}]*managed:\s*true") is True and bicep_resource_has(c, MC, r"enableAzureRBAC:\s*true") is True and bicep_resource_has(c, MC, r"adminGroupObjectIDs:\s*\w+") is True or "aadProfile needs managed, enableAzureRBAC, adminGroupObjectIDs"),
    t("overlay networking with a network policy", lambda c: bicep_resource_has(c, MC, r"networkPluginMode:\s*'overlay'") is True and bicep_resource_has(c, MC, r"networkPolicy:") is True or "overlay + networkPolicy"),
    t("omsagent addon wired to the workspace", lambda c: bicep_resource_has(c, MC, r"omsagent[\s\S]*logAnalyticsWorkspaceResourceID")),
    t("AcrPull role assignment, named with guid(), scoped to the registry", lambda c: bicep_resource_has(c, "Microsoft.Authorization/roleAssignments", r"scope:\s*\w+") is True and bicep_resource_has(c, "Microsoft.Authorization/roleAssignments", r"name:\s*guid\(") is True and ACR_PULL in bicep_text(c) or f"role assignment: scope, name: guid(...), role {ACR_PULL}"),
    t("kubelet identity is the principal", lambda c: "kubeletidentity" in bicep_text(c).lower() or "principalId: aks.properties.identityProfile.kubeletidentity.objectId"),
    t("adminGroupObjectIds is a parameter", lambda c: _b(c, r"param\s+adminGroupObjectIds\s+array", "param adminGroupObjectIds array")),
], [bicep_tool])


# ------------------------------------------------------------------ Kubernetes

def _docs(ctx: Ctx) -> list[dict]:
    docs = load_yaml_docs(ctx, "app.yaml")
    if not docs:
        raise FileNotFoundError("write work/app.yaml")
    return docs


def _kind(ctx: Ctx, kind: str) -> list[dict]:
    return [d for d in _docs(ctx) if d.get("kind") == kind]


def _dep(ctx: Ctx) -> dict:
    deps = _kind(ctx, "Deployment")
    if not deps:
        raise KeyError("no Deployment")
    return deps[0]


def _container(ctx: Ctx) -> dict:
    return _dep(ctx)["spec"]["template"]["spec"]["containers"][0]


def _pod(ctx: Ctx) -> dict:
    return _dep(ctx)["spec"]["template"]["spec"]


def _selector_ok(ctx: Ctx):
    labels = _dep(ctx)["spec"]["template"]["metadata"]["labels"]
    match = _dep(ctx)["spec"]["selector"]["matchLabels"]
    if not all(labels.get(k) == v for k, v in match.items()):
        return "Deployment selector does not match its pod labels"
    svcs = _kind(ctx, "Service")
    if not svcs:
        return "no Service"
    sel = svcs[0]["spec"]["selector"]
    return True if all(labels.get(k) == v for k, v in sel.items()) else "Service selector matches no pods"


def _secret_env(ctx: Ctx):
    envs = _container(ctx).get("env", [])
    if not any("secretKeyRef" in (e.get("valueFrom") or {}) for e in envs):
        return "API_KEY must come from a secretKeyRef"
    bad = [e["name"] for e in envs if re.search(r"KEY|PASSWORD|TOKEN|SECRET", e["name"]) and "value" in e]
    return True if not bad else f"literal secret in env: {bad}"


def _netpols(ctx: Ctx):
    pols = _kind(ctx, "NetworkPolicy")
    deny = [p for p in pols if p["spec"].get("podSelector") == {} and "Ingress" in p["spec"].get("policyTypes", []) and not p["spec"].get("ingress")]
    allow = [p for p in pols if p["spec"].get("ingress")]
    if not deny:
        return "need a default-deny ingress policy (podSelector: {}, no ingress rules)"
    return True if allow else "need an allow policy with an ingress rule"


def _role_narrow(ctx: Ctx):
    roles = _kind(ctx, "Role")
    if not roles:
        return "no Role"
    for r in roles:
        for rule in r["rules"]:
            if "*" in rule.get("resources", []) or "secrets" in rule.get("resources", []) or "*" in rule.get("verbs", []):
                return "Role is too broad (no secrets, no wildcards)"
    return True


def _rolebinding(ctx: Ctx):
    rbs = _kind(ctx, "RoleBinding")
    ok = rbs and any(s.get("kind") == "ServiceAccount" and s.get("name") == "web" for rb in rbs for s in rb["subjects"])
    return True if ok else "RoleBinding must bind ServiceAccount web"


def _k8s_schema(ctx: Ctx):
    try:
        import kubernetes_validate as kv
    except ImportError:
        return Result("objects validate against the Kubernetes 1.31 schema", None, "pip install kubernetes-validate")
    for d in _docs(ctx):
        try:
            kv.validate(d, "1.31", strict=True)
        except Exception as exc:  # noqa: BLE001
            return Result("objects validate against the Kubernetes 1.31 schema", False, f"{d.get('kind')}/{d.get('metadata', {}).get('name')}: {str(exc)[:200]}")
    return Result("objects validate against the Kubernetes 1.31 schema", True)


LAB11 = Spec("Kubernetes manifests from scratch", [
    t("app.yaml has all required kinds", lambda c: not (set("ServiceAccount ConfigMap Deployment Service PodDisruptionBudget NetworkPolicy Role RoleBinding".split()) - {d.get("kind") for d in _docs(c)}) or f"missing kinds: {sorted(set('ServiceAccount ConfigMap Deployment Service PodDisruptionBudget NetworkPolicy Role RoleBinding'.split()) - {d.get('kind') for d in _docs(c)})}"),
    t("Deployment: 2+ replicas", lambda c: _dep(c)["spec"].get("replicas", 1) >= 2 or "replicas >= 2"),
    t("selectors match pod labels (Deployment and Service)", _selector_ok),
    t("pod runs non-root with seccomp RuntimeDefault", lambda c: (_pod(c).get("securityContext", {}).get("runAsNonRoot") is True and _pod(c)["securityContext"].get("seccompProfile", {}).get("type") == "RuntimeDefault") or "pod securityContext: runAsNonRoot + seccomp RuntimeDefault"),
    t("container hardened (no priv-esc, read-only root, drop ALL)", lambda c: (lambda s: s.get("allowPrivilegeEscalation") is False and s.get("readOnlyRootFilesystem") is True and "ALL" in s.get("capabilities", {}).get("drop", []))(_container(c).get("securityContext", {})) or "container securityContext incomplete"),
    t("liveness and readiness probes", lambda c: all(k in _container(c) for k in ("livenessProbe", "readinessProbe")) or "add both probes"),
    t("requests and limits (cpu + memory)", lambda c: (lambda r: all(r.get(s, {}).get(k) for s in ("requests", "limits") for k in ("cpu", "memory")))(_container(c).get("resources", {})) or "need cpu+memory requests and limits"),
    t("named container port", lambda c: all("name" in p for p in _container(c).get("ports", [])) and bool(_container(c).get("ports")) or "name the port"),
    t("image pinned (no latest)", lambda c: (":" in _container(c)["image"] and not _container(c)["image"].endswith(":latest")) or "pin the image"),
    t("config from ConfigMap and secret from secretKeyRef", lambda c: (any("configMapRef" in e for e in _container(c).get("envFrom", [])) and _secret_env(c) is True) or _secret_env(c)),
    t("ServiceAccount does not auto-mount a token", lambda c: _kind(c, "ServiceAccount")[0].get("automountServiceAccountToken") is False or "automountServiceAccountToken: false"),
    t("NetworkPolicies: default deny + explicit allow", _netpols),
    t("Role is narrow and bound to the ServiceAccount", lambda c: _role_narrow(c) is True and _rolebinding(c) is True or (_role_narrow(c) if _role_narrow(c) is not True else _rolebinding(c))),
], [_k8s_schema])


# ------------------------------------------------------------------ AVD

AVD = "azurerm_virtual_desktop_"

LAB12 = Spec("Azure Virtual Desktop in Terraform", [
    t("HCL syntax is valid", tf_syntax),
    t("azurerm pinned to ~> 4", _azurerm_v4),
    t("variables: subscription_id, location, users_group_object_id", lambda c: all(tf_declares(c, "variable", v) for v in ("subscription_id", "location", "users_group_object_id")) or "declare all three"),
    t("host pool is Pooled with BreadthFirst", lambda c: tf_resource_has(c, AVD + "host_pool", r'type\s*=\s*"Pooled"') is True and tf_resource_has(c, AVD + "host_pool", r'load_balancer_type\s*=\s*"BreadthFirst"') is True or "Pooled + BreadthFirst"),
    t("host pool sets maximum_sessions_allowed", lambda c: tf_resource_has(c, AVD + "host_pool", r"maximum_sessions_allowed\s*=\s*\d+")),
    t("Entra ID sign-in in custom_rdp_properties", lambda c: tf_resource_has(c, AVD + "host_pool", r"enablerdsaadauth:i:1")),
    t("registration info with an expiration date", lambda c: tf_resource_has(c, AVD + "host_pool_registration_info", r"expiration_date\s*=")),
    t("Desktop application group on the host pool", lambda c: tf_resource_has(c, AVD + "application_group", r'type\s*=\s*"Desktop"') is True and tf_resource_has(c, AVD + "application_group", r"host_pool_id\s*=") is True or "Desktop app group with host_pool_id"),
    t("workspace and workspace-application group association", lambda c: (tf_has_resource(c, AVD + "workspace") and tf_has_resource(c, AVD + "workspace_application_group_association")) or "need both"),
    t("Desktop Virtualization User role on the app group", lambda c: tf_resource_has(c, "azurerm_role_assignment", r'"Desktop Virtualization User"') is True and tf_resource_has(c, "azurerm_role_assignment", r"var\.users_group_object_id") is True or "role assignment for users_group_object_id"),
    t("no hardcoded GUIDs", _no_guid),
], [terraform_tool])


# ------------------------------------------------------------------ Troubleshooting drills

def _drill_tf_vars(ctx: Ctx):
    text = tf_text(ctx)
    used = set(re.findall(r"\bvar\.(\w+)", text))
    declared = {b.labels[0] for b in tf_blocks(text) if b.kind == "variable"}
    return True if not (used - declared) else f"variables used but never declared: {sorted(used - declared)}"


def _drill_bicep_name(ctx: Ctx):
    m = re.search(r"\n\s*name:\s*(.+)", bicep_text(ctx))
    return True if m and "uniqueString" in m.group(1) else "the storage account name must be globally unique: use uniqueString()"


def _drill_image(ctx: Ctx):
    img = _container_any(ctx)["image"]
    return True if ":" in img and not img.endswith(":latest") else f"image {img!r} is not pinned"


def _container_any(ctx: Ctx) -> dict:
    deps = [d for d in load_yaml_docs(ctx, "app.yaml") if d.get("kind") == "Deployment"]
    if not deps:
        raise FileNotFoundError("work/app.yaml missing")
    return deps[0]["spec"]["template"]["spec"]["containers"][0]


def _drill_limits(ctx: Ctx):
    lim = _container_any(ctx).get("resources", {}).get("limits", {})
    return True if lim.get("cpu") and lim.get("memory") else "add resource limits"


def _drill_selector(ctx: Ctx):
    docs = load_yaml_docs(ctx, "app.yaml")
    dep = next(d for d in docs if d["kind"] == "Deployment")
    svc = next(d for d in docs if d["kind"] == "Service")
    labels = dep["spec"]["template"]["metadata"]["labels"]
    return True if all(labels.get(k) == v for k, v in svc["spec"]["selector"].items()) else "Service selector matches no pods (it would have zero endpoints)"


LAB13 = Spec("Troubleshooting drills", [
    t("Dockerfile: base image pinned", _pinned),
    t("Dockerfile: no ADD from a URL", _no_remote_add),
    t("Dockerfile: runs as non-root", _nonroot),
    t("main.tf: provider has features {}", lambda c: any(b.kind == "provider" and "features" in b.body for b in tf_blocks(tf_text(c))) or "add features {}"),
    t("main.tf: every var.* is declared", _drill_tf_vars),
    t("main.tf: no hardcoded subscription GUID", _no_guid),
    t("main.bicep: unique storage account name", _drill_bicep_name),
    t("main.bicep: TLS 1.2", lambda c: _b(c, r"minimumTlsVersion:\s*'TLS1_2'", "minimumTlsVersion must be TLS1_2")),
    t("main.bicep: blob public access off", lambda c: _b(c, r"allowBlobPublicAccess:\s*false", "allowBlobPublicAccess must be false")),
    t("app.yaml: image pinned", _drill_image),
    t("app.yaml: resource limits", _drill_limits),
    t("app.yaml: Service selector matches pods", _drill_selector),
], [bicep_tool])


# ------------------------------------------------------------------ Capstone

def _sub(ctx: Ctx, name: str) -> Ctx:
    return Ctx(ctx.root / name)


def _cap_tf(ctx: Ctx, rtype: str):
    return True if tf_has_resource(_sub(ctx, "terraform"), rtype) else f"terraform/ is missing {rtype}"


LAB14 = Spec("Capstone enclave", [
    t("terraform/: network (rg, vnet, subnet, NSG)", lambda c: all(tf_has_resource(_sub(c, "terraform"), r) for r in ("azurerm_resource_group", "azurerm_virtual_network", "azurerm_subnet", "azurerm_network_security_group")) or "need rg, vnet, subnet, nsg"),
    t("terraform/: NSG denies all inbound", lambda c: tf_resource_has(_sub(c, "terraform"), "azurerm_network_security_group", r"4096")),
    t("terraform/: Log Analytics + ACR", lambda c: (_cap_tf(c, "azurerm_log_analytics_workspace") is True and _cap_tf(c, "azurerm_container_registry") is True) or "need both"),
    t("terraform/: hardened AKS (private, no local accounts, Entra RBAC)", lambda c: tf_resource_has(_sub(c, "terraform"), AKS, r"private_cluster_enabled\s*=\s*true") is True and tf_resource_has(_sub(c, "terraform"), AKS, r"local_account_disabled\s*=\s*true") is True and tf_resource_has(_sub(c, "terraform"), AKS, r"azure_rbac_enabled\s*=\s*true") is True or "AKS must be private, local accounts off, Azure RBAC on"),
    t("terraform/: Key Vault with RBAC auth and purge protection", lambda c: tf_resource_has(_sub(c, "terraform"), "azurerm_key_vault", r"(rbac_authorization_enabled|enable_rbac_authorization)\s*=\s*true") is True and tf_resource_has(_sub(c, "terraform"), "azurerm_key_vault", r"purge_protection_enabled\s*=\s*true") is True or "Key Vault: RBAC authorization + purge protection"),
    t("terraform/: AVD host pool", lambda c: _cap_tf(c, "azurerm_virtual_desktop_host_pool")),
    t("terraform/: no hardcoded GUIDs", lambda c: _no_guid(_sub(c, "terraform"))),
    t("bicep/: main.bicep with a module and an NSG", lambda c: bool(re.search(r"^\s*module\s", bicep_text(_sub(c, "bicep")), re.M)) and bicep_has_resource(_sub(c, "bicep"), "Microsoft.Network/networkSecurityGroups") or "bicep/ needs a module and an NSG resource"),
    t("docker/: Dockerfile runs non-root", lambda c: _nonroot(_sub(c, "docker"))),
    t("k8s/: a Deployment with limits and probes", lambda c: any(d.get("kind") == "Deployment" and "resources" in d["spec"]["template"]["spec"]["containers"][0] and "livenessProbe" in d["spec"]["template"]["spec"]["containers"][0] for d in load_yaml_docs(_sub(c, "k8s"), "*.yaml", "*.yml")) or "need a Deployment with resources + livenessProbe"),
    t("README.md covers architecture, cost and teardown", lambda c: all(w in (c.root / "README.md").read_text().lower() for w in ("architecture", "cost", "destroy")) or "README needs 'architecture', 'cost' and 'destroy'"),
], [lambda c: bicep_tool(_sub(c, "bicep")), lambda c: terraform_tool(_sub(c, "terraform"))])


LABS: dict[str, tuple[str, Spec]] = {
    "01": ("01-dockerfile", LAB01), "02": ("02-compose", LAB02), "03": ("03-terraform-state", LAB03),
    "04": ("04-terraform-modules", LAB04), "05": ("05-terraform-azure-network", LAB05), "06": ("06-bicep-basics", LAB06),
    "07": ("07-arm-parameters", LAB07), "08": ("08-bicep-enclave-network", LAB08), "09": ("09-aks-terraform", LAB09),
    "10": ("10-aks-bicep", LAB10), "11": ("11-k8s-from-scratch", LAB11), "12": ("12-avd-vdi", LAB12),
    "13": ("13-troubleshooting-drills", LAB13), "14": ("14-capstone-enclave", LAB14),
}


# Stricter, optional checks: they run only when the tool is installed.
for _lab in ("03", "04"):
    LABS[_lab][1].tools.append(terraform_plan_tool)
for _lab in ("01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"):
    LABS[_lab][1].tools.append(checkov_tool(CHECKOV_SKIPS.get(_lab)))
