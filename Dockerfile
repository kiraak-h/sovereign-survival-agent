# Production Multi-Stage Dockerfile for Sovereign AI Agent
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies, Node.js, and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    nodejs \
    npm \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install solc 0.8.20 static binary
RUN curl -L -o /usr/local/bin/solc https://github.com/ethereum/solidity/releases/download/v0.8.20/solc-static-linux \
    && chmod +x /usr/local/bin/solc

# Copy requirements and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose default port
EXPOSE 8000 10000

# Run FastAPI server with uvicorn respecting Render's dynamic $PORT
CMD ["sh", "-c", "python -m uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
