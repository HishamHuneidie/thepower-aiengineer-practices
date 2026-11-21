DOCKER=docker compose -p thepower-course-m13-p12
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

.PHONY: logs-app
logs-app:
	$(DOCKER) logs -f app

.PHONY: rebuild
rebuild: remove start

.PHONY: db-bash
db-bash:
	$(DOCKER_EXEC) db env GPASSWORD=thepower psql -U thepower -d thepower

.PHONY: exec
exec:
	$(DOCKER_EXEC) app $(C)


# Práctica S12: demo en terminal (ver README.md)

.PHONY: inputs
inputs:
	$(DOCKER_EXEC) app python -m app.demo --prepare-inputs

.PHONY: demo
demo:
	$(DOCKER_EXEC) app python -m app.demo

.PHONY: demo-simulate
demo-simulate:
	$(DOCKER_EXEC) app python -m app.demo --simulate

.PHONY: demo-research
demo-research:
	$(DOCKER_EXEC) app python -m app.demo --research

.PHONY: research-status
research-status:
	$(DOCKER_EXEC) app python -m app.demo --status
