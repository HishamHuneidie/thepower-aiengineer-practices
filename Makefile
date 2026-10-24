DOCKER=docker compose -p thepower-course
DOCKER_LANGFUSE=$(DOCKER)-langfuse -f ./repositories/langfuse/docker-compose.yml --env-file ./repositories/langfuse/.env
DOCKER_UTILS=$(DOCKER)-utils -f ./repositories/container-utils/compose.yaml

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
	$(DOCKER_LANGFUSE) stop

.PHONY: utils-start
utils-start:
	$(DOCKER_UTILS) up -d --build

.PHONY: utils-restart
utils-restart:
	$(DOCKER_UTILS) restart

.PHONY: utils-stop
utils-stop:
	$(DOCKER_UTILS) stop

.PHONY: utils-remove
utils-remove:
	$(DOCKER_UTILS) down -v

# All about de architecture

.PHONY: context-new
context-new:
	./scripts/context-new.sh