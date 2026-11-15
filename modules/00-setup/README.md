# 00 · Setup

**Goal:** a working toolbox. About 2 hours.

## Install
Windows: use WSL2 (Ubuntu) and install tools inside it; or `winget install` Docker Desktop, Git, Python, Kubernetes.kind, Kubernetes.kubectl, Helm.Helm, Hashicorp.Terraform, Ollama.Ollama. macOS/Linux: use your package manager.

RAM: 8 GB works with `llama3.2:1b` and a 1-node kind cluster; 16 GB is comfortable.

## Lab
1. `python -m venv .venv`, activate, `pip install -r requirements-dev.txt`
2. `python -m pytest -q` → green (4 xfails are intentional)
3. `make verify-00` → shows which tools are still missing

## Checkpoint
`make verify-00`, then `python -m tutor done 00`.
