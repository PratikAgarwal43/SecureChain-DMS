FROM python:3.12-slim

# Install Node.js and basic tools
RUN apt-get update && apt-get install -y curl supervisor && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy all files
COPY . .

# 1. Install API Gateway dependencies
RUN cd services/api-gateway && pip install --no-cache-dir -r requirements.txt

# 2. Install Quorum Engine dependencies
RUN cd services/quorum-approval-engine && npm install

# Setup Supervisord to run the two services concurrently
RUN echo "[supervisord]" > /etc/supervisor/supervisord.conf && \
    echo "nodaemon=true" >> /etc/supervisor/supervisord.conf && \
    echo "[program:api-gateway]" >> /etc/supervisor/supervisord.conf && \
    echo "command=/bin/bash -c \"uvicorn main:app --host 0.0.0.0 --port \${PORT:-8000}\"" >> /etc/supervisor/supervisord.conf && \
    echo "directory=/app/services/api-gateway" >> /etc/supervisor/supervisord.conf && \
    echo "stdout_logfile=/dev/stdout" >> /etc/supervisor/supervisord.conf && \
    echo "stdout_logfile_maxbytes=0" >> /etc/supervisor/supervisord.conf && \
    echo "stderr_logfile=/dev/stderr" >> /etc/supervisor/supervisord.conf && \
    echo "stderr_logfile_maxbytes=0" >> /etc/supervisor/supervisord.conf && \
    echo "[program:quorum-engine]" >> /etc/supervisor/supervisord.conf && \
    # Force Quorum Engine to run on 3000 so it does not conflict with Render internal PORT \
    echo "environment=PORT=\"3000\"" >> /etc/supervisor/supervisord.conf && \
    echo "command=npm start" >> /etc/supervisor/supervisord.conf && \
    echo "directory=/app/services/quorum-approval-engine" >> /etc/supervisor/supervisord.conf && \
    echo "stdout_logfile=/dev/stdout" >> /etc/supervisor/supervisord.conf && \
    echo "stdout_logfile_maxbytes=0" >> /etc/supervisor/supervisord.conf && \
    echo "stderr_logfile=/dev/stderr" >> /etc/supervisor/supervisord.conf && \
    echo "stderr_logfile_maxbytes=0" >> /etc/supervisor/supervisord.conf

# Run supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]

