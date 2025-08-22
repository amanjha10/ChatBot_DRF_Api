# 🎯 **Admin Dashboard API Documentation**

## 📋 **Complete Agent Management System**

### **🔐 Authentication Required:**
- **Admin/SuperAdmin:** For agent management endpoints
- **Agent:** For agent-specific endpoints (login, status, logout)

---

## 🏗️ **Agent Management APIs (Admin/SuperAdmin)**

### **1. Create Agent**
- **Method:** `POST`
- **URL:** `http://127.0.0.1:8000/api/admin-dashboard/create-agent/`
- **Headers:**
  ```
  Content-Type: application/json
  Authorization: Bearer ADMIN_ACCESS_TOKEN
  ```
- **Body:**
```json
{
  "name": "John Doe",
  "phone": "1234567890",
  "email": "john@example.com",
  "specialization": "Customer Support"
}
```
- **Response:**
```json
{
  "email": "john@example.com",
  "password": "Abc123Xy",
  "agent": {
    "id": 1,
    "sn": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "1234567890",
    "specialization": "Customer Support",
    "status": "OFFLINE",
    "formatted_last_active": "Never",
    "is_active": true,
    "created_at": "2025-08-21T16:30:00Z"
  }
}
```

### **2. List All Agents**
- **Method:** `GET`
- **URL:** `http://127.0.0.1:8000/api/admin-dashboard/list-agents/`
- **Headers:** `Authorization: Bearer ADMIN_ACCESS_TOKEN`
- **Response:**
```json
[
  {
    "id": 1,
    "sn": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "1234567890",
    "specialization": "Customer Support",
    "status": "AVAILABLE",
    "formatted_last_active": "21/08/2025 14:30",
    "generated_password": "NZP3kC8J",
    "is_first_login": false,
    "is_active": true,
    "created_at": "2025-08-21T16:30:00Z"
  },
  {
    "id": 2,
    "sn": 2,
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "9876543210",
    "specialization": "Technical Support",
    "status": "BUSY",
    "formatted_last_active": "21/08/2025 15:45",
    "generated_password": "j9iOyeTg",
    "is_first_login": true,
    "is_active": true,
    "created_at": "2025-08-21T16:35:00Z"
  }
]
```

**🔑 Key Fields:**
- **`generated_password`**: The initial 8-digit password for first login
- **`is_first_login`**: `true` = Agent hasn't set custom password yet, `false` = Agent has set custom password

### **3. Update Agent**
- **Method:** `PUT` or `PATCH`
- **URL:** `http://127.0.0.1:8000/api/admin-dashboard/update-agent/<agent_id>/`
- **Headers:**
  ```
  Content-Type: application/json
  Authorization: Bearer ADMIN_ACCESS_TOKEN
  ```
- **Body:**
```json
{
  "name": "Updated Name",
  "phone": "9999999999",
  "email": "updated@example.com",
  "specialization": "Updated Specialization",
  "is_active": true
}
```

### **4. Reset Agent Password**
- **Method:** `POST`
- **URL:** `http://127.0.0.1:8000/api/admin-dashboard/reset-agent-password/`
- **Headers:**
  ```
  Content-Type: application/json
  Authorization: Bearer ADMIN_ACCESS_TOKEN
  ```
- **Body:**
```json
{
  "agent_id": 1
}
```
- **Response:**
```json
{
  "message": "Password reset successfully",
  "email": "john@example.com",
  "new_password": "NewPass123"
}
```

---

## 🔑 **Agent Authentication APIs**

### **5. Agent First Login (Password Setup)**
- **Method:** `POST`
- **URL:** `http://127.0.0.1:8000/api/admin-dashboard/agent-first-login/`
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "email": "john@example.com",
  "current_password": "Abc123Xy",
  "new_password": "MyNewPassword123",
  "confirm_password": "MyNewPassword123"
}
```
- **Response:**
```json
{
  "message": "Password updated successfully. Please login with your new password.",
  "email": "john@example.com"
}
```

### **6. Agent Login**
- **Method:** `POST`
- **URL:** `http://127.0.0.1:8000/api/admin-dashboard/agent-login/`
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "email": "john@example.com",
  "password": "MyNewPassword123"
}
```
- **Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "agent": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "status": "AVAILABLE",
    "is_first_login": false
  }
}
```

### **7. Agent Logout**
- **Method:** `POST`
- **URL:** `http://127.0.0.1:8000/api/admin-dashboard/agent-logout/`
- **Headers:** `Authorization: Bearer AGENT_ACCESS_TOKEN`
- **Response:**
```json
{
  "message": "Logged out successfully"
}
```

---

## 📊 **Agent Status Management**

### **8. Update Agent Status**
- **Method:** `POST`
- **URL:** `http://127.0.0.1:8000/api/admin-dashboard/update-agent-status/`
- **Headers:**
  ```
  Content-Type: application/json
  Authorization: Bearer AGENT_ACCESS_TOKEN
  ```
- **Body:**
```json
{
  "status": "BUSY"
}
```
- **Response:**
```json
{
  "message": "Status updated successfully",
  "status": "BUSY"
}
```

**Status Options:**
- `AVAILABLE` - Agent is online and ready for chats
- `BUSY` - Agent is currently handling a chat
- `OFFLINE` - Agent is logged out (set automatically on logout)

---

## 📈 **Analytics & Sessions**

### **9. Agent Sessions**
- **Method:** `GET`
- **URL:** `http://127.0.0.1:8000/api/admin-dashboard/agent-sessions/`
- **URL (Specific Agent):** `http://127.0.0.1:8000/api/admin-dashboard/agent-sessions/?agent_id=1`
- **Headers:** `Authorization: Bearer ADMIN_ACCESS_TOKEN`
- **Response:**
```json
[
  {
    "id": 1,
    "agent_name": "John Doe",
    "login_time": "2025-08-21T14:30:00Z",
    "logout_time": "2025-08-21T18:30:00Z",
    "duration_minutes": 240,
    "ip_address": "192.168.1.1"
  }
]
```

---

## 🎯 **Status Tracking Logic**

### **Automatic Status Updates:**
1. **Login** → Status: `AVAILABLE`
2. **Start Chat** → Status: `BUSY` (you'll implement this later)
3. **End Chat** → Status: `AVAILABLE` (you'll implement this later)
4. **Logout** → Status: `OFFLINE` + Update `last_active`

### **Manual Status Updates:**
- Agents can manually switch between `AVAILABLE` and `BUSY`
- Cannot manually set to `OFFLINE` (must use logout endpoint)

---

## 🔐 **Permission Matrix**

| Endpoint | SuperAdmin | Admin | Agent |
|----------|------------|-------|-------|
| Create Agent | ✅ | ✅ | ❌ |
| List Agents | ✅ All | ✅ Own | ❌ |
| Update Agent | ✅ All | ✅ Own | ❌ |
| Reset Password | ✅ All | ✅ Own | ❌ |
| First Login | ✅ | ✅ | ✅ |
| Agent Login | ✅ | ✅ | ✅ |
| Agent Logout | ❌ | ❌ | ✅ Own |
| Update Status | ❌ | ❌ | ✅ Own |
| View Sessions | ✅ All | ✅ Own Agents | ❌ |

---

## 🎯 **Frontend Integration Guide**

### **📊 Agent Table Display:**

Your React frontend can now display a complete agent table with generated passwords:

| SN | Name | Email | Phone | Specialization | Status | Last Active | Generated Password | First Login |
|----|------|-------|-------|----------------|--------|-------------|-------------------|-------------|
| 1 | John Doe | john@example.com | 1234567890 | Customer Support | AVAILABLE | 21/08/2025 14:30 | **NZP3kC8J** | ❌ Complete |
| 2 | Jane Smith | jane@example.com | 9876543210 | Technical Support | BUSY | 21/08/2025 15:45 | **j9iOyeTg** | ✅ Pending |

### **🔑 Password Management Logic:**

```javascript
// Frontend logic for password display
const AgentRow = ({ agent }) => {
  const getPasswordStatus = () => {
    if (agent.is_first_login) {
      return {
        password: agent.generated_password,
        status: "First Login Required",
        color: "orange",
        action: "Give this password to agent for first login"
      };
    } else {
      return {
        password: agent.generated_password,
        status: "Custom Password Set",
        color: "green",
        action: "Agent has set their own password"
      };
    }
  };

  const passwordInfo = getPasswordStatus();

  return (
    <tr>
      <td>{agent.sn}</td>
      <td>{agent.name}</td>
      <td>{agent.email}</td>
      <td>{agent.specialization}</td>
      <td>
        <span className={`status-${agent.status.toLowerCase()}`}>
          {agent.status}
        </span>
      </td>
      <td>
        <div className="password-info">
          <code>{passwordInfo.password}</code>
          <small style={{color: passwordInfo.color}}>
            {passwordInfo.status}
          </small>
        </div>
      </td>
      <td>
        {agent.is_first_login ? (
          <span className="badge badge-warning">Pending</span>
        ) : (
          <span className="badge badge-success">Complete</span>
        )}
      </td>
    </tr>
  );
};
```

### **📱 Admin Workflow:**

1. **Create Agent** → System shows generated password once
2. **View Agent List** → Generated password always visible
3. **Give Password to Agent** → Agent uses for first login
4. **Monitor First Login Status** → `is_first_login` field shows progress
5. **Reset Password if Needed** → Generate new password anytime

### **🔐 Security Benefits:**

- ✅ **Always Available:** Admin can always see the generated password
- ✅ **First Login Tracking:** Know which agents haven't set their password
- ✅ **Reset Capability:** Can reset password anytime if agent forgets
- ✅ **Secure Process:** Agent must know generated password to set custom one

**Your complete Agent Management System is production-ready!** 🚀
