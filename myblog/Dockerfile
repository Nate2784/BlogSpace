# Multi-stage Dockerfile for BlogSpace
# Stage 1: Base image with common dependencies
FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies with security updates
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        gettext \
        curl \
        netcat-openbsd \
        git \
        ca-certificates \
        gnupg \
        lsb-release \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create and set work directory
WORKDIR /app

# Create non-root user with specific UID/GID for better security
RUN groupadd -r django --gid=1000 && useradd -r -g django --uid=1000 django

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies with security and performance optimizations
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --no-deps -r requirements.txt \
    && pip check \
    && python -m compileall /usr/local/lib/python3.12/site-packages/

# Copy entrypoint script and make it executable
COPY --chown=django:django entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy project files with proper ownership
COPY --chown=django:django . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/staticfiles /app/media /app/logs \
    && chmod 755 /app/staticfiles /app/media /app/logs \
    && find /app -type f -name "*.py" -exec chmod 644 {} \; \
    && find /app -type d -exec chmod 755 {} \;

# Switch to non-root user for security
USER django

# Expose port
EXPOSE 8000

# Add labels for better container management
LABEL maintainer="BlogSpace Team"
LABEL version="2.0"
LABEL description="Modern BlogSpace Django Application"

# Enhanced health check with better error handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || curl -f http://localhost:8000/ || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Run the application with optimized Gunicorn configuration
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--worker-connections", "1000", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--preload", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "myblog.wsgi:application"]

# Stage 2: Development image with additional tools
FROM base AS development

# Switch back to root for development tools installation
USER root

# Install development dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        vim \
        nano \
        htop \
        tree \
        iputils-ping \
        telnet \
        strace \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install development Python packages
RUN pip install --no-cache-dir \
        django-debug-toolbar \
        django-extensions \
        ipython \
        pytest \
        pytest-django \
        coverage \
        black \
        flake8 \
        isort

# Switch back to django user
USER django

# Override CMD for development
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
