# Postman Login Debug Guide

## ✅ API is Working! 
The login API is confirmed working with:
- Form data
- JSON with Content-Type header
- JSON using requests.json parameter

## 🔍 Postman Troubleshooting Steps

### Step 1: Verify Your Request URL
Make sure you're using: `http://127.0.0.1:8000/api/auth/login/`
- Note the trailing slash `/`
- Make sure it's a POST request

### Step 2: Try Form-Data Format (EASIEST)
1. Open Postman
2. Set method to `POST`
3. URL: `http://127.0.0.1:8000/api/auth/login/`
4. Go to `Body` tab
5. Select `form-data` radio button
6. Add these key-value pairs:
   ```
   username: superadmin
   password: superadmin123
   ```

### Step 3: Try JSON Format (If you prefer JSON)
1. Open Postman
2. Set method to `POST`
3. URL: `http://127.0.0.1:8000/api/auth/login/`
4. Go to `Headers` tab and add:
   ```
   Content-Type: application/json
   ```
5. Go to `Body` tab
6. Select `raw` radio button
7. Select `JSON` from dropdown
8. Enter this exact JSON:
   ```json
   {
       "username": "superadmin",
       "password": "superadmin123"
   }
   ```

### Step 4: Common Issues & Solutions

#### Issue: Still getting "Invalid credentials"
**Solutions:**
1. Check if Django server is running: `python manage.py runserver`
2. Verify URL has trailing slash: `/api/auth/login/`
3. Make sure you're using POST, not GET
4. Clear Postman cache and try again

#### Issue: Server connection error
**Solutions:**
1. Make sure Django server is running on port 8000
2. Check if another app is using port 8000
3. Try: `python manage.py runserver 0.0.0.0:8000`

#### Issue: JSON format not working
**Solutions:**
1. Double-check Content-Type header is `application/json`
2. Make sure JSON uses double quotes, not single quotes
3. Validate JSON syntax online if needed

### Step 5: Expected Success Response
You should get a 200 status with response like:
```json
{
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
        "id": 1,
        "username": "superadmin",
        "email": "superadmin@example.com",
        "role": "SUPERADMIN",
        ...
    }
}
```

### Step 6: If Still Not Working
1. Export your Postman request and share the raw HTTP request
2. Check Django server logs for any error messages
3. Try the exact same request using curl:
   ```bash
   curl -X POST http://127.0.0.1:8000/api/auth/login/ \
        -H "Content-Type: application/json" \
        -d '{"username": "superadmin", "password": "superadmin123"}'
   ```
