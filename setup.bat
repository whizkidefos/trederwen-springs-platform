@echo off
echo 🏔️  Trederwen Springs - Windows Setup
echo =====================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo ✓ Python is installed

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📚 Installing dependencies...
pip install -r requirements.txt

REM Run setup script
echo 🛠️  Running setup script...
python setup.py

REM Create Django apps
echo 🏗️  Creating Django apps...
python manage.py startapp core
python manage.py startapp users  
python manage.py startapp products
python manage.py startapp orders
python manage.py startapp subscriptions
python manage.py startapp ai_recommendations
python manage.py startapp blog

echo 📋 Moving model files to apps...
REM You'll need to move the model files manually to each app

echo 🗄️  Setting up database...
python manage.py makemigrations
python manage.py migrate

echo 🌱 Creating initial data...
python manage.py setup_initial_data --with-sample-data

echo 👤 Creating superuser...
python manage.py createsuperuser

echo 📁 Collecting static files...
python manage.py collectstatic --noinput

echo.
echo ✅ Setup completed successfully!
echo.
echo 🚀 Starting development server...
echo 📱 Website: http://localhost:8000
echo 🔧 Admin: http://localhost:8000/admin
echo.
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver