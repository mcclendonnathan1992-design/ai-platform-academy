.PHONY: test lint setup up down kind-up kind-down tutor lab-check reset-lab break-lab reveal drill drill-check drill-stats drill-list clean slim-model install-checkov az-preflight az-sweep az-sweep-delete
PY ?= python3

setup:
	$(PY) -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt
test:
	$(PY) -m pytest -q
lint:
	yamllint -c .yamllint k8s gitops .github platform/backstage
up:
	docker compose up -d --build
down:
	docker compose down
kind-up:
	kind create cluster --config k8s/kind-config.yaml
kind-down:
	kind delete cluster --name ai-lab
tutor:
	$(PY) -m tutor modules
verify-%:
	$(PY) scripts/verify.py $*
lab-check:
	$(PY) scripts/lab_check.py $(LAB) $(WHICH)

# ---- practice tools
reset-lab:
	$(PY) scripts/labtool.py reset $(LAB)
break-lab:
	$(PY) scripts/labtool.py break $(LAB) $(ARGS)
reveal:
	$(PY) scripts/labtool.py reveal $(LAB)
drill:
	$(PY) scripts/drill.py start $(ID)
drill-check:
	$(PY) scripts/drill.py check
drill-stats:
	$(PY) scripts/drill.py stats
drill-list:
	$(PY) scripts/drill.py list
clean:
	bash scripts/clean.sh
slim-model:
	ollama pull qwen2.5:0.5b
	@echo "Use it:  TUTOR_MODEL=qwen2.5:0.5b make tutor   (smaller and faster; answers are weaker)"
	@echo "Free space: ollama rm <model you no longer use>   (see: ollama list)"
az-preflight:
	$(PY) scripts/az_tool.py preflight
az-sweep:
	$(PY) scripts/az_tool.py sweep
az-sweep-delete:
	$(PY) scripts/az_tool.py sweep --delete
install-checkov:
	pip install -r requirements-labs.txt
	@echo "Done. make lab-check now also runs the security policy scan."
