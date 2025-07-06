# BlogSpace Deployment Guide

This guide will help you deploy the BlogSpace application using Docker and Docker Compose.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- Git

## Quick Start

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd myblog
```

### 2. Environment Setup
```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your configuration
nano .env  # or use your preferred editor
```

### 3. Deploy with Script
```bash
# Make the deployment script executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

## Manual Deployment

### Development Deployment

1. **Build and start services:**
```bash
docker-compose -f docker-compose.dev.yml up --build -d
```

2. **Run migrations:**
```bash
docker-compose exec web python manage.py migrate
```

3. **Create superuser:**
```bash
docker-compose exec web python manage.py createsuperuser
```

4. **Access the application:**
   - Open http://localhost:8000 in your browser

### Production Deployment

1. **Update environment variables:**
   - Set `DEBUG=False` in .env
   - Set a strong `SECRET_KEY`
   - Configure database settings
   - Set proper `ALLOWED_HOSTS`

2. **Build and start services:**
```bash
docker-compose up --build -d
```

3. **Run migrations:**
```bash
docker-compose exec web python manage.py migrate
```

4. **Collect static files:**
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

5. **Create superuser:**
```bash
docker-compose exec web python manage.py createsuperuser
```

## Environment Variables

### Required Variables
- `SECRET_KEY`: Django secret key (generate a new one for production)
- `DEBUG`: Set to `False` for production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

### Database Configuration
- `DATABASE_URL`: Full database URL (e.g., postgresql://user:pass@host:port/db)
- `DB_ENGINE`: Database engine
- `DB_NAME`: Database name
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database host
- `DB_PORT`: Database port

### Optional Variables
- `REDIS_URL`: Redis connection URL for caching
- `EMAIL_*`: Email configuration for notifications
- `STATIC_ROOT`: Static files directory
- `MEDIA_ROOT`: Media files directory

## Services

### Web Application (Django)
- **Port:** 8000
- **Health Check:** http://localhost:8000/
- **Logs:** `docker-compose logs web`

### Database (PostgreSQL)
- **Port:** 5432
- **Health Check:** Built-in PostgreSQL health check
- **Data:** Persisted in `postgres_data` volume

### Cache (Redis)
- **Port:** 6379
- **Health Check:** Redis ping command
- **Data:** Persisted in `redis_data` volume

### Reverse Proxy (Nginx) - Production Only
- **Port:** 80, 443
- **Configuration:** `nginx.conf`
- **SSL:** Place certificates in `ssl/` directory

## Useful Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
```

### Execute Commands in Container
```bash
# Django shell
docker-compose exec web python manage.py shell

# Database shell
docker-compose exec web python manage.py dbshell

# Bash shell
docker-compose exec web bash
```

### Database Operations
```bash
# Create migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate

# Load fixtures
docker-compose exec web python manage.py loaddata fixture.json
```

### Backup and Restore
```bash
# Backup database
docker-compose exec db pg_dump -U blogspace_user blogspace > backup.sql

# Restore database
docker-compose exec -T db psql -U blogspace_user blogspace < backup.sql
```

## Monitoring

### Health Checks
All services include health checks that can be monitored:
```bash
docker-compose ps
```

### Resource Usage
```bash
docker stats
```

### Service Status
```bash
docker-compose top
```

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Stop conflicting services
   sudo lsof -i :8000
   sudo kill -9 <PID>
   ```

2. **Permission denied:**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

3. **Database connection error:**
   - Check if PostgreSQL service is running
   - Verify database credentials in .env
   - Ensure database exists

4. **Static files not loading:**
   ```bash
   # Collect static files
   docker-compose exec web python manage.py collectstatic --noinput
   ```

### Reset Everything
```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v --remove-orphans

# Remove all images
docker rmi $(docker images -q)

# Start fresh
docker-compose up --build -d
```

## Security Considerations

### Production Security
1. **Change default passwords**
2. **Use strong SECRET_KEY**
3. **Enable HTTPS with SSL certificates**
4. **Configure firewall rules**
5. **Regular security updates**
6. **Monitor logs for suspicious activity**

### SSL/TLS Setup
1. Obtain SSL certificates (Let's Encrypt recommended)
2. Place certificates in `ssl/` directory
3. Update `nginx.conf` to enable HTTPS
4. Set `SECURE_SSL_REDIRECT=True` in .env

## Scaling

### Horizontal Scaling
```bash
# Scale web service
docker-compose up --scale web=3 -d
```

### Load Balancing
Update `nginx.conf` to include multiple upstream servers.

## Maintenance

### Updates
```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
docker-compose up --build -d
```

### Cleanup
```bash
# Remove unused Docker resources
docker system prune -f

# Remove unused volumes
docker volume prune -f
```

## Support

For issues and questions:
1. Check the logs: `docker-compose logs`
2. Review this documentation
3. Check Docker and Django documentation
4. Create an issue in the repository
