FROM python:3.12-slim

# Install Node.js and basic tools
RUN apt-get update && apt-get install -y curl supervisor tesseract-ocr && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy all files
COPY . .

# 1. Install API Gateway dependencies
RUN cd services/api-gateway && pip install --no-cache-dir -r requirements.txt

# 2. Install OCR Pipeline dependencies
RUN cd services/ai-ocr-pipeline && pip install --no-cache-dir -r requirements.txt

# 3. Install Quorum Engine dependencies
RUN cd services/quorum-approval-engine && npm install

# Setup Supervisord to run all three services concurrently
RUN echo "[supervisord]" > /etc/supervisor/conf.d/supervisord.conf && \
    echo "nodaemon=true" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "[program:api-gateway]" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "command=/bin/bash -c \"uvicorn main:app --host 0.0.0.0 --port \${PORT:-8000}\"" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "directory=/app/services/api-gateway" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "[program:ocr-pipeline]" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "command=uvicorn api:app --host 0.0.0.0 --port 8001" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "directory=/app/services/ai-ocr-pipeline" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "[program:quorum-engine]" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "command=npm start" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "directory=/app/services/quorum-approval-engine" >> /etc/supervisor/conf.d/supervisord.conf

# Run supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

