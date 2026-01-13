FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY talon/requirements.txt /app/talon/requirements.txt
RUN pip install --no-cache-dir -r /app/talon/requirements.txt

# Copy shared utilities
COPY shared /app/shared

# Copy application code
COPY talon /app/talon

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd --create-home --shell /bin/bash talon
RUN chown -R talon:talon /app
USER talon

# Expose port
EXPOSE 5000

# Default command (Flask app)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "talon.app:create_app()"]
