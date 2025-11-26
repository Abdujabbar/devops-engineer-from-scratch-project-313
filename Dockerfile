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

# Build frontend with API_URL from environment variables (Render) or use default
# Can be set via: docker build --build-arg API_URL=... or via Render's environment variables
ARG API_URL=http://localhost:8080
ENV API_URL=${API_URL}
RUN set -e && \
    FRONTEND_DIR=$$(npm root -g)/@hexlet/project-devops-deploy-crud-frontend && \
    echo "Frontend directory: $$FRONTEND_DIR" && \
    echo "API_URL: ${API_URL}" && \
    mkdir -p /usr/share/nginx/html && \
    cd $$FRONTEND_DIR && \
    echo "Current directory: $$(pwd)" && \
    echo "Running build command..." && \
    API_URL=${API_URL} npm run build && \
    echo "Build completed, checking for dist directory..." && \
    ls -la && \
    if [ -d "dist" ]; then \
    echo "Found dist directory, copying files..." && \
    cp -r dist/* /usr/share/nginx/html/ && \
    echo "Files copied successfully"; \
    else \
    echo "Error: dist directory not found after build in $$(pwd)" && \
    echo "Contents of current directory:" && \
    ls -la && \
    exit 1; \
    fi

# Copy nginx configuration for container
COPY nginx-container.conf /etc/nginx/nginx.conf

# Expose port 80 (nginx)
EXPOSE 80

# Start all services using Makefile command
CMD ["make", "start-container"]