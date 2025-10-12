# Django GraphQL Deployment Guide

This guide covers the deployment setup for the Django GraphQL project using Docker and Jenkins.

## Project Structure

```
deployments/
├── local/                    # Local development environment
├── development/              # Development/staging environment  
├── production/               # Production environment
└── shared/                  # Shared utilities (if needed)
```

## Environment-Specific Deployment

### Local Development Environment

**Location**: `deployments/local/`

**Services**:
- Django App: http://localhost:8000
- Admin Panel: http://localhost:8000/admin/ (admin/admin)
- Flower Monitoring: http://localhost:5555
- PostgreSQL: localhost:5432 (postgres/postgres)
- Redis: localhost:6379

**Quick Start**:
```bash
cd deployments/local
docker compose up -d --build
```

**Manual Deployment Script**:
```bash
cd deployments/local
./deploy.sh
```

### Development Environment

**Location**: `deployments/development/`

**Services**:
- Django App: http://localhost:8007
- Admin Panel: http://localhost:8007/admin/ (admin/admin)
- Flower Monitoring: http://localhost:5557
- PostgreSQL: localhost:5432 (postgres/postgres)
- Redis: localhost:6379

**Quick Start**:
```bash
cd deployments/development
docker compose up -d --build
```

### Production Environment

**Location**: `deployments/production/`

**Services**: Configured for production with appropriate security settings.

## Jenkins Integration

### Setting Up Jenkins Jobs

1. **Local Jenkins Job**:
   - Pipeline script: `deployments/local/Jenkinsfile`
   - Purpose: Local development testing

2. **Development Jenkins Job**:
   - Pipeline script: `deployments/development/Jenkinsfile`
   - Purpose: Development/staging deployment

3. **Production Jenkins Job**:
   - Pipeline script: `deployments/production/Jenkinsfile`
   - Purpose: Production deployment

### Jenkins Pipeline Features

- **Smart Caching**: Only rebuilds Docker images when code changes
- **Health Checks**: Verifies all services are running
- **Database Migrations**: Automatically runs migrations
- **Static Files**: Collects static files
- **Testing**: Runs Django tests
- **Logging**: Shows service logs for debugging

## Docker Configuration

### Services Included

Each environment includes:
- **Django Application**: Main web application
- **PostgreSQL**: Database
- **Redis**: Caching and Celery broker
- **Celery Worker**: Background task processing
- **Celery Beat**: Scheduled task management
- **Flower**: Celery monitoring interface

### Network Configuration

- **Local**: `django_template_local_network`
- **Development**: `django_template_dev_network`
- **Production**: `django_template_prod_network`

## Environment Variables

### Local Environment
```bash
DEBUG=True
SECRET_KEY=local-development-secret-key
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/django_template_local
REDIS_URL=redis://redis:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

### Development Environment
```bash
DEBUG=True
SECRET_KEY=development-secret-key
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/django_template_dev
REDIS_URL=redis://redis:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,dev.example.com
```

### Production Environment
```bash
DEBUG=False
SECRET_KEY=production-secret-key
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://host:port/0
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## Deployment Commands

### Start Services
```bash
# Local
cd deployments/local
docker compose up -d

# Development
cd deployments/development
docker compose up -d

# Production
cd deployments/production
docker compose up -d
```

### Stop Services
```bash
# Local
cd deployments/local
docker compose down

# Development
cd deployments/development
docker compose down

# Production
cd deployments/production
docker compose down
```

### View Logs
```bash
# View all service logs
docker compose logs

# View specific service logs
docker compose logs django_app
docker compose logs postgres
docker compose logs redis
```

### Run Commands in Containers
```bash
# Django shell
docker compose exec django_app python manage.py shell

# Database migrations
docker compose exec django_app python manage.py migrate

# Create superuser
docker compose exec django_app python manage.py createsuperuser

# Collect static files
docker compose exec django_app python manage.py collectstatic
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**: Ensure ports 8000, 8007, 5432, 6379, 5555, 5557 are available
2. **Network Issues**: Check if Docker networks exist
3. **Database Connection**: Verify PostgreSQL is running and accessible
4. **Redis Connection**: Verify Redis is running and accessible

### Debugging Commands

```bash
# Check running containers
docker compose ps

# Check container logs
docker compose logs --tail=50

# Check network connectivity
docker compose exec django_app ping postgres
docker compose exec django_app ping redis

# Check database connection
docker compose exec postgres pg_isready -U postgres

# Check Redis connection
docker compose exec redis redis-cli ping
```

## Security Considerations

### Production Environment
- Use strong, unique secret keys
- Configure proper database credentials
- Set up SSL/TLS certificates
- Configure firewall rules
- Use environment-specific settings
- Enable security headers
- Configure CORS properly

### Environment Variables
- Never commit sensitive data to version control
- Use environment-specific .env files
- Rotate secrets regularly
- Use secret management systems in production

## Monitoring and Maintenance

### Health Checks
- Django application responsiveness
- Database connectivity
- Redis connectivity
- Celery worker status
- Service logs monitoring

### Regular Maintenance
- Update dependencies
- Backup database
- Monitor disk space
- Review logs
- Update security patches

## Best Practices

1. **Environment Isolation**: Keep environments completely separate
2. **Configuration Management**: Use environment-specific configs
3. **Secret Management**: Never hardcode secrets
4. **Monitoring**: Set up proper logging and monitoring
5. **Backup Strategy**: Regular database and file backups
6. **Security**: Regular security updates and audits
7. **Documentation**: Keep deployment docs updated
8. **Testing**: Test deployments in development first

## Support

For deployment issues:
1. Check service logs
2. Verify network connectivity
3. Check environment variables
4. Review Docker configuration
5. Consult this deployment guide

