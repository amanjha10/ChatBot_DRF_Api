# Django REST Framework Authentication System

A production-ready DRF authentication system with role-based access control using SimpleJWT.

## ✨ Recent Updates (August 2025)

### 🎯 Admin Management Enhancements
- ✅ **Name Field Integration**: Added `name` field to admin creation (replaces first_name/last_name)
- ✅ **Company ID from Name**: Generate company IDs from name field (e.g., "Tesla Motors" → "TES001")
- ✅ **Query Parameter Support**: Get specific admin by ID (`/list-admins/?admin_id=2`)
- ✅ **Delete Admin API**: Full cascade deletion with plan assignments cleanup
- ✅ **Clean API Responses**: Removed unnecessary fields (first_name, last_name, username)

### 🧪 Comprehensive Testing
- ✅ **Postman Collection**: Updated with all new endpoints and error cases
- ✅ **Test Scripts**: Multiple test files for different scenarios
- ✅ **Error Handling**: Proper 404/400 responses with meaningful messages

## Features

- **Custom User Model** with role-based access (SUPERADMIN, ADMIN, AGENT)
- **JWT Authentication** using SimpleJWT
- **Role-based Permissions** with custom permission classes
- **Plan Management System** with automatic assignments
- **Admin Management** with company ID generation
- **Agent Assignment System** for chat management

## User Roles

- **SUPERADMIN**: Can create Admin users
- **ADMIN**: Can assign Agents to chats and create chats
- **AGENT**: Can view their assigned chats

## API Endpoints

### Authentication
- `POST /api/auth/login/` - Login with email/username + password
- `POST /api/auth/token/refresh/` - Refresh JWT token
- `GET /api/auth/profile/` - Get current user profile

### SuperAdmin Only - Admin Management
- `POST /api/auth/create-admin/` - Create Admin users (with name field & company ID)
- `GET /api/auth/list-admins/` - List all admins (clean response)
- `GET /api/auth/list-admins/?admin_id=X` - Get specific admin by ID
- `PUT/PATCH /api/auth/update-admin/<id>/` - Update admin information
- `DELETE /api/auth/delete-admin/<id>/` - Delete admin (cascade deletion)
- `POST /api/auth/change-admin-plan/<id>/` - Change admin's plan

### SuperAdmin Only - Plan Management
- `POST /api/auth/create-plan/` - Create new plans
- `GET /api/auth/list-plans/` - List all available plans
- `GET /api/auth/list-user-plan-assignments/` - View plan assignments

### Admin Dashboard (Admin Role)
- `POST /api/admin-dashboard/create-agent/` - Create new agents
- `GET /api/admin-dashboard/list-agents/` - List company agents
- `POST /api/admin-dashboard/agent-first-login/` - Agent password setup

## Setup Instructions

1. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

4. **Create SuperUser**
   ```bash
   python manage.py createsuperuser --username superadmin --email superadmin@example.com
   # Set password: admin123456
   ```

5. **Set SuperAdmin Role**
   ```bash
   python manage.py setup_superadmin superadmin
   ```

6. **Start Development Server**
   ```bash
   python manage.py runserver
   ```

## Testing the API

### 1. Login (Get JWT Token)
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "superadmin", "password": "admin123456"}'
```

Response includes:
- `access`: JWT access token
- `refresh`: JWT refresh token  
- `user`: User details with role

### 2. Create Admin (SuperAdmin only)
```bash
curl -X POST http://127.0.0.1:8000/api/auth/create-admin/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "username": "admin1",
    "email": "admin1@example.com", 
    "first_name": "Admin",
    "last_name": "User",
    "password": "admin123456",
    "password_confirm": "admin123456",
    "role": "ADMIN"
  }'
```

### 3. Create Chat (Admin only)
```bash
curl -X POST http://127.0.0.1:8000/api/auth/create-chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -d '{
    "title": "Customer Support Chat",
    "description": "Help customer with billing issue"
  }'
```

### 4. Assign Agent (Admin only)
```bash
curl -X POST http://127.0.0.1:8000/api/auth/assign-agent/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -d '{
    "chat_id": 1,
    "agent_id": 2
  }'
```

### 5. View My Chats (Agent only)
```bash
curl -X GET http://127.0.0.1:8000/api/auth/my-chats/ \
  -H "Authorization: Bearer AGENT_ACCESS_TOKEN"
```

## Frontend Integration

The login response includes the user's role, allowing immediate redirection:

```javascript
// Login response
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "superadmin",
    "email": "superadmin@example.com",
    "role": "SUPERADMIN"
  }
}

// React redirect logic
const redirectPath = {
  'SUPERADMIN': '/super-admin',
  'ADMIN': '/admin', 
  'AGENT': '/agent'
}[user.role];

navigate(redirectPath);
```

## Environment Variables

Create a `.env` file:
```
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Production Considerations

- Set `DEBUG=False` in production
- Use a strong `SECRET_KEY`
- Configure proper `ALLOWED_HOSTS`
- Use PostgreSQL instead of SQLite
- Set up proper CORS origins
- Configure HTTPS
- Set appropriate JWT token lifetimes
