#!/bin/bash

# BlogSpace Container Build Script
# This script provides easy commands for building and managing containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_header() {
    echo -e "${PURPLE}[BLOGSPACE]${NC} $1"
}

# Function to show usage
show_usage() {
    echo -e "${CYAN}BlogSpace Container Build Script${NC}"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build-dev     Build development image"
    echo "  build-prod    Build production image"
    echo "  dev           Start development environment"
    echo "  prod          Start production environment"
    echo "  stop          Stop all containers"
    echo "  clean         Clean up containers and images"
    echo "  logs          Show container logs"
    echo "  shell         Open shell in web container"
    echo "  test          Run tests in container"
    echo "  migrate       Run database migrations"
    echo "  collectstatic Collect static files"
    echo "  backup        Backup database"
    echo "  restore       Restore database"
    echo "  health        Check container health"
    echo ""
    echo "Options:"
    echo "  --no-cache    Build without cache"
    echo "  --verbose     Verbose output"
    echo "  --help        Show this help message"
}

# Function to build development image
build_dev() {
    log_header "Building BlogSpace Development Image"
    
    if [[ "$1" == "--no-cache" ]]; then
        log_info "Building without cache..."
        docker build --no-cache --target development -t blogspace:dev .
    else
        docker build --target development -t blogspace:dev .
    fi
    
    log_success "Development image built successfully!"
}

# Function to build production image
build_prod() {
    log_header "Building BlogSpace Production Image"
    
    if [[ "$1" == "--no-cache" ]]; then
        log_info "Building without cache..."
        docker build --no-cache -t blogspace:latest .
    else
        docker build -t blogspace:latest .
    fi
    
    log_success "Production image built successfully!"
}

# Function to start development environment
start_dev() {
    log_header "Starting BlogSpace Development Environment"
    
    # Check if we want Redis
    if [[ "$1" == "--with-redis" ]]; then
        log_info "Starting with Redis..."
        docker-compose -f docker-compose.dev.yml --profile with-redis up -d
    else
        docker-compose -f docker-compose.dev.yml up -d
    fi
    
    log_success "Development environment started!"
    log_info "Access the application at: http://localhost:8000"
}

# Function to start production environment
start_prod() {
    log_header "Starting BlogSpace Production Environment"
    
    # Check if we want full production stack
    if [[ "$1" == "--full" ]]; then
        log_info "Starting full production stack with Nginx and Celery..."
        docker-compose --profile production up -d
    else
        docker-compose up -d
    fi
    
    log_success "Production environment started!"
    log_info "Access the application at: http://localhost:8000"
}

# Function to stop containers
stop_containers() {
    log_header "Stopping BlogSpace Containers"
    
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    docker-compose down 2>/dev/null || true
    
    log_success "All containers stopped!"
}

# Function to clean up
cleanup() {
    log_header "Cleaning Up BlogSpace Containers and Images"
    
    # Stop containers
    stop_containers
    
    # Remove containers
    docker-compose -f docker-compose.dev.yml down --volumes --remove-orphans 2>/dev/null || true
    docker-compose down --volumes --remove-orphans 2>/dev/null || true
    
    # Remove images
    docker rmi blogspace:dev blogspace:latest 2>/dev/null || true
    
    # Prune system
    docker system prune -f
    
    log_success "Cleanup completed!"
}

# Function to show logs
show_logs() {
    log_header "BlogSpace Container Logs"
    
    if docker-compose ps | grep -q "Up"; then
        docker-compose logs -f --tail=100
    elif docker-compose -f docker-compose.dev.yml ps | grep -q "Up"; then
        docker-compose -f docker-compose.dev.yml logs -f --tail=100
    else
        log_error "No running containers found!"
        exit 1
    fi
}

# Function to open shell
open_shell() {
    log_header "Opening Shell in BlogSpace Web Container"
    
    if docker-compose ps web | grep -q "Up"; then
        docker-compose exec web bash
    elif docker-compose -f docker-compose.dev.yml ps web | grep -q "Up"; then
        docker-compose -f docker-compose.dev.yml exec web bash
    else
        log_error "Web container is not running!"
        exit 1
    fi
}

# Function to run tests
run_tests() {
    log_header "Running BlogSpace Tests"
    
    if docker-compose ps web | grep -q "Up"; then
        docker-compose exec web python manage.py test
    elif docker-compose -f docker-compose.dev.yml ps web | grep -q "Up"; then
        docker-compose -f docker-compose.dev.yml exec web python manage.py test
    else
        log_error "Web container is not running!"
        exit 1
    fi
}

# Function to run migrations
run_migrations() {
    log_header "Running Database Migrations"
    
    if docker-compose ps web | grep -q "Up"; then
        docker-compose exec web python manage.py migrate
    elif docker-compose -f docker-compose.dev.yml ps web | grep -q "Up"; then
        docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
    else
        log_error "Web container is not running!"
        exit 1
    fi
}

# Function to collect static files
collect_static() {
    log_header "Collecting Static Files"
    
    if docker-compose ps web | grep -q "Up"; then
        docker-compose exec web python manage.py collectstatic --noinput
    elif docker-compose -f docker-compose.dev.yml ps web | grep -q "Up"; then
        docker-compose -f docker-compose.dev.yml exec web python manage.py collectstatic --noinput
    else
        log_error "Web container is not running!"
        exit 1
    fi
}

# Function to check health
check_health() {
    log_header "Checking Container Health"
    
    if docker-compose ps | grep -q "Up"; then
        docker-compose ps
        echo ""
        log_info "Checking application health..."
        curl -f http://localhost:8000/health/ 2>/dev/null && log_success "Application is healthy!" || log_warning "Health check failed"
    elif docker-compose -f docker-compose.dev.yml ps | grep -q "Up"; then
        docker-compose -f docker-compose.dev.yml ps
        echo ""
        log_info "Checking application health..."
        curl -f http://localhost:8000/ 2>/dev/null && log_success "Application is healthy!" || log_warning "Health check failed"
    else
        log_error "No containers are running!"
        exit 1
    fi
}

# Main script logic
case "$1" in
    "build-dev")
        build_dev "$2"
        ;;
    "build-prod")
        build_prod "$2"
        ;;
    "dev")
        start_dev "$2"
        ;;
    "prod")
        start_prod "$2"
        ;;
    "stop")
        stop_containers
        ;;
    "clean")
        cleanup
        ;;
    "logs")
        show_logs
        ;;
    "shell")
        open_shell
        ;;
    "test")
        run_tests
        ;;
    "migrate")
        run_migrations
        ;;
    "collectstatic")
        collect_static
        ;;
    "health")
        check_health
        ;;
    "--help"|"help"|"")
        show_usage
        ;;
    *)
        log_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
