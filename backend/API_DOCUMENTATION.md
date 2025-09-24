# Rodan Phones E-commerce API Documentation

## Table of Contents

1. [Authentication](#authentication)
2. [User Management](#user-management)
3. [Product Management](#product-management)
4. [Cart Management](#cart-management)
5. [Order Management](#order-management)
6. [Payment Management](#payment-management)
7. [Core Services](#core-services)
8. [Error Handling](#error-handling)
9. [Response Formats](#response-formats)

---

## Base URL

```
http://localhost:8000/api/
```

---

## Authentication

### 1. User Registration

**Endpoint:** `POST /api/users/`  
**Authentication:** Not required

**Request Payload:**

```json
{
  "email": "user@example.com",
  "phonenumber": "+254712345678",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Success Response (201 Created):**

```json
{
  "success": true,
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "phonenumber": "+254712345678",
    "first_name": "John",
    "last_name": "Doe",
    "date_joined": "2025-09-18T10:30:00Z"
  },
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 2. User Login

**Endpoint:** `POST /api/auth/login/`  
**Authentication:** Not required

**Request Payload:**

```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Success Response (200 OK):**

```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 3. Token Refresh

**Endpoint:** `POST /api/token/refresh/`  
**Authentication:** Not required

**Request Payload:**

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Success Response (200 OK):**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

## User Management

### 4. Get Current User Profile

**Endpoint:** `GET /api/users/me/`  
**Authentication:** Required

**Success Response (200 OK):**

```json
{
  "success": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "phonenumber": "+254712345678",
    "first_name": "John",
    "last_name": "Doe",
    "date_joined": "2025-09-18T10:30:00Z"
  }
}
```

### 5. Update User Profile

**Endpoint:** `PUT /api/users/{id}/`  
**Authentication:** Required (Own profile only)

**Request Payload:**

```json
{
  "first_name": "John Updated",
  "last_name": "Doe Updated",
  "phonenumber": "+254712345679"
}
```

### 6. Shipping Addresses

#### List Shipping Addresses

**Endpoint:** `GET /api/shipping-addresses/`  
**Authentication:** Required

#### Create Shipping Address

**Endpoint:** `POST /api/shipping-addresses/`  
**Authentication:** Required

**Request Payload:**

```json
{
  "address": "123 Main Street, Apt 4B, Nairobi, Kenya",
  "default_address": true
}
```

#### Update Shipping Address

**Endpoint:** `PUT /api/shipping-addresses/{id}/`  
**Authentication:** Required

#### Delete Shipping Address

**Endpoint:** `DELETE /api/shipping-addresses/{id}/`  
**Authentication:** Required

---

## Product Management

### 7. Products

#### List Products

**Endpoint:** `GET /api/products/`  
**Authentication:** Not required  
**Query Parameters:**

- `page` - Page number for pagination
- `page_size` - Number of items per page
- `search` - Search in product name, description
- `ordering` - Sort by field (e.g., `price`, `-created_at`)

**Success Response:**

```json
{
  "success": true,
  "count": 100,
  "next": "http://localhost:8000/api/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "iPhone 15 Pro",
      "description": "Latest iPhone with advanced features",
      "price": "150000.00",
      "discounted_price": "145000.00",
      "brand": {
        "id": 1,
        "name": "Apple"
      },
      "category": {
        "id": 1,
        "name": "Smartphones"
      },
      "stock_quantity": 25,
      "is_active": true,
      "rating": 4.5,
      "images": [
        {
          "id": 1,
          "image": "/media/products/iphone15pro.jpg",
          "is_primary": true
        }
      ],
      "created_at": "2025-09-18T10:30:00Z"
    }
  ]
}
```

#### Get Product Details

**Endpoint:** `GET /api/products/{id}/`  
**Authentication:** Not required

#### Create Product (Admin Only)

**Endpoint:** `POST /api/products/`  
**Authentication:** Required (Admin)

**Request Payload:**

```json
{
  "name": "Samsung Galaxy S24",
  "description": "Latest Samsung flagship smartphone",
  "price": "120000.00",
  "brand": 2,
  "category": 1,
  "stock_quantity": 30,
  "sku": "SAM-S24-001",
  "product_type": "simple",
  "discount_type": "percentage",
  "discount": "5.00",
  "tags": [1, 2, 3]
}
```

#### Update Product (Admin Only)

**Endpoint:** `PUT /api/products/{id}/`  
**Authentication:** Required (Admin)

#### Delete Product (Admin Only)

**Endpoint:** `DELETE /api/products/{id}/`  
**Authentication:** Required (Admin)

### 8. Product Collections

#### All Product Collections (Recommended)

**Endpoint:** `GET /api/products/product_collections/`  
**Authentication:** Not required  
**Query Parameters:**

- `limit` - Number of products per collection (default: 5)

**Response:**

```json
{
    "success": true,
    "collections": {
        "featured": {
            "title": "Featured Products",
            "description": "Highest rated and most viewed products",
            "products": [
                {
                    "id": 1,
                    "name": "iPhone 15 Pro",
                    "price": "185000.00",
                    "brand": {
                        "id": 1,
                        "name": "Apple"
                    },
                    "category": {
                        "id": 1,
                        "name": "Smartphones"
                    },
                    "rating": 4.8,
                    "stock_quantity": 25,
                    "is_active": true
                }
            ],
            "count": 5
        },
        "best_sellers": {
            "title": "Best Sellers",
            "description": "Our top selling products",
            "products": [...],
            "count": 5
        },
        "new_arrivals": {
            "title": "New Arrivals",
            "description": "Latest products in our catalog",
            "products": [...],
            "count": 5
        },
        "pocket_friendly": {
            "title": "Pocket Friendly",
            "description": "Affordable products for every budget",
            "products": [...],
            "count": 5
        },
        "high_end": {
            "title": "High End",
            "description": "Premium products with top-tier features",
            "products": [...],
            "count": 5
        },
        "latest_accessories": {
            "title": "Latest Accessories",
            "description": "Newest accessories and add-ons",
            "products": [...],
            "count": 5
        }
    },
    "meta": {
        "limit_per_collection": 5,
        "total_collections": 6,
        "endpoints": {
            "featured": "/api/products/featured/",
            "best_sellers": "/api/products/best_sellers/",
            "new_arrivals": "/api/products/new_arrivals/",
            "pocket_friendly": "/api/products/pocket_friendly/",
            "high_end": "/api/products/high_end/",
            "latest_accessories": "/api/products/latest_accessories/"
        }
    },
    "message": "Product collections retrieved successfully"
}
```

#### Individual Collections

#### Best Sellers

**Endpoint:** `GET /api/products/best_sellers/`  
**Authentication:** Not required

#### New Arrivals

**Endpoint:** `GET /api/products/new_arrivals/`  
**Authentication:** Not required

#### Featured Products

**Endpoint:** `GET /api/products/featured/`  
**Authentication:** Not required

#### Pocket-Friendly Products

**Endpoint:** `GET /api/products/pocket_friendly/`  
**Authentication:** Not required

#### High-End Products

**Endpoint:** `GET /api/products/high_end/`  
**Authentication:** Not required

#### Latest Accessories

**Endpoint:** `GET /api/products/latest_accessories/`  
**Authentication:** Not required

### 9. Product Search & Filtering

#### Search Products

**Endpoint:** `GET /api/products/search/`  
**Authentication:** Not required  
**Query Parameters:**

- `q` - Search query (searches name, description, brand, category, tags)
- `min_price` - Minimum price filter
- `max_price` - Maximum price filter
- `brand` - Brand name filter
- `category` - Category name filter
- `in_stock` - Filter for in-stock items (`true`/`false`)

**Example:**

```
GET /api/products/search/?q=iphone&min_price=50000&max_price=200000&brand=Apple&in_stock=true
```

#### Products by Brand

**Endpoint:** `GET /api/products/by_brand/`  
**Authentication:** Not required  
**Query Parameters:**

- `brand` - Brand name (required)

**Example:**

```
GET /api/products/by_brand/?brand=Samsung
```

#### Products by Category

**Endpoint:** `GET /api/products/by_category/`  
**Authentication:** Not required  
**Query Parameters:**

- `category_id` - Category ID
- `category_name` - Category name

**Example:**

```
GET /api/products/by_category/?category_name=smartphones
```

#### Products by Price Range

**Endpoint:** `GET /api/products/price_range/`  
**Authentication:** Not required  
**Query Parameters:**

- `min_price` - Minimum price
- `max_price` - Maximum price

**Example:**

```
GET /api/products/price_range/?min_price=10000&max_price=50000
```

### 10. Product Variations

**Endpoint:** `GET /api/products/{id}/variations/`  
**Authentication:** Not required

### 11. Categories

**Endpoint:** `GET /api/categories/`  
**Authentication:** Not required

#### Create Category (Admin Only)

**Endpoint:** `POST /api/categories/`  
**Authentication:** Required (Admin)

**Request Payload:**

```json
{
  "name": "Smartphones",
  "description": "Mobile phones and smartphones",
  "parent": null
}
```

### 12. Brands

**Endpoint:** `GET /api/brands/`  
**Authentication:** Not required

### 13. Product Reviews

#### List Reviews

**Endpoint:** `GET /api/reviews/`  
**Authentication:** Not required

#### Create Review

**Endpoint:** `POST /api/reviews/`  
**Authentication:** Required

**Request Payload:**

```json
{
  "product": 1,
  "rating": 5,
  "review_text": "Excellent product! Highly recommended.",
  "title": "Amazing Phone"
}
```

---

## Cart Management

### 14. Get Cart

**Endpoint:** `GET /api/cart/`  
**Authentication:** Required

**Success Response:**

```json
{
  "id": 1,
  "user": 1,
  "cart_total": "295000.00",
  "total_items": 3,
  "unique_items_count": 2,
  "items": [
    {
      "id": 1,
      "product": 1,
      "product_variation": null,
      "quantity": 2,
      "unit_price": "145000.00",
      "subtotal": "290000.00",
      "product_name": "iPhone 15 Pro",
      "product_sku": "IPH-15-PRO",
      "is_available": true,
      "product_details": {
        "id": 1,
        "name": "iPhone 15 Pro",
        "price": "150000.00"
      }
    }
  ],
  "created_at": "2025-09-18T10:30:00Z",
  "updated_at": "2025-09-18T11:45:00Z"
}
```

### 15. Add Item to Cart

**Endpoint:** `POST /api/cart/add_item/`  
**Authentication:** Required

**Request Payload:**

```json
{
  "product_id": 1,
  "product_variation_id": 2,
  "quantity": 1
}
```

**Success Response:**

```json
{
    "message": "Item added to cart successfully",
    "cart": {
        "id": 1,
        "cart_total": "145000.00",
        "total_items": 1,
        "items": [...]
    }
}
```

### 16. Update Cart Item

**Endpoint:** `POST /api/cart/update_item/`  
**Authentication:** Required

**Request Payload:**

```json
{
  "product_id": 1,
  "product_variation_id": 2,
  "quantity": 3
}
```

### 17. Remove Item from Cart

**Endpoint:** `POST /api/cart/remove_item/`  
**Authentication:** Required

**Request Payload:**

```json
{
  "product_id": 1,
  "product_variation_id": 2
}
```

### 18. Clear Cart

**Endpoint:** `POST /api/cart/clear/`  
**Authentication:** Required

### 19. Cart Items (CRUD)

#### List Cart Items

**Endpoint:** `GET /api/cart-items/`  
**Authentication:** Required

#### Create Cart Item

**Endpoint:** `POST /api/cart-items/`  
**Authentication:** Required

**Request Payload:**

```json
{
  "product": 1,
  "product_variation": 2,
  "quantity": 1
}
```

#### Update Cart Item

**Endpoint:** `PUT /api/cart-items/{id}/`  
**Authentication:** Required

#### Delete Cart Item

**Endpoint:** `DELETE /api/cart-items/{id}/`  
**Authentication:** Required

---

## Order Management

### 20. Orders

#### List Orders

**Endpoint:** `GET /api/orders/`  
**Authentication:** Required

#### Create Order Directly

**Endpoint:** `POST /api/orders/`  
**Authentication:** Required

**Request Payload:**

```json
{
  "payment_method": "mpesa",
  "shipping_first_name": "John",
  "shipping_last_name": "Doe",
  "shipping_email": "john@example.com",
  "shipping_phone": "+254700000000",
  "shipping_address_line_1": "123 Main Street",
  "shipping_address_line_2": "Apt 4B",
  "shipping_city": "Nairobi",
  "shipping_postal_code": "00100",
  "shipping_country": "Kenya",
  "shipping_cost": "200.00",
  "tax_amount": "180.00",
  "notes": "Please deliver in the morning",
  "coupon_code": "SAVE10",
  "items": [
    {
      "product": 1,
      "product_variation": 2,
      "quantity": 2,
      "unit_price": "145000.00"
    },
    {
      "product": 3,
      "quantity": 1,
      "unit_price": "25000.00"
    }
  ]
}
```

#### Create Order from Cart (Recommended)

**Endpoint:** `POST /api/orders/create_from_cart/`  
**Authentication:** Required

**Request Payload:**

```json
{
  "shipping_first_name": "John",
  "shipping_last_name": "Doe",
  "shipping_email": "john@example.com",
  "shipping_phone": "+254700000000",
  "shipping_address_line_1": "123 Main Street",
  "shipping_city": "Nairobi",
  "payment_method": "mpesa",
  "shipping_cost": "200.00",
  "tax_amount": "180.00",
  "coupon_code": "SAVE10",
  "notes": "Please deliver in the morning"
}
```

#### Get Order Details

**Endpoint:** `GET /api/orders/{id}/`  
**Authentication:** Required

#### Cancel Order

**Endpoint:** `POST /api/orders/{id}/cancel/`  
**Authentication:** Required

#### Get Order Statistics

**Endpoint:** `GET /api/orders/stats/`  
**Authentication:** Required

**Success Response:**

```json
{
  "total_orders": 15,
  "total_spent": "2500000.00",
  "orders_by_status": {
    "created": 2,
    "confirmed": 3,
    "processing": 1,
    "shipped": 5,
    "delivered": 4,
    "cancelled": 0,
    "refunded": 0
  }
}
```

### 21. Order Items (Read-Only)

#### List Order Items

**Endpoint:** `GET /api/order-items/`  
**Authentication:** Required

**Note:** Order items are read-only. They cannot be modified after order creation.

### 22. Coupons

#### List Coupons

**Endpoint:** `GET /api/coupons/`  
**Authentication:** Required (Admin)

#### Create Coupon (Admin Only)

**Endpoint:** `POST /api/coupons/`  
**Authentication:** Required (Admin)

**Request Payload:**

```json
{
  "code": "SAVE20",
  "description": "Save 20% on all purchases",
  "discount_type": "percentage",
  "discount_value": "20.00",
  "usage_limit": 100,
  "usage_limit_per_user": 1,
  "minimum_order_amount": "1000.00",
  "start_date": "2025-09-01T00:00:00Z",
  "end_date": "2025-12-31T23:59:59Z",
  "is_active": true
}
```

---

## Payment Management

### 23. Payments

#### List Payments

**Endpoint:** `GET /api/payments/`  
**Authentication:** Required

#### Create Payment

**Endpoint:** `POST /api/payments/`  
**Authentication:** Required

**Request Payload:**

```json
{
  "order": 1,
  "payment_method": "mpesa",
  "amount": "315380.00",
  "payment_reference": "MP240918ABC123"
}
```

#### Get Payment Details

**Endpoint:** `GET /api/payments/{id}/`  
**Authentication:** Required

#### Update Payment Status (Admin Only)

**Endpoint:** `PUT /api/payments/{id}/`  
**Authentication:** Required (Admin)

---

## Core Services

### 24. Audit Logs (Admin Only)

#### List Audit Logs

**Endpoint:** `GET /api/audit-logs/`  
**Authentication:** Required (Admin)

#### Get Audit Log Details

**Endpoint:** `GET /api/audit-logs/{id}/`  
**Authentication:** Required (Admin)

---

## Error Handling

### Standard Error Responses

#### 400 Bad Request

```json
{
  "success": false,
  "message": "Validation error",
  "errors": {
    "email": ["This field is required."],
    "password": ["This field may not be blank."]
  }
}
```

#### 401 Unauthorized

```json
{
  "success": false,
  "message": "Authentication required",
  "errors": {
    "detail": "Authentication credentials were not provided."
  }
}
```

#### 403 Forbidden

```json
{
  "success": false,
  "message": "Permission denied",
  "errors": {
    "detail": "You do not have permission to perform this action."
  }
}
```

#### 404 Not Found

```json
{
  "success": false,
  "message": "Resource not found",
  "errors": {
    "detail": "Not found."
  }
}
```

#### 500 Internal Server Error

```json
{
  "success": false,
  "message": "Internal server error",
  "errors": {
    "non_field_errors": [
      "An unexpected error occurred. Please try again later."
    ]
  }
}
```

---

## Response Formats

### Success Response Structure

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    // Response data here
  }
}
```

### Paginated Response Structure

```json
{
  "success": true,
  "count": 100,
  "next": "http://localhost:8000/api/products/?page=3",
  "previous": "http://localhost:8000/api/products/?page=1",
  "results": [
    // Array of objects
  ]
}
```

---

## Authentication Headers

For endpoints requiring authentication, include the JWT token in the Authorization header:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

---

## Content Types

**Request Content-Type:** `application/json`  
**Response Content-Type:** `application/json`

---

## Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `204 No Content` - Resource deleted successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Rate Limiting

API endpoints may be rate-limited. Check response headers for rate limit information:

- `X-RateLimit-Limit` - Rate limit per time window
- `X-RateLimit-Remaining` - Remaining requests in current window
- `X-RateLimit-Reset` - Time when rate limit resets

---

## Notes

1. **Timestamps** are in ISO 8601 format (UTC)
2. **Decimal fields** (prices, amounts) are returned as strings to maintain precision
3. **Pagination** is available on list endpoints with `page` and `page_size` parameters
4. **Filtering and Search** are available on most list endpoints
5. **Order items are read-only** - they cannot be modified after order creation
6. **Stock validation** occurs during cart operations and order creation
7. **Prices are locked** at order creation time for historical accuracy

---

## Example cURL Commands

### Register User

```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe",
    "phonenumber": "+254712345678"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### Get Products

```bash
curl -X GET http://localhost:8000/api/products/
```

### Add to Cart

```bash
curl -X POST http://localhost:8000/api/cart/add_item/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "product_id": 1,
    "quantity": 2
  }'
```

### Create Order from Cart

```bash
curl -X POST http://localhost:8000/api/orders/create_from_cart/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "shipping_first_name": "John",
    "shipping_last_name": "Doe",
    "shipping_email": "john@example.com",
    "shipping_phone": "+254700000000",
    "shipping_address_line_1": "123 Main Street",
    "shipping_city": "Nairobi",
    "payment_method": "mpesa"
  }'
```

---

This documentation covers all available endpoints in your Rodan Phones E-commerce API. For any questions or support, please contact the development team.
