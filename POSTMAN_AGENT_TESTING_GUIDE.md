# 🧪 Postman Testing Guide - Agent Creation API

## 🎯 Testing the Company ID Implementation

### Prerequisites
1. ✅ Django server running: `python manage.py runserver`
2. ✅ Admin user with `company_id` exists
3. ✅ Postman installed

---

## 📋 Step-by-Step Testing

### Step 1: Login as Admin to Get JWT Token

**Request:**
```
Method: POST
URL: http://127.0.0.1:8000/api/auth/login/
```

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
    "username": "admin_unique_test_142116@tesla.com",
    "password": "qiL16dou"
}
```

**Expected Response (200 OK):**
```json
{
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
        "id": 34,
        "username": "admin_unique_test_142116@tesla.com",
        "email": "admin_unique_test_142116@tesla.com",
        "company_id": "TES010",
        "role": "ADMIN"
    }
}
```

**🔑 Copy the `access` token for next steps!**

---

### Step 2: Create Agent (Main Test)

**Request:**
```
Method: POST
URL: http://127.0.0.1:8000/api/admin-dashboard/create-agent/
```

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```
*Replace the token with your actual access token from Step 1*

**Body (raw JSON) - What React Frontend Sends:**
```json
{
    "name": "John Doe Agent",
    "phone": "1234567890",
    "email": "john.agent@company.com",
    "specialization": "Customer Support"
}
```

**Expected Response (201 Created):**
```json
{
    "email": "john.agent@company.com",
    "password": "Abc123Xy",
    "agent": {
        "id": 10,
        "sn": 0,
        "name": "John Doe Agent",
        "email": "john.agent@company.com",
        "phone": "1234567890",
        "specialization": "Customer Support",
        "company_id": "TES010",
        "status": "OFFLINE",
        "formatted_last_active": "Never",
        "generated_password": "Abc123Xy",
        "is_first_login": true,
        "is_active": true,
        "created_at": "2025-08-22T10:30:00Z"
    }
}
```

**✅ Key Points to Verify:**
- `company_id` matches admin's company_id ("TES010")
- Agent gets auto-generated password
- Status is "OFFLINE" by default
- `is_first_login` is true

---

### Step 3: List Agents (Verify Creation)

**Request:**
```
Method: GET
URL: http://127.0.0.1:8000/api/admin-dashboard/list-agents/
```

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Body:** None (GET request)

**Expected Response (200 OK):**
```json
[
    {
        "id": 10,
        "sn": 1,
        "name": "John Doe Agent",
        "email": "john.agent@company.com",
        "phone": "1234567890",
        "specialization": "Customer Support",
        "company_id": "TES010",
        "status": "OFFLINE",
        "formatted_last_active": "Never",
        "is_first_login": true,
        "is_active": true
    }
]
```

---

## 🧪 Additional Test Scenarios

### Test 4: Error Case - Admin Without Company ID

**If you test with SuperAdmin (no company_id):**

**Request:**
```
Method: POST
URL: http://127.0.0.1:8000/api/admin-dashboard/create-agent/
Headers: Authorization: Bearer <superadmin_token>
Body: Same agent data as above
```

**Expected Response (400 Bad Request):**
```json
{
    "error": "Admin user must have a company_id to create agents. Please contact SuperAdmin."
}
```

### Test 5: Error Case - Duplicate Email

**Request:**
```
Method: POST
URL: http://127.0.0.1:8000/api/admin-dashboard/create-agent/
Headers: Authorization: Bearer <admin_token>
```

**Body (same email as before):**
```json
{
    "name": "Another Agent",
    "phone": "9876543210",
    "email": "john.agent@company.com",
    "specialization": "Technical Support"
}
```

**Expected Response (400 Bad Request):**
```json
{
    "email": [
        "This email is already in use by another agent."
    ]
}
```

### Test 6: Error Case - Missing Required Fields

**Request:**
```
Method: POST
URL: http://127.0.0.1:8000/api/admin-dashboard/create-agent/
Headers: Authorization: Bearer <admin_token>
```

**Body (missing required field):**
```json
{
    "name": "Incomplete Agent",
    "phone": "1234567890"
}
```

**Expected Response (400 Bad Request):**
```json
{
    "email": [
        "This field is required."
    ],
    "specialization": [
        "This field is required."
    ]
}
```

---

## 📝 Postman Collection Setup

### Collection Variables
Create these variables in your Postman collection:

```
base_url: http://127.0.0.1:8000
admin_token: {{login_token}}
```

### Test Scripts
Add this to your login request's "Tests" tab:

```javascript
// Save token for other requests
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.collectionVariables.set("login_token", response.access);
    pm.test("Login successful", function () {
        pm.expect(response.user).to.have.property("company_id");
    });
}
```

Add this to your create agent request's "Tests" tab:

```javascript
// Verify agent creation
if (pm.response.code === 201) {
    const response = pm.response.json();
    pm.test("Agent created with company_id", function () {
        pm.expect(response.agent).to.have.property("company_id");
        pm.expect(response).to.have.property("password");
    });
}
```

---

## 🎯 Quick Test Checklist

✅ **Step 1**: Login as admin → Get JWT token  
✅ **Step 2**: Create agent → Verify company_id is set automatically  
✅ **Step 3**: List agents → Verify agent appears in admin's list  
✅ **Step 4**: Test error cases → Verify proper validation  

## 🚀 Ready to Test!

Use the exact URLs, headers, and body content above in Postman. The API will automatically extract the `company_id` from your JWT token and create agents with proper company isolation!
