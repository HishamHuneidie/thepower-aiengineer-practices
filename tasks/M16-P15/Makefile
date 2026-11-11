DOCKER=docker compose -p thepower-course-m16-p15
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

.PHONY: db-bash
db-bash:
	$(DOCKER) exec -ti db env GPASSWORD=thepower psql -U thepower -d thepower

.PHONY: run
run:
	$(DOCKER_EXEC) app python runs/01_connect_to_mcp.py




