# Admin Pagination API Documentation

## New Endpoint: Paginated Admin List

### 📋 **GET /api/auth/list-admins-paginated/**

A comprehensive pagination API for the super-admin dashboard to efficiently handle large numbers of admin users.

#### **Features:**
- ✅ **Pagination**: Handle large datasets with configurable page sizes
- ✅ **Search**: Search across name, email, and company_id fields
- ✅ **Ordering**: Sort by multiple fields (ascending/descending)
- ✅ **Filtering**: Combine search and ordering parameters
- ✅ **Performance**: Optimized queries for large datasets

---

### **Query Parameters:**

| Parameter | Type | Default | Description | Example |
|-----------|------|---------|-------------|---------|
| `page` | integer | 1 | Page number to retrieve | `?page=2` |
| `page_size` | integer | 10 | Items per page (max: 100) | `?page_size=25` |
| `search` | string | - | Search in name, email, company_id | `?search=tesla` |
| `ordering` | string | `-date_joined` | Field to order by | `?ordering=name` |

#### **Valid Ordering Fields:**
- `name` - Sort by admin name (A-Z)
- `-name` - Sort by admin name (Z-A)
- `email` - Sort by email (A-Z)
- `-email` - Sort by email (Z-A)
- `company_id` - Sort by company ID (A-Z)
- `-company_id` - Sort by company ID (Z-A)
- `date_joined` - Sort by join date (oldest first)
- `-date_joined` - Sort by join date (newest first) **[DEFAULT]**

---

### **Example Requests:**

#### **Basic Pagination:**
```
GET /api/auth/list-admins-paginated/
```

#### **Custom Page Size:**
```
GET /api/auth/list-admins-paginated/?page_size=5
```

#### **Navigate to Page 2:**
```
GET /api/auth/list-admins-paginated/?page=2
```

#### **Search for Tesla:**
```
GET /api/auth/list-admins-paginated/?search=tesla
```

#### **Order by Name (A-Z):**
```
GET /api/auth/list-admins-paginated/?ordering=name
```

#### **Combined Parameters:**
```
GET /api/auth/list-admins-paginated/?page=1&page_size=5&search=test&ordering=name
```

---

### **Response Format:**

```json
{
    "count": 25,
    "next": "http://127.0.0.1:8000/api/auth/list-admins-paginated/?page=3",
    "previous": "http://127.0.0.1:8000/api/auth/list-admins-paginated/?page=1",
    "total_pages": 3,
    "current_page": 2,
    "page_size": 10,
    "results": [
        {
            "id": 2,
            "email": "admin@tesla.com",
            "name": "Tesla Motors Inc",
            "address": "123 Tesla Street",
            "contact_person": "Elon Musk",
            "contact_number": "555-TESLA",
            "phone_number": "555-0123",
            "company_id": "TES001",
            "current_plan": {
                "assignment_id": 1,
                "plan_id": 1,
                "plan_name": "Pro",
                "max_agents": 15,
                "price": "199.99",
                "start_date": "2025-08-22T10:00:00Z",
                "expiry_date": "2026-08-22T10:00:00Z",
                "status": "active",
                "days_remaining": 365
            },
            "generated_password": "Abc123Xy",
            "date_joined": "2025-08-22T10:00:00Z",
            "is_active": true
        }
    ]
}
```

---

### **Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Total number of admin users matching the search |
| `next` | string/null | URL for the next page (null if last page) |
| `previous` | string/null | URL for the previous page (null if first page) |
| `total_pages` | integer | Total number of pages |
| `current_page` | integer | Current page number |
| `page_size` | integer | Actual number of items on this page |
| `results` | array | Array of admin user objects |

---

### **Error Responses:**

#### **404 - Page Not Found:**
```json
{
    "detail": "Invalid page."
}
```

#### **401 - Unauthorized:**
```json
{
    "detail": "Authentication credentials were not provided."
}
```

#### **403 - Permission Denied:**
```json
{
    "detail": "You do not have permission to perform this action."
}
```

---

### **Authentication:**

**Required:** SuperAdmin JWT token

```
Authorization: Bearer YOUR_JWT_TOKEN
```

---

### **Use Cases:**

1. **Super-Admin Dashboard**: Display paginated list of all admin users
2. **Search Functionality**: Find specific admins by name, email, or company ID
3. **Sorting**: Order admins by different criteria
4. **Performance**: Handle large numbers of admin users efficiently
5. **Mobile/Web Apps**: Responsive pagination for different screen sizes

---

### **Postman Testing:**

```javascript
// Test Script (Add to Postman Tests tab)
pm.test("Pagination response structure", function () {
    const response = pm.response.json();
    pm.expect(response).to.have.property('count');
    pm.expect(response).to.have.property('results');
    pm.expect(response).to.have.property('total_pages');
    pm.expect(response).to.have.property('current_page');
    pm.expect(response.results).to.be.an('array');
});

pm.test("Admin objects have required fields", function () {
    const response = pm.response.json();
    if (response.results.length > 0) {
        const admin = response.results[0];
        pm.expect(admin).to.have.property('id');
        pm.expect(admin).to.have.property('name');
        pm.expect(admin).to.have.property('email');
        pm.expect(admin).to.have.property('company_id');
    }
});
```

---

### **Performance Notes:**

- **Database Indexing**: Ensure indexes on `name`, `email`, `company_id`, and `date_joined` fields
- **Query Optimization**: Uses Django ORM select_related for efficient joins
- **Memory Usage**: Limited page sizes prevent memory issues
- **Caching**: Consider adding Redis caching for frequently accessed pages

---

## Migration from Non-Paginated API

### **Old API (still available):**
```
GET /api/auth/list-admins/
GET /api/auth/list-admins/?admin_id=2
```

### **New Paginated API:**
```
GET /api/auth/list-admins-paginated/
```

**Recommendation**: Use paginated API for dashboard lists, keep the old API for specific admin lookups.
