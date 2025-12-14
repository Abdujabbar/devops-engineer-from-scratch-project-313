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


RUN FRONTEND_DIR=$$(npm root -g)/@hexlet/project-devops-deploy-crud-frontend && \
    cp -r $$FRONTEND_DIR/dist/. /app/public/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80 (nginx)
EXPOSE 80

# Start all services using Makefile command
CMD ["make", "start-container"]