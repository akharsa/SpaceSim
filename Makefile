# Makefile for SpaceSim - convenience wrapper around docker compose

COMPOSE_FILE := infrastructure/docker-compose.yml
DC := docker compose -f $(COMPOSE_FILE)

.PHONY: help up up-no-build build down down-volumes restart logs logs-service ps exec shell clean install gen-compose

help:
	@echo "Usage: make <target> [SERVICE=name]"
	@echo "Targets:"
	@echo "  install        - create .venv and install repo requirements (runs scripts/setup_env.sh)"
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

.PHONY: gen-compose

gen-compose:
	@if [ -z "$(MISSION)" ]; then echo "Specify MISSION=<mission-name>"; exit 1; fi
	@if [ ! -f "missions/$(MISSION).yaml" ]; then echo "Mission file missions/$(MISSION).yaml not found"; exit 1; fi
	python3 scripts/generate_compose_mission.py $(MISSION)

up:
	@# Ensure mission override is generated for missions with more than 2 satellites
	@if [ -z "$(MISSION)" ]; then echo "Specify MISSION=<mission-name> (available under missions/)"; exit 1; fi
	@if [ ! -f "missions/$(MISSION).yaml" ]; then echo "Mission file missions/$(MISSION).yaml not found"; exit 1; fi
	$(MAKE) gen-compose
	$(DC) -f infrastructure/docker-compose.yml -f infrastructure/compose.mission.yml up -d --build

up-no-build:
	@if [ -z "$(MISSION)" ]; then echo "Specify MISSION=<mission-name> (available under missions/)"; exit 1; fi
	@if [ ! -f "missions/$(MISSION).yaml" ]; then echo "Mission file missions/$(MISSION).yaml not found"; exit 1; fi
	$(MAKE) gen-compose
	$(DC) -f infrastructure/docker-compose.yml -f infrastructure/compose.mission.yml up -d

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
