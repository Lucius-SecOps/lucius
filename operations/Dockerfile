FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY operations/requirements.txt /app/operations/requirements.txt
RUN pip install --no-cache-dir -r /app/operations/requirements.txt

# Copy shared utilities
COPY shared /app/shared

# Copy application code
COPY operations /app/operations

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd --create-home --shell /bin/bash operations
RUN chown -R operations:operations /app
USER operations

# Default command
CMD ["python", "-m", "operations.cli", "--help"]
