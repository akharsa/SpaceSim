# Makefile for SpaceSim - convenience wrapper around docker compose

# Load environment variables from .env file if it exists
ifneq (,$(wildcard .env))
    include .env
    export
endif

COMPOSE_BASE := -f simulator/docker-compose.yml -f simulator/telemetry_bridge.yml -f simulator/visualizer.yml
# include generated mission override if present
COMPOSE_MISSION := $(if $(wildcard simulator/compose.mission.yml),-f simulator/compose.mission.yml,)
DC := docker compose $(COMPOSE_BASE) $(COMPOSE_MISSION)

.PHONY: help up up-no-build build down down-volumes restart logs logs-service ps exec shell clean install gen-compose up-infra dev

help:
	@echo "Usage: make <target> [SERVICE=name]"
	@echo "Targets:"
	@echo "  install        - create .venv and install repo requirements (runs scripts/setup_env.sh)"
	@echo "  dev            - start in development mode with live file updates (requires MISSION=<name>)"
	@echo "  up             - build and start all services in background (requires MISSION=<name>)"
	@echo "  up-no-build    - start services without building (requires MISSION=<name>)"
	@echo "  build          - build all service images"
	@echo "  down           - stop and remove containers"
	@echo "  down-volumes   - stop, remove containers and volumes"
	@echo "  restart        - down then up"
	@echo "  logs           - follow logs for all services"
	@echo "  logs-service   - follow logs for a specific service (SERVICE=name)"
	@echo "  ps             - show docker compose status"
	@echo "  exec           - exec a shell in a service (SERVICE=name)"
	@echo "  shell          - exec bash or sh in a service (SERVICE=name)"
	@echo "  clean          - down, remove local images and orphans"

install:
	@echo "Running setup_env.sh to create .venv and install requirements..."
	./scripts/setup_env.sh

.PHONY: gen-compose up-infra

dev:
	@echo "Starting in development mode with live file updates..."
	@echo "Edit files in simulator/visualizer/public/ and they'll update immediately!"
	@if [ -z "$(MISSION)" ]; then echo "Specify MISSION=<mission-name> (available under missions/)"; exit 1; fi
	@if [ ! -f "missions/$(MISSION).yaml" ]; then echo "Mission file missions/$(MISSION).yaml not found"; exit 1; fi
	$(MAKE) gen-compose
	NODE_ENV=development $(DC) up --build

gen-compose:
	@if [ -z "$(MISSION)" ]; then echo "Specify MISSION=<mission-name>"; exit 1; fi
	@if [ ! -f "missions/$(MISSION).yaml" ]; then echo "Mission file missions/$(MISSION).yaml not found"; exit 1; fi
	@if [ ! -d ".venv" ]; then echo "Virtual environment not found. Run 'make install' first."; exit 1; fi
	.venv/bin/python scripts/generate_compose_mission.py $(MISSION)

up-infra:
	@echo "Bringing up simulator services: mosquitto, influxdb, grafana, telemetry_bridge, visualizer"
	$(DC) up -d --build

up:
	@# Ensure simulator is running, then generate mission override and start mission services
	@if [ -z "$(MISSION)" ]; then echo "Specify MISSION=<mission-name> (available under missions/)"; exit 1; fi
	@if [ ! -f "missions/$(MISSION).yaml" ]; then echo "Mission file missions/$(MISSION).yaml not found"; exit 1; fi
	$(MAKE) gen-compose
	$(DC) up -d --build

up-no-build:
	@# Start simulator and mission services without building
	@if [ -z "$(MISSION)" ]; then echo "Specify MISSION=<mission-name> (available under missions/)"; exit 1; fi
	@if [ ! -f "missions/$(MISSION).yaml" ]; then echo "Mission file missions/$(MISSION).yaml not found"; exit 1; fi
	$(MAKE) gen-compose
	$(DC) up -d

build:
	$(DC) build --parallel

down:
	$(DC) down

down-volumes:
	$(DC) down -v

restart:
	$(MAKE) down
	$(MAKE) up

logs:
	$(DC) logs -f --tail=200

logs-service:
	@if [ -z "$(SERVICE)" ]; then echo "Specify SERVICE=<service>"; exit 1; fi
	$(DC) logs -f --tail=200 $(SERVICE)

ps:
	$(DC) ps

exec:
	@if [ -z "$(SERVICE)" ]; then echo "Specify SERVICE=<service>"; exit 1; fi
	$(DC) exec -it $(SERVICE) sh

shell:
	@if [ -z "$(SERVICE)" ]; then echo "Specify SERVICE=<service>"; exit 1; fi
	-$(DC) exec -it $(SERVICE) /bin/bash || $(DC) exec -it $(SERVICE) sh

clean:
	$(DC) down -v --rmi local --remove-orphans
