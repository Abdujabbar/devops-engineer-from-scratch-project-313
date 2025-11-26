
API_URL ?= http://localhost:8080

start:
	uv run fastapi dev --host localhost --port 8080

start-frontend:
	npx start-hexlet-devops-deploy-crud-frontend

build-frontend:
	@echo "Building frontend..."
	@echo "Note: For production deployment, frontend is built in Dockerfile with Node.js v24"
	@echo "This local build uses your current Node.js version: $$(node --version)"
	@mkdir -p dist
	@FRONTEND_DIR=$$(npm root -g)/@hexlet/project-devops-deploy-crud-frontend && \
	if [ ! -d "$$FRONTEND_DIR" ]; then \
		echo "Installing frontend package..." && \
		npm install -g @hexlet/project-devops-deploy-crud-frontend; \
	fi && \
	cd $$FRONTEND_DIR && \
	API_URL=$(API_URL) npm run build && \
	cp -r dist/* $(PWD)/dist/ 2>/dev/null || true
	@echo "Frontend built in dist/ directory"

start-nginx:
	@echo "Starting nginx on port 80..."
	@if docker ps -q -f name=nginx-proxy 2>/dev/null | grep -q .; then \
		echo "Nginx container already running"; \
	else \
		docker run -d --name nginx-proxy --rm \
			-p 80:80 \
			-v $$(pwd)/nginx.conf:/etc/nginx/nginx.conf:ro \
			--add-host=host.docker.internal:host-gateway \
			nginx:alpine; \
		echo "Nginx started on port 80"; \
	fi

stop-nginx:
	@echo "Stopping nginx..."
	@docker stop nginx-proxy 2>/dev/null || true

start-all:
	@echo "Starting backend, frontend, and nginx concurrently..."
	@trap 'make stop-nginx; kill 0' INT TERM EXIT; \
	make start-nginx; \
	uv run fastapi dev --host localhost --port 8080 & \
	API_URL=$(API_URL) npx start-hexlet-devops-deploy-crud-frontend & \
	wait

start-container:
	@echo "Starting backend and nginx in container (frontend served as static files)..."
	@trap 'kill 0' SIGTERM SIGINT; \
	uv run uvicorn main:app --host 0.0.0.0 --port 8080 & \
	sleep 2 && nginx -g 'daemon off;' & \
	wait

test:
	uv run pytest tests/

lint:
	uv run ruff check .

format:
	uv run ruff format .

install:
	uv sync