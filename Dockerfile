FROM python:3.14-slim

WORKDIR /app

# Install Node.js, npm, nginx, and build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    make \
    curl \
    nginx \
    && curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install frontend package globally
RUN npm install -g @hexlet/project-devops-deploy-crud-frontend

# Install uv
RUN pip install --no-cache-dir uv

# Install Python dependencies
COPY pyproject.toml uv.lock* Makefile ./
RUN make install

# Copy application code
COPY . .

# Build frontend with API_URL (default to localhost for build, can be overridden)
ARG API_URL=http://localhost:8080
ENV API_URL=${API_URL}
RUN FRONTEND_DIR=$$(npm root -g)/@hexlet/project-devops-deploy-crud-frontend && \
    mkdir -p /usr/share/nginx/html && \
    cd $$FRONTEND_DIR && \
    API_URL=${API_URL} npm run build && \
    if [ -d "dist" ]; then \
    cp -r dist/* /usr/share/nginx/html/; \
    else \
    echo "Error: dist directory not found after build" && exit 1; \
    fi

# Copy nginx configuration for container
COPY nginx-container.conf /etc/nginx/nginx.conf

# Expose port 80 (nginx)
EXPOSE 80

# Start all services using Makefile command
CMD ["make", "start-container"]