# Updated API Documentation

## 🚀 **Enhanced Admin Management System**

### **1. Create Admin Endpoint**

**Endpoint:** `POST /api/auth/create-admin/`
**Authentication:** SuperAdmin only (Bearer token required)

### **Request Format:**
```json
{
  "name": "Jane Smith",
  "email": "jane.smith@example.com",
  "address": "456 Oak Street, Downtown",
  "contact_person": "Emergency Contact Person",
  "contact_number": "9876543210",
  "phone_number": "1234567890",
  "plan": "Premium Plan"
}
```

### **Response Format:**
```json
{
  "email": "jane.smith@example.com",
  "password": "S1t8Juti"
}
```

### **2. List Admins Endpoint**

**Endpoint:** `GET /api/auth/list-admins/`
**Authentication:** SuperAdmin only (Bearer token required)

### **Response Format:**
```json
[
  {
    "id": 7,
    "username": "jane.smith",
    "email": "jane.smith@example.com",
    "name": "Jane Smith",
    "address": "456 Oak Street, Downtown",
    "contact_person": "Emergency Contact Person",
    "contact_number": "9876543210",
    "phone_number": "1234567890",
    "plan": "Premium Plan",
    "generated_password": "S1t8Juti",
    "date_joined": "2025-08-21T09:39:47.743211Z"
  }
]
```

### **Features:**
- ✅ **Random Password Generation:** 8-character alphanumeric password
- ✅ **Email as Login:** Uses email from form as login credential
- ✅ **Auto Username:** Generates unique username from email
- ✅ **Profile Storage:** Saves all form fields in database
- ✅ **SuperAdmin Only:** Protected by role-based permissions
- ✅ **CORS Enabled:** Works with React frontend

## 🧪 **Testing Examples**

### **1. Get SuperAdmin Token:**
```bash
curl -X POST http://192.168.1.91:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "superadmin", "password": "admin123456"}'
```

### **2. Create Admin User:**
```bash
curl -X POST http://192.168.1.90:8000/api/auth/create-admin/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SUPERADMIN_TOKEN" \
  -d '{
    "name": "Jane Smith",
    "email": "jane.smith@example.com",
    "address": "456 Oak Street, Downtown",
    "contact_person": "Emergency Contact Person",
    "contact_number": "9876543210",
    "phone_number": "1234567890",
    "plan": "Premium Plan"
  }'
```

**Response:**
```json
{
  "email": "jane.smith@example.com",
  "password": "S1t8Juti"
}
```

### **3. List All Created Admins:**
```bash
curl -X GET http://192.168.1.90:8000/api/auth/list-admins/ \
  -H "Authorization: Bearer YOUR_SUPERADMIN_TOKEN"
```

**Response:**
```json
[
  {
    "id": 7,
    "username": "jane.smith",
    "email": "jane.smith@example.com",
    "name": "Jane Smith",
    "address": "456 Oak Street, Downtown",
    "contact_person": "Emergency Contact Person",
    "contact_number": "9876543210",
    "phone_number": "1234567890",
    "plan": "Premium Plan",
    "generated_password": "S1t8Juti",
    "date_joined": "2025-08-21T09:39:47.743211Z"
  }
]
```

### **4. Test New Admin Login:**
```bash
curl -X POST http://192.168.1.90:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "jane.smith@example.com", "password": "S1t8Juti"}'
```

**Response:**
```json
{
  "access": "jwt_token_here",
  "refresh": "refresh_token_here",
  "user": {
    "id": 7,
    "username": "jane.smith",
    "email": "jane.smith@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "role": "ADMIN",
    "name": "Jane Smith",
    "address": "456 Oak Street, Downtown",
    "contact_person": "Emergency Contact Person",
    "contact_number": "9876543210",
    "phone_number": "1234567890",
    "plan": "Premium Plan",
    "generated_password": "S1t8Juti",
    "date_joined": "2025-08-21T09:39:47.743211Z"
  }
}
```

## 📱 **React Integration**

### **Create Admin Form Submission:**
```javascript
const createAdmin = async (formData) => {
  try {
    const response = await fetch('http://192.168.1.90:8000/api/auth/create-admin/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${superAdminToken}`,
      },
      credentials: 'include',
      body: JSON.stringify({
        name: formData.name,
        email: formData.email,
        address: formData.address,
        contact_person: formData.contact_person,
        contact_number: formData.contact_number,
        phone_number: formData.phone_number,
        plan: formData.plan
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();

    // Display credentials to SuperAdmin
    alert(`Admin created successfully!\nEmail: ${result.email}\nPassword: ${result.password}`);

    return result;
  } catch (error) {
    console.error('Error creating admin:', error);
    throw error;
  }
};
```

### **List Admins for Dashboard:**
```javascript
const listAdmins = async () => {
  try {
    const response = await fetch('http://192.168.1.90:8000/api/auth/list-admins/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${superAdminToken}`,
      },
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const admins = await response.json();

    // Display in dashboard table
    return admins;
  } catch (error) {
    console.error('Error fetching admins:', error);
    throw error;
  }
};
```

## 🔐 **Login Flow**

1. **SuperAdmin creates Admin** via form → Gets email + generated password
2. **New Admin logs in** using email and password → Gets redirected to Admin dashboard
3. **Role-based redirect** works automatically based on user.role

## 🗄️ **Database Schema**

### **User Model Fields:**
- `username` (auto-generated from email)
- `email` (from form, used for login)
- `first_name` (extracted from name field)
- `last_name` (extracted from name field)
- `name` (full name from form)
- `address` (from form)
- `contact_person` (from form)
- `contact_number` (from form)
- `phone_number` (from form)
- `plan` (from form)
- `role` (automatically set to ADMIN)
- `password` (randomly generated)
- `generated_password` (stored for dashboard viewing)

## ✅ **Validation & Security**

- **Email uniqueness** check
- **Username uniqueness** with auto-increment
- **SuperAdmin authorization** required
- **Random secure password** generation
- **CORS protection** configured
- **JWT token validation**

**Your enhanced API is ready for production use with React frontend!** 🎯
