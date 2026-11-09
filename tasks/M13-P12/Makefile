DOCKER=docker compose -p thepower-course-m13-p12

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




