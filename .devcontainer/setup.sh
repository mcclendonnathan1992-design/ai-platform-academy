#!/usr/bin/env bash
# Best-effort setup: never fail the Codespace build.
sudo rm -f /etc/apt/sources.list.d/yarn.list
pip install -r requirements-dev.txt || true
if ! command -v terraform >/dev/null; then
  wget -qO- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp.gpg
  echo "deb [signed-by=/usr/share/keyrings/hashicorp.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
  sudo apt-get update && sudo apt-get install -y terraform || echo "Install Terraform manually later."
fi
if ! command -v kind >/dev/null; then
  curl -fsSL https://kind.sigs.k8s.io/dl/v0.24.0/kind-linux-amd64 -o /tmp/kind && sudo install /tmp/kind /usr/local/bin/kind || true
fi
if ! command -v ollama >/dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh || echo "Install Ollama manually later."
fi
python -m pytest -q || true
echo "Ready: make verify-00"
exit 0
