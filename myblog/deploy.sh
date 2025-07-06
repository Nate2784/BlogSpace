#!/bin/bash

# BlogSpace Deployment Script
# This script helps deploy the BlogSpace application using Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed."
}

# Function to create .env file if it doesn't exist
setup_env() {
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from .env.example..."
        if [ -f .env.example ]; then
            cp .env.example .env
            print_warning "Please edit .env file with your configuration before proceeding."
            read -p "Press Enter to continue after editing .env file..."
        else
            print_error ".env.example file not found. Please create .env file manually."
            exit 1
        fi
    else
        print_success ".env file found."
    fi
}

# Function to build Docker images
build_images() {
    print_status "Building Docker images..."
    docker-compose build --no-cache
    print_success "Docker images built successfully."
}

# Function to start services
start_services() {
    local env_file=${1:-"docker-compose.yml"}
    print_status "Starting services using $env_file..."
    
    if [ "$env_file" = "docker-compose.dev.yml" ]; then
        docker-compose -f docker-compose.dev.yml up -d
    else
        docker-compose up -d
    fi
    
    print_success "Services started successfully."
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    docker-compose exec web python manage.py migrate
    print_success "Database migrations completed."
}

# Function to create superuser
create_superuser() {
    print_status "Creating Django superuser..."
    docker-compose exec web python manage.py createsuperuser
}

# Function to collect static files
collect_static() {
    print_status "Collecting static files..."
    docker-compose exec web python manage.py collectstatic --noinput
    print_success "Static files collected."
}

# Function to show logs
show_logs() {
    docker-compose logs -f
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    docker-compose down
    print_success "Services stopped."
}

# Function to clean up
cleanup() {
    print_status "Cleaning up Docker resources..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    print_success "Cleanup completed."
}

# Function to show status
show_status() {
    print_status "Service status:"
    docker-compose ps
}

# Main menu
show_menu() {
    echo ""
    echo "=== BlogSpace Deployment Menu ==="
    echo "1. Development deployment"
    echo "2. Production deployment"
    echo "3. Build images"
    echo "4. Run migrations"
    echo "5. Create superuser"
    echo "6. Collect static files"
    echo "7. Show logs"
    echo "8. Show status"
    echo "9. Stop services"
    echo "10. Cleanup"
    echo "0. Exit"
    echo ""
}

# Main script
main() {
    print_status "BlogSpace Deployment Script"
    
    # Check prerequisites
    check_docker
    setup_env
    
    while true; do
        show_menu
        read -p "Choose an option: " choice
        
        case $choice in
            1)
                print_status "Starting development deployment..."
                build_images
                start_services "docker-compose.dev.yml"
                run_migrations
                print_success "Development deployment completed!"
                print_status "Application is running at http://localhost:8000"
                ;;
            2)
                print_status "Starting production deployment..."
                build_images
                start_services "docker-compose.yml"
                run_migrations
                collect_static
                print_success "Production deployment completed!"
                print_status "Application is running at http://localhost:8000"
                ;;
            3)
                build_images
                ;;
            4)
                run_migrations
                ;;
            5)
                create_superuser
                ;;
            6)
                collect_static
                ;;
            7)
                show_logs
                ;;
            8)
                show_status
                ;;
            9)
                stop_services
                ;;
            10)
                cleanup
                ;;
            0)
                print_status "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid option. Please try again."
                ;;
        esac
    done
}

# Run main function
main "$@"
