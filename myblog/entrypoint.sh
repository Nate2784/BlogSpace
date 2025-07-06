#!/bin/bash

# BlogSpace Docker Entrypoint Script
# This script prepares the Django application for running in a container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to wait for database
wait_for_db() {
    log_info "Waiting for database to be ready..."
    
    # Extract database info from DATABASE_URL or use individual variables
    if [ -n "$DATABASE_URL" ]; then
        # Parse DATABASE_URL
        DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
        DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    fi
    
    # Default values if not set
    DB_HOST=${DB_HOST:-localhost}
    DB_PORT=${DB_PORT:-5432}
    
    # Wait for database connection
    while ! nc -z $DB_HOST $DB_PORT; do
        log_info "Database is unavailable - sleeping"
        sleep 1
    done
    
    log_success "Database is ready!"
}

# Function to wait for Redis
wait_for_redis() {
    if [ -n "$REDIS_URL" ] && [ "$DEBUG" = "False" ] || [ "$DEBUG" = "false" ]; then
        log_info "Waiting for Redis to be ready..."

        # Extract Redis host and port
        REDIS_HOST=$(echo $REDIS_URL | sed -n 's/redis:\/\/\([^:]*\):.*/\1/p')
        REDIS_PORT=$(echo $REDIS_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

        REDIS_HOST=${REDIS_HOST:-localhost}
        REDIS_PORT=${REDIS_PORT:-6379}

        while ! nc -z $REDIS_HOST $REDIS_PORT; do
            log_info "Redis is unavailable - sleeping"
            sleep 1
        done

        log_success "Redis is ready!"
    else
        log_info "Skipping Redis check for development mode"
    fi
}

# Function to run database migrations
run_migrations() {
    log_info "Running database migrations..."
    python manage.py migrate --noinput
    log_success "Database migrations completed!"
}

# Function to collect static files
collect_static() {
    log_info "Collecting static files..."
    python manage.py collectstatic --noinput --clear
    log_success "Static files collected!"
}

# Function to create cache table
create_cache_table() {
    if [ "$DEBUG" = "False" ] || [ "$DEBUG" = "false" ]; then
        log_info "Creating cache table..."
        python manage.py createcachetable || log_warning "Cache table creation failed or already exists"
    else
        log_info "Skipping cache table creation for development mode"
    fi
}

# Function to check for superuser
check_superuser() {
    log_info "Checking for superuser..."
    
    # Check if DJANGO_SUPERUSER_* environment variables are set
    if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
        log_info "Creating superuser from environment variables..."
        python manage.py createsuperuser --noinput || log_warning "Superuser creation failed or already exists"
    else
        log_warning "No superuser environment variables found. You may need to create a superuser manually."
    fi
}

# Function to validate Django settings
validate_settings() {
    log_info "Validating Django settings..."
    python manage.py check --deploy || log_error "Django settings validation failed!"
    log_success "Django settings are valid!"
}

# Function to warm up the application
warmup() {
    log_info "Warming up the application..."
    python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myblog.settings')
django.setup()
from django.core.cache import cache
from django.contrib.auth.models import User
# Warm up database connections
User.objects.exists()
# Warm up cache
try:
    cache.set('warmup', 'ok', 60)
except:
    pass  # Cache might not be available
print('Application warmed up successfully!')
" || log_warning "Warmup failed, but continuing..."
    log_success "Application is ready!"
}

# Main entrypoint logic
main() {
    log_info "Starting BlogSpace application..."
    
    # Wait for external services
    if [ "$DATABASE_URL" != "sqlite:///db.sqlite3" ]; then
        wait_for_db
    fi
    wait_for_redis
    
    # Prepare Django application
    run_migrations
    collect_static
    create_cache_table
    
    # Validate settings in production
    if [ "$DEBUG" = "False" ] || [ "$DEBUG" = "false" ]; then
        validate_settings
    fi
    
    # Create superuser if environment variables are provided
    check_superuser
    
    # Warm up the application
    warmup
    
    log_success "BlogSpace is ready to serve requests!"
    
    # Execute the main command
    exec "$@"
}

# Run main function with all arguments
main "$@"
