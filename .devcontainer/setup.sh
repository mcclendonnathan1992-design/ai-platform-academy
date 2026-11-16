#!/usr/bin/env bash
# Best-effort setup: never fail the Codespace build.
pip install -r requirements-dev.txt || true
if ! command -v kind >/dev/null; then
  curl -fsSL https://kind.sigs.k8s.io/dl/v0.24.0/kind-linux-amd64 -o /tmp/kind && sudo install /tmp/kind /usr/local/bin/kind || true
fi
if ! command -v ollama >/dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh || echo "Install Ollama manually later."
fi
python -m pytest -q || true
echo "Ready: make verify-00"
exit 0
