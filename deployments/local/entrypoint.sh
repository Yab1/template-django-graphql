#!/bin/sh
set -e

echo "Waiting for database..."
sleep 10

# Apply database migrations
echo "Applying database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser if it doesn't exist (for local development)
echo "Creating superuser if it doesn't exist..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser created: admin/admin')
else:
    print('Superuser already exists')
EOF

# Start main Django app on port 8000
echo "Starting main Django app on port 8000..."
python manage.py runserver 0.0.0.0:8000
