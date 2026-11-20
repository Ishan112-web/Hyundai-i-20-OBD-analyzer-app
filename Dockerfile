# i20 AI Garage - Staging Dockerfile
# Multi-stage build for minimal production image

# =============================================================================
# Build Stage - Install dependencies and compile wheels
# =============================================================================
FROM python:3.11-slim AS builder

# Install system dependencies for building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    libopenblas-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for clean dependency isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements first for better cache utilization
COPY requirements.txt .
COPY requirements-dev.txt .

# Install production dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install dev dependencies (for testing in container if needed)
# RUN pip install --no-cache-dir -r requirements-dev.txt


# =============================================================================
# Runtime Stage - Minimal image with only runtime dependencies
# =============================================================================
FROM python:3.11-slim AS runtime

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6 \
    libjpeg62-turbo \
    zlib1g \
    libopenblas0 \
    libsqlite3-0 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appgroup app.py config.py ./
COPY --chown=appuser:appgroup components/ ./components/
COPY --chown=appuser:appgroup modules/ ./modules/
COPY --chown=appuser:appgroup services/ ./services/
COPY --chown=appuser:appgroup scripts/ ./scripts/

# Create data and reports directories with correct ownership
RUN mkdir -p /app/data /app/reports && chown -R appuser:appgroup /app/data /app/reports

# Switch to non-root user
USER appuser

# Environment variables for staging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    OBD_MODE=simulation \
    SIMULATION_INTERVAL=1.0 \
    TELEMETRY_REFRESH_INTERVAL=2.0 \
    DATABASE_PATH=/app/data/i20_garage_staging.db

# Expose Streamlit port (Render assigns PORT env var)
EXPOSE 8501

# Health check endpoint - uses Streamlit's built-in health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Entry point
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]