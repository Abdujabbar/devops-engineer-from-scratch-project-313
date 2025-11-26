FROM python:3.14-slim

WORKDIR /app

RUN echo "Acquire::http::Pipeline-Depth 0;" > /etc/apt/apt.conf.d/99custom && \
    echo "Acquire::http::No-Cache true;" >> /etc/apt/apt.conf.d/99custom && \
    echo "Acquire::BrokenProxy    true;" >> /etc/apt/apt.conf.d/99custom

RUN printf 'deb http://ftp.de.debian.org/debian trixie main\n\
    deb http://ftp.de.debian.org/debian trixie-updates main\n\
    deb http://ftp.de.debian.org/debian-security trixie-security main\n' > /etc/apt/sources.list


# Install Node.js, npm, nginx, and build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends --fix-missing \
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
ARG API_URL=https://devops-engineer-from-scratch-project-313-unba.onrender.com/
ENV API_URL=${API_URL}
RUN set -e && \
    echo "API_URL: ${API_URL}" && \
    echo "Copying pre-built frontend files from globally installed package..." && \
    mkdir -p /usr/share/nginx/html && \
    if [ -d "/usr/lib/node_modules/@hexlet/project-devops-deploy-crud-frontend/dist" ]; then \
    echo "Found dist directory in global package, copying files..." && \
    cp -r /usr/lib/node_modules/@hexlet/project-devops-deploy-crud-frontend/dist/* /usr/share/nginx/html/ && \
    echo "Files copied successfully"; \
    else \
    echo "Error: dist directory not found in global package" && \
    echo "Checking global package location..." && \
    ls -la /usr/lib/node_modules/@hexlet/project-devops-deploy-crud-frontend/ 2>/dev/null || echo "Package not found in expected location" && \
    exit 1; \
    fi

# Copy nginx configuration for container
COPY nginx-container.conf /etc/nginx/nginx.conf

# Expose port 80 (nginx)
EXPOSE 80

# Start all services using Makefile command
CMD ["make", "start-container"]