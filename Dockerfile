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

# Copy requirements and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-install solc 0.8.20 during build so container starts instantly
RUN python -c "import solcx; solcx.install_solc('0.8.20')" || true

# Copy application source code
COPY . .

# Expose default ports
EXPOSE 8000 10000

# Run entrypoint script with comprehensive error handling and dynamic $PORT support
CMD ["python", "start.py"]
