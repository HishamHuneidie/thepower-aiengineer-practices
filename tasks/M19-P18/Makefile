DOCKER=docker compose -p thepower-course-m19-p18
DOCKER_EXEC=$(DOCKER) exec -it
DOCKER_EXEC_NON_INTERACTIVE=$(DOCKER) exec -T

# All about the app

.PHONY: start
start:
	$(DOCKER) up -d --build

.PHONY: restart
restart:
	$(DOCKER) restart

.PHONY: stop
stop:
	$(DOCKER) down

.PHONY: remove
remove:
	$(DOCKER) down -v

.PHONY: logs
logs:
	$(DOCKER) logs -f

.PHONY: rebuild
rebuild: remove start

.PHONY: bash
bash:
	$(DOCKER_EXEC) app bash

.PHONY: exec
exec:
	$(DOCKER_EXEC) app $(C)

.PHONY: test
test:
	$(DOCKER_EXEC) app pytest

.PHONY: validate
validate:
	$(DOCKER_EXEC) app ruff check .
