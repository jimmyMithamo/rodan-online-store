# Rodan Phones E-commerce API

A comprehensive Django REST Framework e-commerce platform for mobile phone retail with advanced features including cart management, order processing, payment integration, and extensive product search capabilities.

## Project Overview

This is a modern e-commerce API built with Django REST Framework featuring:

- **Modular Architecture**: Separated apps for different business concerns
- **JWT Authentication**: Secure token-based authentication
- **Advanced Product Search**: Multiple search endpoints and filtering options
- **Shopping Cart Management**: Full cart lifecycle with item management
- **Order Processing**: Complete order workflow with payment integration
- **Audit Logging**: Comprehensive activity tracking
- **API Documentation**: Complete endpoint documentation with examples

## Architecture

### App Structure

```
core/              # Audit logging and system-wide utilities
payments/          # Payment processing and transaction management
order_management/  # Order processing and coupon management
cart_management/   # Shopping cart and cart item management
product_management/# Product catalog, categories, reviews
user_management/   # User authentication and profile management
```

### Key Features

- **Multi-app Django architecture** for separation of concerns
- **Cart-to-Order conversion** workflow
- **Advanced product filtering** by price, brand, category, availability
- **JWT-based authentication** with refresh tokens
- **Comprehensive audit logging** for all user actions
- **Payment method flexibility** (M-Pesa, Card, Bank Transfer)
- **Product review system** with ratings
- **Shipping address management**

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd rodan-phones-ecommerce/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (optional)
python manage.py loaddata fixtures/sample_data.json
```

### 3. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

## API Documentation

### Complete Documentation

- **[API Documentation](API_DOCUMENTATION.md)** - Comprehensive guide with all endpoints, request/response examples
- **[Quick Reference](API_QUICK_REFERENCE.md)** - Developer quick reference guide
- **[Postman Collection](Rodan_Phones_API.postman_collection.json)** - Import into Postman for testing

### Authentication

All endpoints (except registration and login) require JWT authentication:

```bash
# Login to get token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Use token in subsequent requests
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/products/
```

### Key Endpoints

| Category     | Endpoint                             | Description              |
| ------------ | ------------------------------------ | ------------------------ |
| **Auth**     | `POST /api/auth/login/`              | User login               |
| **Products** | `GET /api/products/`                 | List all products        |
| **Products** | `GET /api/products/search/`          | Advanced product search  |
| **Products** | `GET /api/products/pocket_friendly/` | Budget-friendly products |
| **Products** | `GET /api/products/high_end/`        | Premium products         |
| **Cart**     | `GET /api/cart/`                     | Get user's cart          |
| **Cart**     | `POST /api/cart/add_item/`           | Add item to cart         |
| **Orders**   | `POST /api/orders/create_from_cart/` | Convert cart to order    |
| **Payments** | `POST /api/payments/`                | Process payment          |

## Advanced Features

### Product Search & Filtering

```bash
# Search with multiple parameters
GET /api/products/search/?q=iphone&min_price=50000&max_price=200000&brand=Apple&in_stock=true

# Filter by category
GET /api/products/by_category/?category_name=smartphones

# Price range filtering
GET /api/products/price_range/?min_price=10000&max_price=50000
```

### Cart Management

```bash
# Add item to cart
POST /api/cart/add_item/
{
    "product_id": 1,
    "product_variation_id": 2,
    "quantity": 1
}

# Update quantity
POST /api/cart/update_item/
{
    "product_id": 1,
    "product_variation_id": 2,
    "quantity": 3
}
```

### Order Processing

```bash
# Create order from cart
POST /api/orders/create_from_cart/
{
    "shipping_first_name": "John",
    "shipping_last_name": "Doe",
    "shipping_email": "john@example.com",
    "shipping_phone": "+254700000000",
    "shipping_address_line_1": "123 Main Street",
    "shipping_city": "Nairobi",
    "payment_method": "mpesa",
    "shipping_cost": "200.00",
    "tax_amount": "180.00"
}
```

## Development

### Project Structure

```
backend/
├── rodan_phones_backend/     # Django project settings
├── core/                     # Audit logging app
├── payments/                 # Payment processing app
├── order_management/         # Order processing app
├── cart_management/          # Shopping cart app
├── product_management/       # Product catalog app
├── user_management/          # User authentication app
├── requirements.txt
├── manage.py
└── API_DOCUMENTATION.md
```

### Key Models

- **Product**: Core product information with variations and pricing
- **Cart/CartItem**: Shopping cart functionality
- **Order/OrderItem**: Order processing and fulfillment
- **Payment**: Payment processing and tracking
- **AuditLog**: System-wide activity logging
- **Review**: Product reviews and ratings

### Testing

```bash
# Run tests
python manage.py test

# Run specific app tests
python manage.py test product_management
python manage.py test cart_management
```

### API Testing with Postman

1. Import the Postman collection: `Rodan_Phones_API.postman_collection.json`
2. Set the `baseUrl` variable to your API URL (default: `http://localhost:8000/api`)
3. Use the "Login" request to authenticate and automatically set the auth token
4. Test all endpoints with pre-configured request examples

## Production Deployment

### Environment Variables

Create a `.env` file:

```
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
ALLOWED_HOSTS=yourdomain.com
```

### Database Configuration

For production, update `settings.py` to use PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'rodan_phones',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Security Checklist

- [ ] Update `SECRET_KEY` for production
- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up HTTPS
- [ ] Configure CORS headers
- [ ] Set up rate limiting
- [ ] Configure logging
- [ ] Set up monitoring

## API Response Format

All API responses follow a consistent format:

### Success Response

```json
{
  "status": "success",
  "data": {
    // Response data here
  },
  "message": "Operation completed successfully"
}
```

### Error Response

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field_name": ["Error message"]
    }
  }
}
```

### Pagination

```json
{
  "count": 150,
  "next": "http://localhost:8000/api/products/?page=2",
  "previous": null,
  "results": [
    // Array of items
  ]
}
```

## Support

For questions or support:

- Check the [API Documentation](API_DOCUMENTATION.md)
- Review the [Quick Reference Guide](API_QUICK_REFERENCE.md)
- Import the Postman collection for testing
- Create an issue in the repository

## License

This project is licensed under the MIT License - see the LICENSE file for details.
