#!/usr/bin/env python
"""
Quick setup script for Trederwen Springs platform
Run this before running Django commands
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    base_dir = Path(__file__).resolve().parent
    
    directories = [
        'logs',
        'media',
        'media/avatars',
        'media/products',
        'media/categories',
        'media/brands',
        'media/blog',
        'media/blog/featured',
        'media/blog/images',
        'media/recipes',
        'static',
        'staticfiles',
    ]
    
    print("Creating necessary directories...")
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created {directory}/")

def create_env_file():
    """Create .env file from example if it doesn't exist"""
    base_dir = Path(__file__).resolve().parent
    env_file = base_dir / '.env'
    env_example = base_dir / '.env.example'
    
    if not env_file.exists() and env_example.exists():
        print("Creating .env file from example...")
        with open(env_example, 'r') as example:
            content = example.read()
        
        # Replace some default values for local development
        content = content.replace('your-secret-key-here-change-this-in-production', 
                                'django-insecure-local-development-key-123456789')
        
        with open(env_file, 'w') as env:
            env.write(content)
        print("✓ Created .env file")
    elif env_file.exists():
        print("• .env file already exists")
    else:
        print("⚠ .env.example not found, creating basic .env file")
        basic_env = """DEBUG=True
SECRET_KEY=django-insecure-local-development-key-123456789
DATABASE_URL=sqlite:///db.sqlite3
AI_RECOMMENDATIONS_ENABLED=True
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
"""
        with open(env_file, 'w') as env:
            env.write(basic_env)
        print("✓ Created basic .env file")

def create_init_files():
    """Create __init__.py files for apps"""
    base_dir = Path(__file__).resolve().parent
    
    apps = ['core', 'users', 'products', 'orders', 'subscriptions', 'ai_recommendations', 'blog']
    
    for app in apps:
        app_dir = base_dir / app
        if app_dir.exists():
            init_file = app_dir / '__init__.py'
            if not init_file.exists():
                init_file.touch()
                print(f"✓ Created {app}/__init__.py")
            
            # Create management commands structure
            management_dir = app_dir / 'management'
            commands_dir = management_dir / 'commands'
            
            management_dir.mkdir(exist_ok=True)
            commands_dir.mkdir(exist_ok=True)
            
            (management_dir / '__init__.py').touch()
            (commands_dir / '__init__.py').touch()

def main():
    print("🏔️  Trederwen Springs - Quick Setup")
    print("=" * 40)
    
    try:
        create_directories()
        create_env_file()
        create_init_files()
        
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. python manage.py startapp core")
        print("2. python manage.py startapp users")
        print("3. python manage.py startapp products")
        print("4. python manage.py startapp orders")
        print("5. python manage.py startapp subscriptions")
        print("6. python manage.py startapp ai_recommendations")
        print("7. python manage.py startapp blog")
        print("8. python manage.py makemigrations")
        print("9. python manage.py migrate")
        print("10. python manage.py runserver")
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()