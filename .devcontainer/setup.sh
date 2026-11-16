#!/usr/bin/env bash
# Best-effort setup: never fail the Codespace build.
sudo rm -f /etc/apt/sources.list.d/yarn.list
pip install -r requirements-dev.txt || true
# One shared Terraform provider cache: every lab reuses the same download instead of copying ~100 MB each.
mkdir -p "$HOME/.terraform.d/plugin-cache"
grep -q TF_PLUGIN_CACHE_DIR "$HOME/.bashrc" 2>/dev/null || echo 'export TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"' >> "$HOME/.bashrc"
# Azure CLI (for the real-Azure labs)
command -v az >/dev/null || (curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash) || echo "Install the Azure CLI later (see labs/AZURE.md)."
if ! command -v terraform >/dev/null; then
  VER=1.9.8
  curl -fsSL -o /tmp/tf.zip https://releases.hashicorp.com/terraform/${VER}/terraform_${VER}_linux_amd64.zip \
    && unzip -o /tmp/tf.zip -d /tmp && sudo install /tmp/terraform /usr/local/bin/terraform \
    || echo "Install Terraform manually later."
fi
if ! command -v kind >/dev/null; then
  curl -fsSL https://kind.sigs.k8s.io/dl/v0.24.0/kind-linux-amd64 -o /tmp/kind && sudo install /tmp/kind /usr/local/bin/kind || true
fi
if ! command -v ollama >/dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh || echo "Install Ollama manually later."
fi
command -v az >/dev/null && (az bicep install || echo "Run 'az bicep install' later.")
python -m pytest -q || true
echo "Ready: make verify-00"
exit 0
