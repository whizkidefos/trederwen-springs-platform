#!/bin/bash

# Trederwen Springs Development Server Startup Script
# This script sets up and runs the development environment

echo "🏔️  Trederwen Springs E-commerce Platform"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating environment file..."
    cp .env.example .env
    echo "✏️  Please edit .env file with your configuration"
fi

# Create logs directory
mkdir -p logs

# Database setup
echo "🗄️  Setting up database..."
python manage.py makemigrations core
python manage.py makemigrations users
python manage.py makemigrations products
python manage.py makemigrations orders
python manage.py makemigrations subscriptions
python manage.py makemigrations ai_recommendations
python manage.py makemigrations blog

python manage.py migrate

# Check if we should create initial data
read -p "📊 Create initial data and sample content? (y/n): " create_data
if [[ $create_data == "y" || $create_data == "Y" ]]; then
    echo "🌱 Creating initial data..."
    python manage.py setup_initial_data --with-sample-data
fi

# Check if superuser exists
echo "👤 Checking for admin user..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('No admin user found. Please create one:')
    exit(1)
else:
    admin = User.objects.filter(is_superuser=True).first()
    print(f'Admin user exists: {admin.email}')
"

if [ $? -eq 1 ]; then
    echo "🔐 Creating admin user..."
    python manage.py createsuperuser
fi

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start development server
echo ""
echo "🚀 Starting development server..."
echo "📱 Website: http://localhost:8000"
echo "🔧 Admin: http://localhost:8000/admin"
echo "📚 API Docs: http://localhost:8000/api/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Use different commands for different OS
if command -v python3 &> /dev/null; then
    python3 manage.py runserver 0.0.0.0:8000
else
    python manage.py runserver 0.0.0.0:8000
fi