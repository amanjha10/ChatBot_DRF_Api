# Plan Management System API Documentation

## 🚀 **Perfect Plan Management System**

### **Overview**
The plan management system allows SuperAdmins to:
1. Create subscription plans with standard names (basic, pro, premium) and flexible agent limits
2. Assign plans to admin users during creation
3. Track plan assignments with subscription management (cancel, renew, upgrade)
4. Preserve historical data for all subscription changes
5. View comprehensive reports of user-plan relationships

**Key Features:**
- ✅ **Standard Plan Names:** Easy to remember (basic, pro, premium)
- ✅ **Flexible Agent Limits:** Frontend specifies agent count (no auto-restrictions)
- ✅ **ID-Based References:** Easy mapping (basic=1, pro=2, premium=3)
- ✅ **Subscription Management:** Cancel, renew, upgrade with history preservation
- ✅ **Clean Implementation:** Simple, maintainable code

---

## 📋 **API Endpoints**

### **1. Create Plan**
**Endpoint:** `POST /api/auth/create-plan/`
**Authentication:** SuperAdmin only

**Request:**
```json
{
  "plan_name": "basic",            // Options: "basic", "pro", "premium"
  "max_agents": 5,                 // Frontend specifies agent count
  "price": "99.99"
}
```

**Response:**
```json
{
  "id": 1,
  "plan_name": "basic",
  "plan_name_display": "Basic",
  "max_agents": 5,
  "price": "99.99",
  "is_active": true,
  "created_at": "2025-08-21T12:58:19.663918Z"
}
```

---

### **2. List All Plans**
**Endpoint:** `GET /api/auth/list-plans/`
**Authentication:** SuperAdmin only

**Response:**
```json
[
  {
    "id": 1,
    "plan_name": "basic",
    "plan_name_display": "Basic",
    "max_agents": 5,
    "price": "99.99",
    "is_active": true,
    "created_at": "2025-08-21T13:04:56.516008Z"
  },
  {
    "id": 2,
    "plan_name": "pro",
    "plan_name_display": "Pro",
    "max_agents": 10,
    "price": "199.99",
    "is_active": true,
    "created_at": "2025-08-21T13:05:27.528705Z"
  },
  {
    "id": 3,
    "plan_name": "premium",
    "plan_name_display": "Premium",
    "max_agents": 20,
    "price": "299.99",
    "is_active": true,
    "created_at": "2025-08-21T13:05:46.104414Z"
  }
]
```

---

### **3. Create Admin with Plan**
**Endpoint:** `POST /api/auth/create-admin/`
**Authentication:** SuperAdmin only

**Request:**
```json
{
  "email": "admin@company.com",
  "address": "123 Main Street",
  "contact_person": "Emergency Contact Name",
  "contact_number": "9876543210",
  "phone_number": "1234567890",
  "plan_id": 2  // Plan ID from list-plans endpoint
}
```

**Response:**
```json
{
  "email": "premium@company.com",
  "password": "B9lSmRYw",
  "plan": {
    "id": 3,
    "name": "Premium",
    "max_agents": 20,
    "price": "299.99"
  }
}
```

**Note:** When a plan is assigned, a UserPlanAssignment record is automatically created with:
- Start date: Current timestamp
- Expiry date: 1 year from start date
- Status: "active"

---

### **4. List User Plan Assignments (Combined Table)**
**Endpoint:** `GET /api/auth/list-user-plan-assignments/`
**Authentication:** SuperAdmin only

**Response:**
```json
[
  {
    "id": 3,
    "user_details": {
      "id": 3,
      "username": "testadmin",
      "email": "testadmin@company.com",
      "role": "ADMIN"
    },
    "plan_details": {
      "id": 2,
      "plan_name": "Pro",
      "max_agents": 10,
      "price": "199.99"
    },
    "start_date": "2025-08-21T11:33:30.121566Z",
    "expiry_date": "2026-08-21T11:32:49.297342Z",
    "status": "active",
    "status_display": "Active",
    "days_remaining": 364,
    "is_expired": false,
    "notes": "Upgraded from Basic to Pro. User requested upgrade to Pro plan",
    "created_at": "2025-08-21T11:33:30.121756Z"
  },
  {
    "id": 2,
    "user_details": {
      "id": 3,
      "username": "testadmin",
      "email": "testadmin@company.com",
      "role": "ADMIN"
    },
    "plan_details": {
      "id": 1,
      "plan_name": "Basic",
      "max_agents": 5,
      "price": "99.99"
    },
    "start_date": "2025-08-21T11:32:49.297342Z",
    "expiry_date": "2026-08-21T11:32:49.297342Z",
    "status": "upgraded",
    "status_display": "Upgraded",
    "days_remaining": 364,
    "is_expired": false,
    "notes": "Upgraded to assignment ID: 3",
    "created_at": "2025-08-21T11:32:49.297414Z"
  }
]
```

---

## 🔄 **Subscription Management Endpoints**

### **5. Cancel Subscription**
**Endpoint:** `POST /api/auth/cancel-subscription/`
**Authentication:** SuperAdmin only

**Request:**
```json
{
  "assignment_id": 1,
  "reason": "User requested cancellation"
}
```

**Response:**
```json
{
  "message": "Subscription cancelled successfully",
  "assignment": {
    "id": 1,
    "status": "cancelled",
    "notes": "User requested cancellation"
  }
}
```

### **6. Renew Subscription**
**Endpoint:** `POST /api/auth/renew-subscription/`
**Authentication:** SuperAdmin only

**Request:**
```json
{
  "assignment_id": 1,
  "expiry_date": "2026-08-21T10:00:00Z"  // Optional - defaults to 1 year
}
```

**Response:**
```json
{
  "message": "Subscription renewed successfully",
  "new_assignment": {
    "id": 4,
    "status": "active",
    "start_date": "2025-08-21T12:00:00Z",
    "expiry_date": "2026-08-21T12:00:00Z",
    "notes": "Subscription renewed"
  }
}
```

### **7. Upgrade Plan**
**Endpoint:** `POST /api/auth/upgrade-plan/`
**Authentication:** SuperAdmin only

**Request:**
```json
{
  "assignment_id": 1,
  "new_plan_id": 2,
  "reason": "User requested upgrade to Pro"
}
```

**Response:**
```json
{
  "message": "Plan upgraded successfully",
  "new_assignment": {
    "id": 5,
    "plan_details": {
      "id": 2,
      "plan_name": "Pro",
      "max_agents": 10,
      "price": "199.99"
    },
    "status": "active",
    "notes": "Upgraded from Basic to Pro. User requested upgrade to Pro"
  }
}
```

---

---

## 🎯 **Key Advantages of Perfect System**

### **✅ Best of Both Worlds:**
- **Standard Plan Names:** Easy to remember (basic, pro, premium)
- **Flexible Agent Limits:** Frontend specifies exact agent count (5, 10, 20, etc.)
- **ID-Based Mapping:** Simple references (basic=1, pro=2, premium=3)
- **No Auto-Restrictions:** Full control over agent limits

### **✅ Clean Implementation:**
- **Minimal Code:** No complex auto-setting logic
- **Simple API:** Just 3 fields: plan_name, max_agents, price
- **Frontend Control:** All business logic handled in React dashboard
- **Easy Maintenance:** Clean, maintainable codebase

### **✅ Perfect for SuperAdmin Dashboard:**
- **Predictable IDs:** Always know basic=1, pro=2, premium=3
- **Flexible Limits:** Set any agent count per plan
- **Standard Names:** Easy to understand and remember
- **Agent Restrictions:** Will be implemented later in Admin dashboard logic

---

## 🧪 **Testing in Postman**

### **Step 1: Get SuperAdmin Token**
- **URL:** `http://127.0.0.1:8000/api/auth/login/`
- **Method:** POST
- **Body:**
```json
{
  "username": "superadmin",
  "password": "admin123456"
}
```

### **Step 2: Create Standard Plans**
- **URL:** `http://127.0.0.1:8000/api/auth/create-plan/`
- **Method:** POST
- **Headers:** `Authorization: Bearer YOUR_TOKEN`

**Create Basic Plan:**
```json
{
  "plan_name": "basic",
  "max_agents": 5,
  "price": "99.99"
}
```

**Create Pro Plan:**
```json
{
  "plan_name": "pro",
  "max_agents": 10,
  "price": "199.99"
}
```

**Create Premium Plan:**
```json
{
  "plan_name": "premium",
  "max_agents": 20,
  "price": "299.99"
}
```

### **Step 3: List Plans**
- **URL:** `http://127.0.0.1:8000/api/auth/list-plans/`
- **Method:** GET
- **Headers:** `Authorization: Bearer YOUR_TOKEN`

### **Step 4: Create Admin with Standard Plan**
- **URL:** `http://127.0.0.1:8000/api/auth/create-admin/`
- **Method:** POST
- **Headers:** `Authorization: Bearer YOUR_TOKEN`
- **Body:**
```json
{
  "email": "premium@company.com",
  "address": "123 Premium Street",
  "contact_person": "Emergency Contact",
  "contact_number": "9876543210",
  "phone_number": "1234567890",
  "plan_id": 3
}
```

### **Step 5: View Plan Assignments**
- **URL:** `http://127.0.0.1:8000/api/auth/list-user-plan-assignments/`
- **Method:** GET
- **Headers:** `Authorization: Bearer YOUR_TOKEN`

---

## 📱 **React Frontend Integration**

### **Create Custom Plan Form:**
```javascript
const createPlan = async (planData) => {
  const response = await fetch('http://192.168.1.90:8000/api/auth/create-plan/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${superAdminToken}`,
    },
    credentials: 'include',
    body: JSON.stringify({
      plan_name: planData.planName,        // Any custom name
      max_agents: planData.maxAgents,      // Frontend specifies agent count
      price: planData.price
    }),
  });
  return await response.json();
};

// Example usage:
// createPlan({
//   planName: "Startup Plan",
//   maxAgents: 3,
//   price: "49.99"
// });
```

### **Load Plans for Dropdown:**
```javascript
const loadPlans = async () => {
  const response = await fetch('http://192.168.1.90:8000/api/auth/list-plans/', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${superAdminToken}`,
    },
    credentials: 'include',
  });
  const plans = await response.json();

  // Use in React select dropdown
  return plans.map(plan => ({
    value: plan.id,
    label: `${plan.plan_name} - ${plan.max_agents} agents ($${plan.price})`
  }));
};

// Example dropdown options:
// [
//   { value: 3, label: "Startup Plan - 3 agents ($49.99)" },
//   { value: 4, label: "Enterprise Plan - 25 agents ($499.99)" },
//   { value: 5, label: "Custom Business Plan - 12 agents ($199.99)" }
// ]
```

### **Create Admin with Plan:**
```javascript
const createAdminWithPlan = async (formData) => {
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
      contact_person: formData.contactPerson,
      contact_number: formData.contactNumber,
      phone_number: formData.phoneNumber,
      plan: formData.selectedPlanId  // Plan ID from dropdown
    }),
  });
  return await response.json();
};
```

### **Dashboard Table for Plan Assignments:**
```javascript
const loadPlanAssignments = async () => {
  const response = await fetch('http://192.168.1.90:8000/api/auth/list-user-plan-assignments/', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${superAdminToken}`,
    },
    credentials: 'include',
  });
  return await response.json();
};

// Display in table format:
// | User | Plan | Company | Start Date | Expiry Date | Days Remaining | Status |
```

---

## 🗄️ **Database Schema**

### **Plan Model:**
- `id` (Primary Key)
- `plan_name` (basic/pro/premium)
- `company_name`
- `price` (Decimal)
- `is_active` (Boolean)
- `created_at`, `updated_at`

### **User Model (Updated):**
- `plan` (Foreign Key to Plan)
- All existing fields...

### **UserPlanAssignment Model (Combined Table):**
- `id` (Primary Key)
- `user` (Foreign Key to User)
- `plan` (Foreign Key to Plan)
- `company_name` (Denormalized)
- `start_date`, `expiry_date`
- `is_active`, `is_expired` (Computed)
- `days_remaining` (Computed)

**Your complete plan management system is ready for production use!** 🎯
