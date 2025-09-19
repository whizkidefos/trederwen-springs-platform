# Trederwen Springs E-commerce Platform

A modern, AI-powered e-commerce platform for premium Welsh spring water with subscription capabilities, built with Django and TailwindCSS.

## Features

### 🛒 E-commerce Core
- **Product Catalog**: Comprehensive product management with categories, variants, and detailed specifications
- **Shopping Cart**: Session-based cart with AJAX updates and persistent storage
- **Checkout Process**: Secure payment processing with Stripe integration
- **Order Management**: Complete order lifecycle from placement to delivery
- **Inventory Tracking**: Real-time stock management with low-stock alerts

### 🔄 Subscription System
- **Flexible Plans**: Weekly, monthly, and quarterly subscription options
- **Customer Control**: Easy pause, resume, and modification of subscriptions
- **Automated Billing**: Recurring payments with Stripe subscriptions
- **Delivery Scheduling**: Customizable delivery preferences and timing
- **Subscription Analytics**: Detailed insights for business optimization

### 🤖 AI-Powered Recommendations
- **Personalized Suggestions**: ML-driven product recommendations based on user behavior
- **Collaborative Filtering**: Recommendations based on similar user preferences
- **Content-Based Filtering**: Product similarity matching
- **Trending Analysis**: Real-time trending product identification
- **Cross-sell Optimization**: Smart frequently-bought-together suggestions

### 📝 Content Management
- **Blog System**: Full-featured blog with categories, tags, and SEO optimization
- **Recipe Integration**: Special recipe content type with ingredient lists and instructions
- **Newsletter Management**: Email subscription and campaign management
- **SEO Optimization**: Meta tags, structured data, and search-friendly URLs

### 👥 User Management
- **Custom User Model**: Extended user profiles with preferences and analytics
- **Address Management**: Multiple shipping and billing addresses
- **Order History**: Complete purchase history and tracking
- **Wishlist**: Save products for later purchase
- **User Analytics**: Behavior tracking for personalization

### 📊 Analytics & Reporting
- **Sales Analytics**: Revenue tracking and performance metrics
- **User Behavior**: Detailed activity logging and analysis
- **Product Performance**: View counts, conversion rates, and popularity metrics
- **Subscription Metrics**: Churn analysis and retention insights

### 🎨 Modern UI/UX
- **Responsive Design**: Mobile-first approach with TailwindCSS
- **Interactive Elements**: Alpine.js for dynamic user interactions
- **Modern Aesthetics**: Clean, professional design inspired by premium brands
- **Performance Optimized**: Fast loading times and smooth animations

## Technology Stack

### Backend
- **Django 4.2**: Python web framework
- **PostgreSQL**: Production database (SQLite for development)
- **Redis**: Caching and session storage
- **Celery**: Background task processing
- **Stripe**: Payment processing

### Frontend
- **TailwindCSS**: Utility-first CSS framework
- **Alpine.js**: Lightweight JavaScript framework
- **HTML5/CSS3**: Modern web standards
- **Responsive Design**: Mobile-first approach

### AI/ML
- **scikit-learn**: Machine learning algorithms
- **pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing

### DevOps & Deployment
- **Gunicorn**: WSGI HTTP Server
- **WhiteNoise**: Static file serving
- **Django Debug Toolbar**: Development debugging
- **Environment Variables**: Secure configuration management

## Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 14+ (for TailwindCSS development)
- Redis Server
- PostgreSQL (for production)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd trederwen-springs
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment setup**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Database setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create initial data**
   ```bash
   python manage.py setup_initial_data --with-sample-data
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run development server**
   ```bash
   python manage.py runserver
   ```

Visit `http://localhost:8000` to see the application.

### Admin Access
- URL: `http://localhost:8000/admin/`
- Default credentials: admin/admin123 (if using sample data)

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key
STRIPE_SECRET_KEY=sk_test_your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Redis (for production)
REDIS_URL=redis://127.0.0.1:6379/1

# AI Recommendations
AI_RECOMMENDATIONS_ENABLED=True
```

### Production Deployment

For production deployment, update the following:

1. **Database**: Switch to PostgreSQL
2. **Static Files**: Configure AWS S3 or similar
3. **Email**: Setup SMTP service
4. **Caching**: Configure Redis
5. **Security**: Update security settings
6. **Environment**: Set `DEBUG=False`

## Project Structure

```
trederwen_springs/
├── core/                   # Core functionality and homepage
├── products/              # Product catalog and management
├── orders/                # Order processing and management
├── users/                 # User authentication and profiles
├── subscriptions/         # Subscription management
├── ai_recommendations/    # AI-powered recommendation engine
├── blog/                  # Content management system
├── static/                # Static files (CSS, JS, images)
├── templates/             # HTML templates
├── media/                 # User uploaded files
├── requirements.txt       # Python dependencies
├── manage.py             # Django management script
└── README.md             # This file
```

## Key Features Detail

### Product Management
- **Categories & Brands**: Hierarchical organization
- **Variants**: Size, flavor, and other product variations
- **Images**: Multiple product images with optimization
- **Reviews**: Customer review system with moderation
- **Tags**: Flexible product tagging system
- **SEO**: Search engine optimization features

### Order Processing
- **Multi-step Checkout**: Streamlined purchase process
- **Payment Options**: Credit cards, digital wallets via Stripe
- **Shipping Methods**: Multiple delivery options
- **Order Tracking**: Real-time status updates
- **Refunds**: Automated refund processing

### Subscription Features
- **Flexible Billing**: Weekly, monthly, quarterly plans
- **Pause/Resume**: Customer control over subscriptions
- **Delivery Scheduling**: Preferred delivery dates and times
- **Automatic Payments**: Secure recurring billing
- **Cancellation**: Easy subscription management

### AI Recommendations
- **Behavioral Tracking**: User activity monitoring
- **Similarity Analysis**: Product-to-product recommendations
- **Trending Detection**: Real-time popularity analysis
- **Cross-selling**: Smart product combinations
- **Personalization**: Individual user preferences

## API Endpoints

### Core APIs
- `/api/cart/` - Cart management
- `/api/recommendations/` - Product recommendations
- `/api/search/` - Product search
- `/api/newsletter/` - Newsletter subscription

### Admin APIs
- `/admin/` - Django admin interface
- `/api/analytics/` - Business analytics (admin only)

## Testing

Run the test suite:

```bash
python manage.py test
```

For coverage report:
```bash
coverage run --source='.' manage.py test
coverage report
```

## Development

### Adding New Features

1. **Create Django App**: `python manage.py startapp app_name`
2. **Add to INSTALLED_APPS**: Update settings.py
3. **Create Models**: Define data models
4. **Create Migrations**: `python manage.py makemigrations`
5. **Apply Migrations**: `python manage.py migrate`
6. **Create Views**: Implement business logic
7. **Add URLs**: Configure routing
8. **Create Templates**: Design user interface

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions and classes
- Keep functions small and focused
- Use type hints where applicable

### Database Management

```bash
# Create new migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Rollback migration
python manage.py migrate app_name 0001
```

## Deployment

### Production