# Yammic local demo platform — one-command stack.
# Owner: DevOps (CEL-1773). See ops/RUNBOOK.md.
#
#   make reset   drop volumes, start Postgres + HAPI FHIR, seed
#   make demo    start everything (infra, seed if empty, backend, web) and health-check it
#   make health  check Postgres, FHIR, backend, web
#
# Everything is local: synthetic data only, no hosting, no paid APIs.

SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE ?= docker compose
UV ?= uv
PY ?= python3

FLUTTER ?= $(shell command -v flutter 2>/dev/null)
ifeq ($(strip $(FLUTTER)),)
FLUTTER := $(HOME)/flutter/bin/flutter
endif

PG_PORT ?= 5433
FHIR_PORT ?= 8090
BACKEND_PORT ?= 8000
WEB_PORT ?= 8080
STRICT ?= 0

FHIR_LOCAL := http://127.0.0.1:$(FHIR_PORT)
BACKEND_LOCAL := http://127.0.0.1:$(BACKEND_PORT)
WEB_LOCAL := http://127.0.0.1:$(WEB_PORT)

LOG_DIR := ops/logs
RUN_DIR := ops/run
BUILD_DIR := app/build/web

.PHONY: help up down seed reset backend web demo stop health psql fhir

help:
	@echo "Yammic demo platform (local only)"
	@echo ""
	@echo "  make up        start Postgres 16 (:$(PG_PORT)) and HAPI FHIR R4 (:$(FHIR_PORT)); wait for healthy"
	@echo "  make down      stop containers, keep the data volume"
	@echo "  make seed      load synthetic data (fhir-seed/load.py and backend seed, when present)"
	@echo "  make reset     remove volumes, up, seed   (clean slate)"
	@echo "  make backend   run the FastAPI backend with reload on :$(BACKEND_PORT) (foreground)"
	@echo "  make web       build Flutter web and serve it on :$(WEB_PORT) (foreground)"
	@echo "  make demo      up + seed if empty + backend + web in the background, then health --strict"
	@echo "  make health    check Postgres, FHIR /fhir/metadata, backend /health, web (STRICT=1 to require all)"
	@echo "  make stop      stop backend + web processes and containers"
	@echo "  make psql      open psql on the yammic database"
	@echo ""
	@echo "Logs: $(LOG_DIR)/  PIDs: $(RUN_DIR)/"

# ---------------------------------------------------------------- infrastructure
up:
	@command -v docker >/dev/null || { echo "ERROR: docker not found in PATH"; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "ERROR: Docker daemon not reachable. Start Docker Desktop, then retry (ops/RUNBOOK.md)."; exit 1; }
	@echo "== up: starting Postgres 16 and HAPI FHIR R4 (waiting for healthy)"
	@$(COMPOSE) up -d --wait --wait-timeout 420
	@echo "== up: postgres 127.0.0.1:$(PG_PORT)  |  HAPI FHIR $(FHIR_LOCAL)/fhir/metadata"

down:
	@$(COMPOSE) down --remove-orphans
	@echo "== down: containers removed; data volume yammic-postgres-data kept"

seed:
	@mkdir -p $(LOG_DIR)
	@if [ -f fhir-seed/load.py ]; then \
		echo "== seed: FHIR (fhir-seed/load.py)"; \
		$(UV) run --project backend python fhir-seed/load.py || { echo "ERROR: FHIR seed failed"; exit 1; }; \
	else \
		echo "== seed: skip FHIR — fhir-seed/load.py not present yet (workstream W3)"; \
	fi
	@if [ -f backend/app/seed.py ]; then \
		n=$$($(COMPOSE) exec -T postgres psql -U yammic -d yammic -tAc "SELECT count(*) FROM study" 2>/dev/null | tr -d '[:space:]'); \
		if [ -n "$$n" ] && [ "$$n" != "0" ]; then \
			echo "== seed: skip backend — database already has $$n study row(s) (use make reset for a clean slate)"; \
		else \
			echo "== seed: backend (python -m app.seed)"; \
			( cd backend && $(UV) run python -m app.seed ) || { echo "ERROR: backend seed failed"; exit 1; }; \
		fi; \
	else \
		echo "== seed: skip backend — backend/app/seed.py not present yet (workstream W1)"; \
	fi

reset:
	@echo "== reset: removing containers and data volume"
	@$(COMPOSE) down -v --remove-orphans
	@$(MAKE) --no-print-directory up
	@$(MAKE) --no-print-directory seed

# ---------------------------------------------------------------- app processes
backend:
	@if [ ! -f backend/app/main.py ]; then echo "ERROR: backend not present yet (workstream W1)"; exit 1; fi
	@echo "== backend: uvicorn on $(BACKEND_LOCAL)"
	cd backend && exec $(UV) run uvicorn app.main:app --host 127.0.0.1 --port $(BACKEND_PORT) --reload

web:
	@if [ ! -x "$(FLUTTER)" ]; then echo "ERROR: flutter not found (looked at '$(FLUTTER)'; set FLUTTER=...)"; exit 1; fi
	@echo "== web: flutter build web --release"
	cd app && "$(FLUTTER)" build web --release
	@echo "== web: serving $(BUILD_DIR) on $(WEB_LOCAL)"
	exec $(PY) -m http.server $(WEB_PORT) --bind 127.0.0.1 --directory $(CURDIR)/$(BUILD_DIR)

# ---------------------------------------------------------------- full demo
demo: up
	@mkdir -p $(LOG_DIR) $(RUN_DIR)
	@$(MAKE) --no-print-directory _seed-if-empty
	@$(MAKE) --no-print-directory _start-backend
	@$(MAKE) --no-print-directory _start-web
	@echo ""
	@STRICT=1 ops/health.sh --strict
	@echo ""
	@echo "Demo is up: web $(WEB_LOCAL)  |  API $(BACKEND_LOCAL)/docs  |  FHIR $(FHIR_LOCAL)/fhir/metadata"
	@echo "Logs: $(LOG_DIR)/backend.log $(LOG_DIR)/web.log (web build: $(LOG_DIR)/web-build.log)"

_seed-if-empty:
	@backend_n=$$($(COMPOSE) exec -T postgres psql -U yammic -d yammic -tAc "SELECT count(*) FROM study" 2>/dev/null | tr -d '[:space:]'); \
	fhir_n=$$(timeout 10 curl -fsS "$(FHIR_LOCAL)/Patient?_summary=count" 2>/dev/null | $(PY) -c "import sys,json;print(json.load(sys.stdin).get('total',0))" 2>/dev/null); \
	backend_n=$${backend_n:-0}; fhir_n=$${fhir_n:-0}; \
	if [ "$$backend_n" != "0" ] && [ "$$fhir_n" != "0" ]; then \
		echo "== demo: data present (backend $$backend_n studies, FHIR $$fhir_n patients) — not seeding"; \
	else \
		echo "== demo: seeding (backend $$backend_n studies, FHIR $$fhir_n patients)"; \
		$(MAKE) --no-print-directory seed; \
	fi

_start-backend:
	@mkdir -p $(LOG_DIR) $(RUN_DIR)
	@if timeout 3 curl -fsS "$(BACKEND_LOCAL)/health" >/dev/null 2>&1; then \
		echo "== demo: backend already answering on :$(BACKEND_PORT)"; \
	elif [ -f $(RUN_DIR)/backend.pid ] && kill -0 $$(cat $(RUN_DIR)/backend.pid) 2>/dev/null; then \
		echo "== demo: backend already starting (pid $$(cat $(RUN_DIR)/backend.pid))"; \
	else \
		if [ ! -f backend/app/main.py ]; then echo "ERROR: backend/app/main.py not present yet (workstream W1)"; exit 1; fi; \
		echo "== demo: starting backend, log $(LOG_DIR)/backend.log"; \
		( cd backend && exec nohup $(UV) run uvicorn app.main:app --host 127.0.0.1 --port $(BACKEND_PORT) ) \
			> "$(CURDIR)/$(LOG_DIR)/backend.log" 2>&1 & echo $$! > "$(CURDIR)/$(RUN_DIR)/backend.pid"; \
		for i in $$(seq 1 40); do \
			if timeout 2 curl -fsS "$(BACKEND_LOCAL)/health" >/dev/null 2>&1; then echo "== demo: backend ready (pid $$(cat $(CURDIR)/$(RUN_DIR)/backend.pid))"; exit 0; fi; \
			sleep 1; \
		done; \
		echo "ERROR: backend did not become ready in 40 s; see $(LOG_DIR)/backend.log"; exit 1; \
	fi

_start-web:
	@mkdir -p $(LOG_DIR) $(RUN_DIR)
	@if timeout 3 curl -fsS "$(WEB_LOCAL)/" >/dev/null 2>&1; then \
		echo "== demo: web already answering on :$(WEB_PORT)"; \
	elif [ -f $(RUN_DIR)/web.pid ] && kill -0 $$(cat $(RUN_DIR)/web.pid) 2>/dev/null; then \
		echo "== demo: web server already running (pid $$(cat $(RUN_DIR)/web.pid))"; \
	else \
		need=0; \
		[ -f $(BUILD_DIR)/index.html ] || need=1; \
		if [ -n "$$(find app/lib app/web app/assets app/pubspec.yaml -newer $(BUILD_DIR)/index.html -print -quit 2>/dev/null)" ]; then need=1; fi; \
		if [ "$$need" = "1" ]; then \
			if [ ! -x "$(FLUTTER)" ]; then echo "ERROR: flutter not found (looked at '$(FLUTTER)'); cannot build web (set FLUTTER=...)"; exit 1; fi; \
			echo "== demo: building Flutter web, log $(LOG_DIR)/web-build.log"; \
			( cd app && "$(FLUTTER)" build web --release ) > "$(CURDIR)/$(LOG_DIR)/web-build.log" 2>&1 \
				|| { echo "ERROR: flutter build failed — see $(LOG_DIR)/web-build.log"; exit 1; }; \
		else \
			echo "== demo: reusing existing web build (sources unchanged)"; \
		fi; \
		echo "== demo: serving $(BUILD_DIR) on :$(WEB_PORT), log $(LOG_DIR)/web.log"; \
		( cd $(BUILD_DIR) && exec nohup $(PY) -m http.server $(WEB_PORT) --bind 127.0.0.1 ) \
			> "$(CURDIR)/$(LOG_DIR)/web.log" 2>&1 & echo $$! > "$(CURDIR)/$(RUN_DIR)/web.pid"; \
		for i in $$(seq 1 20); do \
			if timeout 2 curl -fsS "$(WEB_LOCAL)/" >/dev/null 2>&1; then echo "== demo: web ready (pid $$(cat $(CURDIR)/$(RUN_DIR)/web.pid))"; exit 0; fi; \
			sleep 1; \
		done; \
		echo "ERROR: web server did not answer in 20 s; see $(LOG_DIR)/web.log"; exit 1; \
	fi

stop:
	@if [ -f $(RUN_DIR)/web.pid ]; then kill $$(cat $(RUN_DIR)/web.pid) 2>/dev/null || true; rm -f $(RUN_DIR)/web.pid; echo "== stop: web"; fi
	@if [ -f $(RUN_DIR)/backend.pid ]; then kill $$(cat $(RUN_DIR)/backend.pid) 2>/dev/null || true; rm -f $(RUN_DIR)/backend.pid; echo "== stop: backend"; fi
	@pkill -f "uvicorn app.main:app.*--port $(BACKEND_PORT)" 2>/dev/null || true
	@pkill -f "http.server $(WEB_PORT)" 2>/dev/null || true
	@$(COMPOSE) down --remove-orphans
	@echo "== stop: app processes and containers stopped; data volume kept"

# ---------------------------------------------------------------- checks / misc
health:
	@if [ "$(STRICT)" = "1" ]; then ops/health.sh --strict; else ops/health.sh; fi

psql:
	@$(COMPOSE) exec postgres psql -U yammic -d yammic

fhir:
	@curl -fsS $(FHIR_LOCAL)/fhir/metadata | $(PY) -m json.tool | head -40
