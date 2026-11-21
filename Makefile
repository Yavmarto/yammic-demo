# Yammic local demo platform — one-command stack.
# Owner: DevOps (CEL-1773). See ops/RUNBOOK.md.
#
#   make reset   drop volumes, start Postgres + HAPI FHIR, seed
#   make demo    start everything (infra, seed if empty, backend, AI worker, web) and health-check it
#   make health  check Postgres, FHIR, backend, AI worker, web
#
# Everything is local: synthetic data only, no hosting, no paid APIs.

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Per-machine secrets (JWT_SECRET, PSEUDONYM_KEY, AUDIT_KEY, DB passwords): generated once, git-ignored.
$(shell ops/ensure-env.sh >&2)
include ops/.env.local
export

COMPOSE ?= docker compose
UV ?= uv
PY ?= python3

FLUTTER ?= $(shell command -v flutter 2>/dev/null)
ifeq ($(strip $(FLUTTER)),)
FLUTTER := $(HOME)/flutter/bin/flutter
endif

# v4 defaults. The frozen v3 stack runs next door on 5433/8090/8000/8080 and must
# stay untouched; every port below can be overridden from the environment.
PG_PORT ?= 5434
FHIR_PORT ?= 8091
FHIR2_PORT ?= 8092
BACKEND_PORT ?= 8001
WEB_PORT ?= 8081
STRICT ?= 0
AI_PROVIDER ?= auto
# Start the worker through the service entry point, not `-m app.ai`. The frozen
# v3 ops/ai-workers.sh matches every `python -m app.ai` process; this form keeps
# v4's worker invisible to it, so v3's make demo/stop do not touch v4 and vice versa.
AI_RUN := python -c 'import sys; from app.ai.service import main; sys.exit(main(sys.argv[1:]))'

# FHIR seed sets, one per hospital. Task C added `--hospital N` and the
# `fhir-seed/hospital2/<set>/` layout; detect the flag so this Makefile still
# works on a tree where that change has not landed. Hospital 2 is skipped until
# its data directory exists.
FHIR_HAS_HOSPITAL_FLAG := $(shell python3 fhir-seed/load.py --help 2>/dev/null | grep -q -- '--hospital' && echo yes || echo no)
FHIR_H1_SET ?= baseline
FHIR_H2_SET ?= baseline
FHIR_H1_ARRIVALS ?= arrivals
FHIR_H2_ARRIVALS ?= arrivals

# Backend runs as the least-privilege role; seed/migrations run as the owner.
ADMIN_URL := postgresql+psycopg://yammic:yammic@localhost:$(PG_PORT)/yammic
export DATABASE_URL ?= postgresql+psycopg://yammic_app:$(APP_DB_PASSWORD)@localhost:$(PG_PORT)/yammic

FHIR_LOCAL := http://127.0.0.1:$(FHIR_PORT)
FHIR2_LOCAL := http://127.0.0.1:$(FHIR2_PORT)
BACKEND_LOCAL := http://127.0.0.1:$(BACKEND_PORT)
WEB_LOCAL := http://127.0.0.1:$(WEB_PORT)
FHIR_BASE := $(FHIR_LOCAL)/fhir

# Backend settings for the two hospital endpoints. FHIR_BASE_URL is the
# backward-compatible single source (hospital 1). FHIR_SOURCES is the v4 list
# the backend reads: JSON array of {id, name, url}. Task D consumes it.
export FHIR_BASE_URL ?= $(FHIR_BASE)
export FHIR_SOURCES ?= [{"id":"hospital-1","name":"Hospital 1","url":"$(FHIR_LOCAL)/fhir"},{"id":"hospital-2","name":"Hospital 2","url":"$(FHIR2_LOCAL)/fhir"}]
# The AI worker talks to this stack's backend, never to v3's :8000.
export YAMMIC_API_URL ?= $(BACKEND_LOCAL)

LOG_DIR := ops/logs
RUN_DIR := ops/run
BUILD_DIR := app/build/web

.PHONY: help up down seed reset backend web ai demo stop health psql fhir stage-arrivals \
        _seed-fhir-h1 _seed-fhir-h2 _seed-fhir-arrivals

help:
	@echo "Yammic v4 demo platform (local only) — v3 stays on 5433/8090/8000/8080"
	@echo ""
	@echo "  make up        start Postgres 16 (:$(PG_PORT)) and HAPI FHIR R4 (:$(FHIR_PORT) + :$(FHIR2_PORT)); wait for healthy"
	@echo "  make down      stop containers, keep the data volume"
	@echo "  make seed      load synthetic data (both hospitals via fhir-seed/load.py, then backend seed)"
	@echo "  make reset     remove volumes, up, seed   (clean slate)"
	@echo "  make backend   run the FastAPI backend with reload on :$(BACKEND_PORT) (foreground)"
	@echo "  make ai        run the AI extraction worker for :$(BACKEND_PORT) in the foreground (one worker only)"
	@echo "  make web       build Flutter web and serve it on :$(WEB_PORT) (foreground)"
	@echo "  make stage-arrivals  load the live-sync arrivals into both hospitals (demo state in one command)"
	@echo "  make demo      up + seed if empty + backend + AI worker + web in the background, then health --strict"
	@echo "  make health    check Postgres, both FHIR servers, backend /health, AI worker, web (STRICT=1 to require all)"
	@echo "  make stop      stop this stack's backend + AI worker + web processes and containers"
	@echo "  make psql      open psql on the yammic database"
	@echo ""
	@echo "Logs: $(LOG_DIR)/  PIDs: $(RUN_DIR)/"
	@echo "Hospital 2 seed: fhir-seed/hospital2/<set>/ (FHIR_H2_SET, default baseline); skipped when absent."

# ---------------------------------------------------------------- infrastructure
up:
	@command -v docker >/dev/null || { echo "ERROR: docker not found in PATH"; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "ERROR: Docker daemon not reachable. Start Docker Desktop, then retry (ops/RUNBOOK.md)."; exit 1; }
	@echo "== up: starting Postgres 16 and both HAPI FHIR R4 servers (waiting for healthy)"
	@$(COMPOSE) up -d --wait --wait-timeout 600
	@echo "== up: postgres 127.0.0.1:$(PG_PORT)  |  hospital 1 $(FHIR_LOCAL)/fhir/metadata  |  hospital 2 $(FHIR2_LOCAL)/fhir/metadata"

down:
	@$(COMPOSE) down --remove-orphans
	@echo "== down: containers removed; data volume yammic-v4-postgres-data kept (v3 volume untouched)"

seed:
	@mkdir -p $(LOG_DIR)
	@$(MAKE) --no-print-directory _seed-fhir-h1
	@$(MAKE) --no-print-directory _seed-fhir-h2
	@if [ -f backend/app/seed.py ]; then \
		n=$$($(COMPOSE) exec -T postgres psql -U yammic -d yammic -tAc "SELECT count(*) FROM study" 2>/dev/null | tr -d '[:space:]'); \
		if [ -n "$$n" ] && [ "$$n" != "0" ]; then \
			echo "== seed: skip backend — database already has $$n study row(s) (use make reset for a clean slate)"; \
		else \
			echo "== seed: backend (python -m app.seed)"; \
			( cd backend && DATABASE_URL=$(ADMIN_URL) $(UV) run python -m app.seed ) || { echo "ERROR: backend seed failed"; exit 1; }; \
		fi; \
	else \
		echo "== seed: skip backend — backend/app/seed.py not present yet (workstream W1)"; \
	fi

# One FHIR load per hospital. `--set` selects the bundle set, `--hospital`
# selects the data tree and `--base-url` the server. Hospital 2 stays skipped
# until its data directory exists.
H1_HOSPITAL_ARG := $(if $(filter yes,$(FHIR_HAS_HOSPITAL_FLAG)),--hospital 1)
H2_HOSPITAL_ARG := $(if $(filter yes,$(FHIR_HAS_HOSPITAL_FLAG)),--hospital 2)
H2_SET_DIR := $(if $(filter yes,$(FHIR_HAS_HOSPITAL_FLAG)),fhir-seed/hospital2/$(FHIR_H2_SET),fhir-seed/hospital2)
H2_ARRIVALS_DIR := $(if $(filter yes,$(FHIR_HAS_HOSPITAL_FLAG)),fhir-seed/hospital2/$(FHIR_H2_ARRIVALS),fhir-seed/hospital2)

_seed-fhir-h1:
	@if [ ! -f fhir-seed/load.py ]; then \
		echo "== seed: skip FHIR hospital 1 — fhir-seed/load.py not present yet"; exit 0; \
	fi; \
	if [ ! -f "fhir-seed/$(FHIR_H1_SET)/manifest.json" ]; then \
		echo "ERROR: hospital 1 seed set '$(FHIR_H1_SET)' not found: fhir-seed/$(FHIR_H1_SET)/manifest.json"; exit 1; \
	fi; \
	echo "== seed: hospital 1 set=$(FHIR_H1_SET) -> $(FHIR_BASE)"; \
	$(UV) run --project backend python fhir-seed/load.py $(H1_HOSPITAL_ARG) --set "$(FHIR_H1_SET)" --base-url "$(FHIR_BASE)" \
		|| { echo "ERROR: hospital 1 FHIR seed failed"; exit 1; }

_seed-fhir-h2:
	@if [ ! -f fhir-seed/load.py ]; then \
		echo "== seed: skip FHIR hospital 2 — fhir-seed/load.py not present yet"; exit 0; \
	fi; \
	if [ "$(FHIR_HAS_HOSPITAL_FLAG)" != "yes" ]; then \
		echo "== seed: skip FHIR hospital 2 — load.py has no --hospital yet (task C)"; exit 0; \
	fi; \
	if [ ! -f "$(H2_SET_DIR)/manifest.json" ]; then \
		echo "== seed: skip FHIR hospital 2 — no $(H2_SET_DIR) data yet"; exit 0; \
	fi; \
	echo "== seed: hospital 2 set=$(FHIR_H2_SET) -> $(FHIR2_LOCAL)/fhir"; \
	$(UV) run --project backend python fhir-seed/load.py $(H2_HOSPITAL_ARG) --set "$(FHIR_H2_SET)" --base-url "$(FHIR2_LOCAL)/fhir" \
		|| { echo "ERROR: hospital 2 FHIR seed failed"; exit 1; }

reset:
	@echo "== reset: removing containers and data volume"
	@$(COMPOSE) down -v --remove-orphans
	@rm -f ops/audit-anchor.log   # the anchor belongs to the DB it anchors
	@$(MAKE) --no-print-directory up
	@$(MAKE) --no-print-directory seed

# ---------------------------------------------------------------- app processes
backend:
	@if [ ! -f backend/app/main.py ]; then echo "ERROR: backend not present yet (workstream W1)"; exit 1; fi
	@echo "== backend: uvicorn on $(BACKEND_LOCAL)"
	cd backend && exec $(UV) run uvicorn app.main:app --host 127.0.0.1 --port $(BACKEND_PORT) --reload

ai:
	@if [ ! -f backend/app/ai/__main__.py ]; then echo "ERROR: AI service not present (backend/app/ai)"; exit 1; fi
	@pids="$$(ops/ai-workers.sh | tr '\n' ' ' | sed 's/ $$//')"; \
	if [ -n "$$pids" ]; then \
		echo "ERROR: an AI worker is already running (pid $$pids) — one worker only; stop it first (make stop)"; exit 1; \
	fi
	@if ! timeout 3 curl -fsS "$(BACKEND_LOCAL)/health" >/dev/null 2>&1; then \
		echo "WARNING: backend is not answering on :$(BACKEND_PORT) — the worker cannot log in (start: make demo)"; \
	fi
	@echo "== ai: foreground worker (provider $(AI_PROVIDER)), API $(BACKEND_LOCAL); Ctrl-C to stop"
	cd backend && exec $(UV) run $(AI_RUN) --provider $(AI_PROVIDER) --api $(BACKEND_LOCAL)

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
	@$(MAKE) --no-print-directory _start-ai
	@$(MAKE) --no-print-directory _start-web
	@echo ""
	@STRICT=1 ops/health.sh --strict
	@echo ""
	@echo "Demo is up: web $(WEB_LOCAL)  |  API $(BACKEND_LOCAL)/docs"
	@echo "Hospital 1: $(FHIR_LOCAL)/fhir/metadata  |  hospital 2: $(FHIR2_LOCAL)/fhir/metadata"
	@ai_pids="$$(ops/ai-workers.sh | tr '\n' ' ' | sed 's/ $$//')"; \
	echo "AI worker: $${ai_pids:-NOT RUNNING} — consumes queued extraction runs (one worker per stack)"
	@echo "Logs: $(LOG_DIR)/backend.log $(LOG_DIR)/ai.log $(LOG_DIR)/web.log (web build: $(LOG_DIR)/web-build.log)"

_seed-if-empty:
	@backend_n=$$($(COMPOSE) exec -T postgres psql -U yammic -d yammic -tAc "SELECT count(*) FROM study" 2>/dev/null | tr -d '[:space:]'); \
	fhir_n=$$(timeout 10 curl -fsS "$(FHIR_LOCAL)/Patient?_summary=count" 2>/dev/null | $(PY) -c "import sys,json;print(json.load(sys.stdin).get('total',0))" 2>/dev/null); \
	fhir2_n=$$(timeout 10 curl -fsS "$(FHIR2_LOCAL)/Patient?_summary=count" 2>/dev/null | $(PY) -c "import sys,json;print(json.load(sys.stdin).get('total',0))" 2>/dev/null); \
	backend_n=$${backend_n:-0}; fhir_n=$${fhir_n:-0}; fhir2_n=$${fhir2_n:-0}; \
	need=0; \
	{ [ "$$backend_n" = "0" ] || [ "$$fhir_n" = "0" ]; } && need=1; \
	if [ -f "$(H2_SET_DIR)/manifest.json" ] && [ "$$fhir2_n" = "0" ]; then need=1; fi; \
	if [ "$$need" = "0" ]; then \
		echo "== demo: data present (backend $$backend_n studies, hospital 1 $$fhir_n patients, hospital 2 $$fhir2_n patients) — not seeding"; \
	else \
		echo "== demo: seeding (backend $$backend_n studies, hospital 1 $$fhir_n patients, hospital 2 $$fhir2_n patients)"; \
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

_start-ai:
	@mkdir -p $(LOG_DIR) $(RUN_DIR)
	@pids="$$(ops/ai-workers.sh | tr '\n' ' ' | sed 's/ $$//')"; \
	if [ -n "$$pids" ]; then \
		echo "== demo: AI worker already running (pid $$pids) — one worker only"; \
	else \
		if ! timeout 3 curl -fsS "$(BACKEND_LOCAL)/health" >/dev/null 2>&1; then \
			echo "ERROR: backend is not answering on :$(BACKEND_PORT); the AI worker needs it"; exit 1; \
		fi; \
		if [ ! -f backend/app/ai/__main__.py ]; then echo "ERROR: AI service not present (backend/app/ai)"; exit 1; fi; \
		echo "== demo: starting AI worker (provider $(AI_PROVIDER)), log $(LOG_DIR)/ai.log"; \
		( cd backend && exec nohup $(UV) run $(AI_RUN) --provider $(AI_PROVIDER) --api $(BACKEND_LOCAL) ) \
			> "$(CURDIR)/$(LOG_DIR)/ai.log" 2>&1 & echo $$! > "$(CURDIR)/$(RUN_DIR)/ai.pid"; \
		ready=0; \
		for i in $$(seq 1 15); do \
			if ! kill -0 $$(cat "$(CURDIR)/$(RUN_DIR)/ai.pid") 2>/dev/null; then \
				echo "ERROR: AI worker exited during startup; see $(LOG_DIR)/ai.log"; \
				tail -n 5 "$(LOG_DIR)/ai.log" 2>/dev/null; rm -f "$(RUN_DIR)/ai.pid"; exit 1; \
			fi; \
			if [ -n "$$(ops/ai-workers.sh)" ]; then ready=1; break; fi; \
			sleep 1; \
		done; \
		if [ "$$ready" != "1" ]; then \
			echo "ERROR: AI worker did not start in 15 s; see $(LOG_DIR)/ai.log"; \
			tail -n 5 "$(LOG_DIR)/ai.log" 2>/dev/null; exit 1; \
		fi; \
		pids="$$(ops/ai-workers.sh | tr '\n' ' ' | sed 's/ $$//')"; \
		echo "== demo: AI worker ready (pid $$pids), provider $(AI_PROVIDER)"; \
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
	@pids="$$(ops/ai-workers.sh | tr '\n' ' ' | sed 's/ $$//')"; \
	if [ -f $(RUN_DIR)/ai.pid ]; then kill $$(cat $(RUN_DIR)/ai.pid) 2>/dev/null || true; fi; \
	if [ -n "$$pids" ]; then kill $$pids 2>/dev/null || true; echo "== stop: ai worker (pid $$pids)"; fi; \
	rm -f $(RUN_DIR)/ai.pid
	@pkill -f "uvicorn app.main:app.*--port $(BACKEND_PORT)" 2>/dev/null || true
	@pkill -f "http.server $(WEB_PORT)" 2>/dev/null || true
	@$(COMPOSE) down --remove-orphans
	@echo "== stop: this stack's app processes and containers stopped; v4 data volume kept (v3 untouched)"

# ---------------------------------------------------------------- checks / misc
health:
	@if [ "$(STRICT)" = "1" ]; then ops/health.sh --strict; else ops/health.sh; fi

stage-arrivals:
	@if [ ! -f fhir-seed/load.py ]; then echo "ERROR: fhir-seed/load.py not present"; exit 1; fi
	@if ! timeout 10 curl -fsS "$(FHIR_LOCAL)/fhir/metadata" >/dev/null 2>&1; then \
		echo "ERROR: hospital 1 HAPI is not answering on $(FHIR_LOCAL); run: make up"; exit 1; \
	fi
	@if ! timeout 10 curl -fsS "$(FHIR2_LOCAL)/fhir/metadata" >/dev/null 2>&1; then \
		echo "ERROR: hospital 2 HAPI is not answering on $(FHIR2_LOCAL); run: make up"; exit 1; \
	fi
	@echo "== stage-arrivals: loading the live-sync arrival bundles into both hospitals (platform data not touched)"
	@echo "== stage-arrivals: hospital 1 set=$(FHIR_H1_ARRIVALS) -> $(FHIR_BASE)"
	@$(PY) fhir-seed/load.py --set "$(FHIR_H1_ARRIVALS)" --base-url "$(FHIR_BASE)"
	@if [ "$(FHIR_HAS_HOSPITAL_FLAG)" = "yes" ] && [ -f "$(H2_ARRIVALS_DIR)/manifest.json" ]; then \
		echo "== stage-arrivals: hospital 2 set=$(FHIR_H2_ARRIVALS) -> $(FHIR2_LOCAL)/fhir"; \
		$(PY) fhir-seed/load.py $(H2_HOSPITAL_ARG) --set "$(FHIR_H2_ARRIVALS)" --base-url "$(FHIR2_LOCAL)/fhir"; \
	else \
		echo "== stage-arrivals: skip hospital 2 — no hospital-2 arrivals data yet"; \
	fi
	@echo "== stage-arrivals: done — press Sync now in the app to pull the new patients"

psql:
	@$(COMPOSE) exec postgres psql -U yammic -d yammic

fhir:
	@for u in $(FHIR_LOCAL) $(FHIR2_LOCAL); do echo "== $$u/fhir/metadata"; curl -fsS "$$u/fhir/metadata" | $(PY) -m json.tool | head -20; done
