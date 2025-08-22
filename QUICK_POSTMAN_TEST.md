# 🚀 Quick Postman Test - Agent Creation API

## 📋 Quick Setup (5 minutes)

### Step 1: Login as Admin
```
Method: POST
URL: http://127.0.0.1:8000/api/auth/login/
Headers: Content-Type: application/json
Body:
{
    "username": "admin_unique_test_142116@tesla.com",
    "password": "qiL16dou"
}
```
**Copy the `access` token from response!**

### Step 2: Create Agent
```
Method: POST
URL: http://127.0.0.1:8000/api/admin-dashboard/create-agent/
Headers: 
    Authorization: Bearer YOUR_TOKEN_HERE
    Content-Type: application/json
Body:
{
    "name": "Test Agent",
    "phone": "1234567890",
    "email": "test.agent@example.com",
    "specialization": "Customer Support"
}
```

### Step 3: Verify Agent Created
```
Method: GET
URL: http://127.0.0.1:8000/api/admin-dashboard/list-agents/
Headers: Authorization: Bearer YOUR_TOKEN_HERE
```

## ✅ What to Verify

1. **Login Response** should contain:
   ```json
   {
       "access": "jwt_token_here",
       "user": {
           "company_id": "TES010",
           "role": "ADMIN"
       }
   }
   ```

2. **Create Agent Response** should contain:
   ```json
   {
       "email": "test.agent@example.com",
       "password": "auto_generated_password",
       "agent": {
           "company_id": "TES010",    ← Automatically set!
           "status": "OFFLINE",
           "is_first_login": true
       }
   }
   ```

3. **List Agents** should show your created agent with same `company_id`

## 🎯 Key Test Points

✅ **Frontend Simplicity**: Only 4 fields needed  
✅ **Security**: `company_id` comes from JWT, not frontend  
✅ **Isolation**: Admin only sees their company's agents  
✅ **Validation**: Proper errors for missing/duplicate data  

## 📁 Import Collection

Use this file: `Agent_Creation_API_Test.postman_collection.json`

This includes all test cases with automatic validation!
