DOCKER=docker compose -p thepower-course-m17-p16
DOCKER_EXEC=$(DOCKER) exec -it

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

.PHONY: exec
exec:
	$(DOCKER_EXEC) app $(C)
