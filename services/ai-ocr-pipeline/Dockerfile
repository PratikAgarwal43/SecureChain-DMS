# SecureChain DMS — Member 6 Service (OCR + Forensic + Sensitivity)
# Base image includes CUDA runtime so Qwen2-VL can run on GPU inside the container.
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV SECURECHAIN_HOME=/app

# --- system dependencies ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3-pip python3.11-venv \
    poppler-utils \
    libgl1 libglib2.0-0 \
    git curl \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3.11 /usr/bin/python

WORKDIR /app

# --- python dependencies (cached layer — only rebuilds if requirements.txt changes) ---
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- application code ---
COPY core/ ./core/
COPY api.py .
RUN mkdir -p ./models ./work

EXPOSE 8000

ENV API_PORT=8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
