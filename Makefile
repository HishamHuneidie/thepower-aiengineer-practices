DOCKER=docker compose -p thepower-course

# All about the app

.PHONY: start
start:
	$(DOCKER) up -d --build

.PHONY: restart
restart:
	$(DOCKER) restart

.PHONY: remove
remove:
	$(DOCKER) down -v

.PHONY: logs
logs:
	$(DOCKER) logs -f

.PHONY: build
build:
	$(DOCKER) build --no-cache

.PHONY: rebuild
rebuild: remove build

# All about de architecture

.PHONY: context-new
context-new:
	./scripts/context-new.sh