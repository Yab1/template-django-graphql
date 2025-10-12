# Local Development Environment

This directory contains all configuration files for the local development environment.

## Files

- `Dockerfile` - Container configuration for local development
- `docker-compose.yml` - Service orchestration for local environment
- `entrypoint.sh` - Container startup script
- `Jenkinsfile` - Jenkins pipeline for local deployment
- `deploy.sh` - Manual deployment script

## Quick Start

### Manual Deployment
```bash
cd deployments/local
./deploy.sh
```

### Using Docker Compose Directly
```bash
cd deployments/local
docker compose up -d --build
```

## Services

- **Django App**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/ (admin/admin)
- **Flower Monitoring**: http://localhost:5555
- **PostgreSQL**: localhost:5432 (postgres/postgres)
- **Redis**: localhost:6379

## Environment Variables

The deployment script automatically creates a `.env.local` file with appropriate settings for local development.

## Jenkins Integration

The `Jenkinsfile` can be used to create a Jenkins job for automated local deployment. The pipeline includes:

1. Environment setup
2. Smart Docker image caching
3. Health checks
4. Database migrations
5. Static file collection
6. Test execution

## Stopping Services

```bash
docker compose -p django-template-graphql-local --env-file .env.local -f docker-compose.yml down
```

