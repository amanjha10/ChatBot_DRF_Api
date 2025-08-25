# UNIFIED LOGIN API DOCUMENTATION

## Overview
The authentication system now supports **unified login** for all user roles through a single endpoint. All users (SuperAdmin, Admin, Agent) can authenticate using the same API endpoint with role-specific responses.

## Unified Login Endpoint

### POST `/api/auth/login/`
**Authentication endpoint for all user roles**

#### Request Format
```json
{
    "username": "user@example.com",  // Can be username or email
    "password": "password123"
}
```

#### Response Formats

##### SuperAdmin Response
```json
{
    "access": "jwt_access_token",
    "refresh": "jwt_refresh_token",
    "user": {
        "id": 1,
        "role": "SUPERADMIN",
        "email": "superadmin@example.com",
        "username": "superadmin"
    }
}
```

##### Admin Response
```json
{
    "access": "jwt_access_token",
    "refresh": "jwt_refresh_token",
    "user": {
        "id": 2,
        "role": "ADMIN",
        "email": "admin@company.com",
        "company_id": "COM001",
        "name": "Company Name"
    }
}
```

##### Agent Response (Successful Login)
```json
{
    "access": "jwt_access_token",
    "refresh": "jwt_refresh_token",
    "user": {
        "id": 3,
        "role": "AGENT",
        "email": "agent@example.com"
    },
    "agent": {
        "id": 1,
        "name": "Agent Name",
        "email": "agent@example.com",
        "status": "AVAILABLE",
        "is_first_login": false,
        "company_id": "COM001"
    }
}
```

##### Agent Response (First Login Required)
```json
{
    "error": "First login required",
    "message": "Please set your password using the first-login endpoint",
    "is_first_login": true,
    "email": "agent@example.com"
}
```

## Authentication Flow

### SuperAdmin & Admin
1. Direct login with credentials
2. Receive JWT tokens immediately
3. Use tokens for authenticated requests

### Agent Authentication Flow
1. **Initial Login Attempt**: Agent uses temporary password
2. **First Login Check**: System detects `is_first_login = true`
3. **First Login Setup**: Agent completes password setup via `/api/admin-dashboard/agent-first-login/`
4. **Subsequent Logins**: Agent uses new password for normal authentication

## Features

### ✅ Unified Authentication
- Single endpoint for all user roles
- Role-based response formatting
- Automatic role detection

### ✅ Agent-Specific Features
- Automatic status update to "AVAILABLE" on login
- Session tracking with IP address logging
- First login flow integration
- Company isolation enforcement

### ✅ Security Features
- JWT-based authentication
- Company isolation for agents and admins
- Secure password reset flow for agents
- Session management

### ✅ Company Isolation
- Agents automatically inherit admin's company_id
- Admins can only manage agents from their company
- Company-based data filtering throughout system

## Example Usage

### JavaScript/React Example
```javascript
const loginUser = async (username, password) => {
    const response = await fetch('/api/auth/login/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    
    if (response.ok) {
        // Handle based on user role
        switch (data.user.role) {
            case 'SUPERADMIN':
                // Redirect to super admin dashboard
                break;
            case 'ADMIN':
                // Redirect to admin dashboard
                localStorage.setItem('company_id', data.user.company_id);
                break;
            case 'AGENT':
                if (data.agent) {
                    // Successful agent login
                    localStorage.setItem('agent_status', data.agent.status);
                } else {
                    // Handle first login required
                    // Redirect to first login setup
                }
                break;
        }
        
        // Store tokens
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
    }
};
```

### Python Example
```python
import requests

def login_user(username, password):
    response = requests.post('http://127.0.0.1:8000/api/auth/login/', data={
        'username': username,
        'password': password
    })
    
    if response.status_code == 200:
        data = response.json()
        
        # Check user role
        role = data['user']['role']
        
        if role == 'AGENT':
            if 'error' in data and 'first login' in data['error']:
                print("Agent needs to complete first login")
                return None
            else:
                print(f"Agent login successful. Status: {data['agent']['status']}")
        
        return {
            'access_token': data['access'],
            'refresh_token': data['refresh'],
            'user': data['user'],
            'agent': data.get('agent')  # Only present for agents
        }
    
    return None
```

## Migration Notes

### For Frontend Applications
- **No Breaking Changes**: Existing login implementations continue to work
- **Enhanced Responses**: Agent logins now include additional agent data
- **Role-Based Routing**: Use `user.role` to determine dashboard routing

### Deprecated Endpoints
- Consider deprecating separate agent login endpoints
- Unified login handles all authentication scenarios
- Maintains backward compatibility during transition period

## Testing

### Test Coverage
✅ SuperAdmin login  
✅ Admin login with company_id  
✅ Agent first login detection  
✅ Agent login after first login setup  
✅ Role-based response formatting  
✅ Company isolation enforcement  
✅ Session tracking for agents  

### Test Scripts Available
- `test_unified_login_final.py` - Comprehensive test suite
- `test_complete_agent_flow.py` - Agent-specific flow testing

## Security Considerations

### JWT Token Security
- Access tokens have limited lifespan
- Refresh tokens for extended sessions
- Role-based permissions enforced

### Company Isolation
- Automatic company_id inheritance for agents
- Admin actions restricted to their company
- Data filtering at model level

### Agent Security
- Forced first login with password change
- Session tracking for audit trails
- Status management for availability

## API Compatibility

### Backward Compatibility
- All existing endpoints remain functional
- Response formats enhanced, not changed
- Gradual migration support

### Forward Compatibility
- Extensible role-based response system
- Easy addition of new user roles
- Flexible authentication flow support

---

**🚀 UNIFIED LOGIN IMPLEMENTATION COMPLETE**  
**📅 Implementation Date**: August 25, 2025  
**✅ Status**: Production Ready  
**🔧 Version**: v2.0 - Unified Authentication
