# Rodan Phones API - Quick Reference

## 🚀 Quick Start

### Base URL

```
http://localhost:8000/api/
```

### Authentication

Include JWT token in header for protected endpoints:

```
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## 🔐 Authentication Flow

```javascript
// 1. Register
POST /
  api /
  users /
  {
    email: "user@example.com",
    password: "password123",
    first_name: "John",
    last_name: "Doe",
    phonenumber: "+254712345678",
  };

// 2. Login
POST /
  api /
  auth /
  login /
  {
    email: "user@example.com",
    password: "password123",
  };

// 3. Refresh Token
POST /
  api /
  token /
  refresh /
  {
    refresh: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  };
```

---

## 📱 Product Endpoints

### Basic Product Operations

```javascript
GET /api/products/                    // List all products
GET /api/products/{id}/               // Get product details
GET /api/products/{id}/variations/    // Get product variations
```

### Product Collections

```javascript
GET /api/products/product_collections/   // All collections in one response
GET /api/products/best_sellers/       // Best selling products
GET /api/products/new_arrivals/       // Newest products
GET /api/products/featured/           // Featured products
GET /api/products/pocket_friendly/    // Cheapest products
GET /api/products/high_end/           // Most expensive products
GET /api/products/latest_accessories/ // Latest accessories
```

### Product Search & Filtering

```javascript
// Advanced search
GET /api/products/search/?q=iphone&min_price=50000&max_price=200000&brand=Apple&in_stock=true

// By brand
GET /api/products/by_brand/?brand=Samsung

// By category
GET /api/products/by_category/?category_name=smartphones

// By price range
GET /api/products/price_range/?min_price=10000&max_price=50000
```

---

## 🛒 Cart Flow

```javascript
// 1. Add item to cart
POST /api/cart/add_item/
{
  "product_id": 1,
  "product_variation_id": 2,
  "quantity": 1
}

// 2. View cart
GET /api/cart/

// 3. Update item quantity
POST /api/cart/update_item/
{
  "product_id": 1,
  "quantity": 3
}

// 4. Remove item
POST /api/cart/remove_item/
{
  "product_id": 1
}

// 5. Clear cart
POST /api/cart/clear/
```

---

## 📦 Order Flow

```javascript
// Recommended: Create order from cart
POST /api/orders/create_from_cart/
{
  "shipping_first_name": "John",
  "shipping_last_name": "Doe",
  "shipping_email": "john@example.com",
  "shipping_phone": "+254700000000",
  "shipping_address_line_1": "123 Main Street",
  "shipping_city": "Nairobi",
  "payment_method": "mpesa"
}

// Alternative: Create order directly
POST /api/orders/
{
  "payment_method": "mpesa",
  "shipping_first_name": "John",
  "shipping_last_name": "Doe",
  "shipping_email": "john@example.com",
  "shipping_phone": "+254700000000",
  "shipping_address_line_1": "123 Main Street",
  "shipping_city": "Nairobi",
  "items": [
    {
      "product": 1,
      "quantity": 2,
      "unit_price": "145000.00"
    }
  ]
}

// View orders
GET /api/orders/

// Get order details
GET /api/orders/{id}/

// Cancel order
POST /api/orders/{id}/cancel/

// Order statistics
GET /api/orders/stats/
```

---

## 💳 Payment Flow

```javascript
// Create payment
POST /api/payments/
{
  "order": 1,
  "payment_method": "mpesa",
  "amount": "315380.00",
  "payment_reference": "MP240918ABC123"
}

// View payments
GET /api/payments/

// Get payment details
GET /api/payments/{id}/
```

---

## 👤 User Management

```javascript
// Get current user profile
GET /api/users/me/

// Update profile
PUT /api/users/{id}/
{
  "first_name": "John Updated",
  "last_name": "Doe Updated"
}

// Shipping addresses
GET /api/shipping-addresses/           // List addresses
POST /api/shipping-addresses/          // Create address
PUT /api/shipping-addresses/{id}/      // Update address
DELETE /api/shipping-addresses/{id}/   // Delete address
```

---

## 📊 Categories & Brands

```javascript
GET /api/categories/                   // List categories
GET /api/brands/                       // List brands
GET /api/tags/                         // List tags
```

---

## ⭐ Reviews

```javascript
// List reviews
GET /
  api /
  reviews /
  // Create review
  POST /
  api /
  reviews /
  {
    product: 1,
    rating: 5,
    review_text: "Excellent product!",
    title: "Amazing Phone",
  };
```

---

## 🎟️ Coupons (Admin)

```javascript
GET /
  api /
  coupons / // List coupons
  POST /
  api /
  coupons / // Create coupon
  {
    code: "SAVE20",
    description: "Save 20%",
    discount_type: "percentage",
    discount_value: "20.00",
    start_date: "2025-09-01T00:00:00Z",
    end_date: "2025-12-31T23:59:59Z",
  };
```

---

## 📋 Common Query Parameters

### Pagination

```
?page=2&page_size=20
```

### Search

```
?search=iphone
```

### Ordering

```
?ordering=-created_at        // Newest first
?ordering=price             // Cheapest first
?ordering=-price            // Most expensive first
```

### Filtering

```
?category=1
?brand=2
?in_stock=true
?min_price=1000&max_price=5000
```

---

## 🔄 E-commerce Workflow

### Customer Journey

```
1. Browse Products → GET /api/products/
2. Search/Filter → GET /api/products/search/
3. View Details → GET /api/products/{id}/
4. Add to Cart → POST /api/cart/add_item/
5. View Cart → GET /api/cart/
6. Checkout → POST /api/orders/create_from_cart/
7. Make Payment → POST /api/payments/
8. Track Order → GET /api/orders/{id}/
```

### Admin Workflow

```
1. Manage Products → POST/PUT/DELETE /api/products/
2. Manage Categories → POST/PUT/DELETE /api/categories/
3. Manage Coupons → POST/PUT/DELETE /api/coupons/
4. View Orders → GET /api/orders/
5. Process Payments → PUT /api/payments/{id}/
6. View Analytics → GET /api/orders/stats/
```

---

## ❌ Error Codes

| Code | Meaning      |
| ---- | ------------ |
| 200  | Success      |
| 201  | Created      |
| 400  | Bad Request  |
| 401  | Unauthorized |
| 403  | Forbidden    |
| 404  | Not Found    |
| 500  | Server Error |

---

## 💡 Pro Tips

1. **Always authenticate** for cart/order operations
2. **Use cart flow** for better UX (add to cart → checkout)
3. **Handle pagination** for product listings
4. **Validate stock** before adding to cart
5. **Cache product data** for better performance
6. **Use search endpoints** for product discovery
7. **Check order status** for real-time updates
8. **Implement error handling** for all API calls

---

## 📞 Support

For technical support or questions about this API, please contact the development team.

**Last Updated:** September 19, 2025
