DOCKER=docker compose -p thepower-course
DOCKER_LANGFUSE=$(DOCKER)-langfuse -f ./repositories/langfuse/docker-compose.yml --env-file ./repositories/langfuse/.env

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

.PHONY: langfuse-start
langfuse-start:
	$(DOCKER_LANGFUSE) up -d --build

.PHONY: langfuse-restart
langfuse-restart:
	$(DOCKER_LANGFUSE) restart

.PHONY: langfuse-stop
langfuse-stop:
	$(DOCKER) stop

# All about de architecture

.PHONY: context-new
context-new:
	./scripts/context-new.sh