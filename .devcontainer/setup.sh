#!/usr/bin/env bash
# Runs once when the Codespace is created.
set -e
pip install -r requirements-dev.txt
curl -fsSL https://kind.sigs.k8s.io/dl/v0.24.0/kind-linux-amd64 -o /tmp/kind && sudo install /tmp/kind /usr/local/bin/kind
curl -fsSL https://ollama.com/install.sh | sh || echo "Ollama install failed; run it manually (modules/02-local-llm)."
python -m pytest -q || true
echo "Ready. Start with: make verify-00  and  python -m tutor modules"
