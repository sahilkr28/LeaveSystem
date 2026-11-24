# Production Dockerfile for Smart Campus Hostel ERP
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Set working directory
WORKDIR /app

# Install system dependencies for PostgreSQL client and build utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition
COPY app/requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . /app

# Non-root user security policy
RUN useradd -m -u 1001 erpuser && \
    chown -R erpuser:erpuser /app
USER erpuser

# Expose ERP web port
EXPOSE 5000

# Healthcheck targeting the telemetry route
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Production WSGI Server Command
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
