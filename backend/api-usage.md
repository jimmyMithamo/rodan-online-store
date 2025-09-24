# Rodan Phones API - User Management Endpoints

## Base URL
```
http://localhost:8000/api/
```

## Authentication
Most endpoints require JWT authentication. Include the access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## 1. User Registration
**Endpoint:** `POST /api/users/`  
**Authentication:** Not required  
**Description:** Register a new user account

### Request Payload:
```json
{
    "email": "user@example.com",
    "phonenumber": "+254712345678",
    "first_name": "John",
    "last_name": "Doe",
    "password": "SecurePass123",
    "password_confirm": "SecurePass123"
}
```

### Success Response (201 Created):
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

### Error Response (400 Bad Request):
```json
{
    "success": false,
    "message": "Registration failed",
    "errors": {
        "email": ["A user with this email already exists"],
        "password": ["Password must contain at least one number"]
    }
}
```

---

## 2. User Login
**Endpoint:** `POST /api/auth/login/`  
**Authentication:** Not required  
**Description:** Login with email and password

### Request Payload:
```json
{
    "email": "user@example.com",
    "password": "SecurePass123"
}
```

### Success Response (200 OK):
```json
{
    "success": true,
    "message": "Login successful",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
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

### Error Response (400 Bad Request):
```json
{
    "success": false,
    "message": "Invalid credentials",
    "errors": {
        "non_field_errors": ["Invalid email or password"]
    }
}
```

---

## 3. Token Refresh
**Endpoint:** `POST /api/token/refresh/`  
**Authentication:** Not required  
**Description:** Refresh access token using refresh token

### Request Payload:
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Success Response (200 OK):
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

## 4. Get Current User Profile
**Endpoint:** `GET /api/users/me/`  
**Authentication:** Required  
**Description:** Get the authenticated user's profile

### Success Response (200 OK):
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

---

## 5. Update User Profile
**Endpoint:** `PUT /api/users/update_profile/`  
**Authentication:** Required  
**Description:** Update the authenticated user's profile

### Request Payload (partial update allowed):
```json
{
    "first_name": "Jane",
    "last_name": "Smith",
    "phonenumber": "+254787654321"
}
```

### Success Response (200 OK):
```json
{
    "success": true,
    "message": "Profile updated successfully",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "phonenumber": "+254787654321",
        "first_name": "Jane",
        "last_name": "Smith",
        "date_joined": "2025-09-18T10:30:00Z"
    }
}
```

---

## 6. List Users (Admin Only)
**Endpoint:** `GET /api/users/`  
**Authentication:** Required (Admin)  
**Description:** List all users (admin only)

### Success Response (200 OK):
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "email": "user@example.com",
            "phonenumber": "+254712345678",
            "first_name": "John",
            "last_name": "Doe",
            "date_joined": "2025-09-18T10:30:00Z"
        },
        {
            "id": 2,
            "email": "admin@example.com",
            "phonenumber": "+254700000000",
            "first_name": "Admin",
            "last_name": "User",
            "date_joined": "2025-09-18T09:00:00Z"
        }
    ]
}
```

---

## 7. List Shipping Addresses
**Endpoint:** `GET /api/shipping-addresses/`  
**Authentication:** Required  
**Description:** Get all shipping addresses for the authenticated user

### Success Response (200 OK):
```json
{
    "success": true,
    "addresses": [
        {
            "id": 1,
            "address": "123 Main Street, Nairobi, Kenya",
            "default_address": true,
            "created_at": "2025-09-18T10:30:00Z",
            "updated_at": "2025-09-18T10:30:00Z"
        }
    ],
    "count": 1
}
```

---

## 8. Create Shipping Address
**Endpoint:** `POST /api/shipping-addresses/`  
**Authentication:** Required  
**Description:** Create a new shipping address

### Request Payload:
```json
{
    "address": "456 Oak Avenue, Mombasa, Kenya",
    "default_address": false
}
```

### Success Response (201 Created):
```json
{
    "success": true,
    "message": "Shipping address created successfully",
    "address": {
        "id": 2,
        "address": "456 Oak Avenue, Mombasa, Kenya",
        "default_address": false,
        "created_at": "2025-09-18T11:00:00Z",
        "updated_at": "2025-09-18T11:00:00Z"
    }
}
```

---

## 9. Get Specific Shipping Address
**Endpoint:** `GET /api/shipping-addresses/{id}/`  
**Authentication:** Required  
**Description:** Get a specific shipping address

### Success Response (200 OK):
```json
{
    "id": 1,
    "address": "123 Main Street, Nairobi, Kenya",
    "default_address": true,
    "created_at": "2025-09-18T10:30:00Z",
    "updated_at": "2025-09-18T10:30:00Z"
}
```

---

## 10. Update Shipping Address
**Endpoint:** `PUT /api/shipping-addresses/{id}/`  
**Authentication:** Required  
**Description:** Update a shipping address

### Request Payload:
```json
{
    "address": "123 Updated Street, Nairobi, Kenya",
    "default_address": true
}
```

### Success Response (200 OK):
```json
{
    "success": true,
    "message": "Shipping address updated successfully",
    "address": {
        "id": 1,
        "address": "123 Updated Street, Nairobi, Kenya",
        "default_address": true,
        "created_at": "2025-09-18T10:30:00Z",
        "updated_at": "2025-09-18T12:00:00Z"
    }
}
```

---

## 11. Delete Shipping Address
**Endpoint:** `DELETE /api/shipping-addresses/{id}/`  
**Authentication:** Required  
**Description:** Delete a shipping address

### Success Response (200 OK):
```json
{
    "success": true,
    "message": "Shipping address deleted successfully"
}
```

---

## Common Error Responses

### 401 Unauthorized:
```json
{
    "success": false,
    "message": "Authentication required",
    "errors": {
        "detail": "Authentication credentials were not provided."
    }
}
```

### 403 Forbidden:
```json
{
    "success": false,
    "message": "Permission denied",
    "errors": {
        "detail": "You do not have permission to perform this action."
    }
}
```

### 404 Not Found:
```json
{
    "success": false,
    "message": "Resource not found",
    "errors": {
        "detail": "Not found."
    }
}
```

### 500 Internal Server Error:
```json
{
    "success": false,
    "message": "Internal server error",
    "errors": {
        "non_field_errors": ["An unexpected error occurred. Please try again later."]
    }
}
```

---

## Validation Rules

### Email:
- Must be a valid email format
- Must be unique across all users
- Required field

### Phone Number:
- Must be a valid phone number format
- Can include country code
- Required field

### Password (Registration):
- Minimum 8 characters
- Must contain at least one number
- Must contain at least one letter
- Required field

### Names:
- Minimum 2 characters
- Required fields
- Automatically title-cased

### Address:
- Minimum 10 characters
- Required field

---

## Example Usage with cURL

### Register a new user:
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "phonenumber": "+254712345678",
    "first_name": "Test",
    "last_name": "User",
    "password": "TestPass123",
    "password_confirm": "TestPass123"
  }'
```

### Login:
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123"
  }'
```

### Get profile (with token):
```bash
curl -X GET http://localhost:8000/api/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create shipping address:
```bash
curl -X POST http://localhost:8000/api/shipping-addresses/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "address": "123 Test Street, Nairobi, Kenya",
    "default_address": true
  }'
```