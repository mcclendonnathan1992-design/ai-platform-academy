#!/usr/bin/env bash
# Free disk space safely. Never touches your work/ files, Git, or Docker volumes (your data).
cd "$(dirname "$0")/.." || exit 1
echo "== Disk before"; df -h "$PWD" | tail -1
echo
if docker info >/dev/null 2>&1; then
  echo "== Docker: pruning build cache, dangling images, stopped containers"
  docker builder prune -af 2>&1 | tail -1
  docker image prune -f 2>&1 | tail -1
  docker container prune -f 2>&1 | tail -1
else
  echo "(docker is not running here, skipping)"
fi
echo
echo "== Removing Terraform working folders (.terraform) and Python caches in this repo"
find . -path ./.git -prune -o -type d -name .terraform -print -exec rm -rf {} + 2>/dev/null | sed 's/^/  removed /'
find . -path ./.git -prune -o -type d \( -name __pycache__ -o -name .pytest_cache \) -exec rm -rf {} + 2>/dev/null
echo
echo "== Disk after"; df -h "$PWD" | tail -1
echo
docker info >/dev/null 2>&1 && { echo "== What Docker still holds"; docker system df 2>/dev/null; echo; }
if command -v ollama >/dev/null 2>&1; then
  echo "== Ollama models (each is 0.4-2 GB). Remove ones you do not use with: ollama rm <name>"
  ollama list 2>/dev/null
fi
[ -n "${TF_PLUGIN_CACHE_DIR:-}" ] && echo "Terraform provider cache (shared by all labs): $(du -sh "$TF_PLUGIN_CACHE_DIR" 2>/dev/null | cut -f1)"
