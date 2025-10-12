#!/bin/bash
set -Eeuo pipefail
IFS=$'\n\t'

PROJECT_NAME="django-template-graphql-local"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env.local"

# Use Jenkins WORKSPACE if set, otherwise stay in current dir
cd "${WORKSPACE:-$(pwd)}"

echo ">>> Creating local .env file..."
cat > "$ENV_FILE" << 'EOF'
# Local Development Environment
DEBUG=True
SECRET_KEY=local-development-secret-key-change-in-production
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/django_template_local
REDIS_URL=redis://redis:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
EOF

# Speed up builds and better caching
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Ensure external network used by compose exists
docker network inspect django_template_local_network >/dev/null 2>&1 || docker network create django_template_local_network

echo ">>> Starting local deployment..."

# Cleanup previous deployment
echo ">>> Stopping running containers..."
docker compose -p "$PROJECT_NAME" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" down --remove-orphans || true
docker image prune -f || true

# Build Docker images
echo ">>> Building Docker images (with cache, parallel)..."
docker compose -p "$PROJECT_NAME" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build --parallel

# Tag the main django app image with commit hash for tracking
CURRENT_COMMIT=$(git rev-parse HEAD)
MAIN_IMAGE="${PROJECT_NAME}-django_app:latest"
if docker image inspect "$MAIN_IMAGE" >/dev/null 2>&1; then
    docker tag "$MAIN_IMAGE" "${MAIN_IMAGE%:latest}:${CURRENT_COMMIT}"
    echo "✅ Image built and tagged with commit: $CURRENT_COMMIT"
fi

echo ">>> Starting services..."
docker compose -p "$PROJECT_NAME" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d

echo ">>> Service status:"
docker compose -p "$PROJECT_NAME" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps

# Wait for services to start
echo ">>> Waiting for services to start..."
sleep 30

# Health checks
echo ">>> Performing health checks..."
for i in {1..10}; do
    if curl -f http://localhost:8000/ || curl -f http://localhost:8000/admin/; then
        echo "✅ Django application is responding"
        break
    else
        echo "Attempt $i: Django not ready yet, waiting..."
        sleep 10
    fi
done

# Run migrations
echo ">>> Running database migrations..."
docker compose -p "$PROJECT_NAME" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T django_app python manage.py migrate --verbosity=2

# Collect static files
echo ">>> Collecting static files..."
docker compose -p "$PROJECT_NAME" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T django_app python manage.py collectstatic --noinput --verbosity=2

# Run tests
echo ">>> Running tests..."
docker compose -p "$PROJECT_NAME" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T django_app python manage.py test --verbosity=2 || echo "⚠️ Tests failed but continuing..."

echo ""
echo "🎉 Local deployment complete!"
echo "Django app: http://localhost:8000"
echo "Admin panel: http://localhost:8000/admin/ (admin/admin)"
echo "Flower monitoring: http://localhost:5555"
echo "PostgreSQL: localhost:5432 (postgres/postgres)"
echo "Redis: localhost:6379"
echo ""
echo "To stop services: docker compose -p $PROJECT_NAME --env-file $ENV_FILE -f $COMPOSE_FILE down"
