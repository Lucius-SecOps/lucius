FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY sentinel/requirements.txt /app/sentinel/requirements.txt
RUN pip install --no-cache-dir -r /app/sentinel/requirements.txt

# Copy shared utilities
COPY shared /app/shared

# Copy application code
COPY sentinel /app/sentinel

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd --create-home --shell /bin/bash sentinel
RUN chown -R sentinel:sentinel /app
USER sentinel

# Default command
CMD ["python", "-m", "sentinel.cli", "scan", "--help"]
