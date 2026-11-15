.PHONY: test lint setup up down kind-up kind-down tutor $(addprefix verify-,00 01 02 03 04 05 06 07 08 09)
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
