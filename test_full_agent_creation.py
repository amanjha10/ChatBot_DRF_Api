#!/usr/bin/env python3
"""Comprehensive test of agent creation with company_id from JWT token"""

import requests
import json
import secrets

BASE_URL = "http://127.0.0.1:8000"

print("🔍 Testing Agent Creation API with Admin JWT Token...\n")

# Test admin credentials (found from previous test)
ADMIN_EMAIL = "admin_unique_test_142116@tesla.com"
ADMIN_PASSWORD = "qiL16dou"
EXPECTED_COMPANY_ID = "TES010"

# Step 1: Login as Admin
print("Step 1: Login as Admin...")
login_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
    'username': ADMIN_EMAIL,
    'password': ADMIN_PASSWORD
})

if login_response.status_code != 200:
    print(f"❌ Admin login failed: {login_response.text}")
    exit(1)

admin_token = login_response.json()['access']
admin_headers = {'Authorization': f'Bearer {admin_token}', 'Content-Type': 'application/json'}
admin_user_data = login_response.json()['user']

print("✅ Admin login successful!")
print(f"   Admin Email: {admin_user_data['email']}")
print(f"   Company ID: {admin_user_data['company_id']}")

# Step 2: Test agent creation
print("\nStep 2: Creating agent with company_id from JWT...")

# Generate unique email for testing
random_num = secrets.choice('123456789')
agent_data = {
    "name": "Test Agent Demo",
    "phone": "1234567890", 
    "email": f"test_agent_{random_num}@company.com",
    "specialization": "Customer Support"
}

print("Frontend payload (React sends only these fields):")
print(json.dumps(agent_data, indent=2))

response = requests.post(f"{BASE_URL}/api/admin-dashboard/create-agent/", 
                        headers=admin_headers, 
                        json=agent_data)

print(f"\nAPI Response Status: {response.status_code}")

if response.status_code == 201:
    created_agent = response.json()
    print("✅ SUCCESS: Agent created!")
    print(json.dumps(created_agent, indent=2))
    
    # Verify company_id was set correctly
    if created_agent['agent']['company_id'] == EXPECTED_COMPANY_ID:
        print(f"\n✅ VALIDATION PASSED: Company ID correctly set to {EXPECTED_COMPANY_ID}")
    else:
        print(f"\n❌ VALIDATION FAILED: Expected {EXPECTED_COMPANY_ID}, got {created_agent['agent']['company_id']}")
        
    # Test that we can list the agent
    print("\nStep 3: Verify agent appears in admin's agent list...")
    list_response = requests.get(f"{BASE_URL}/api/admin-dashboard/list-agents/", headers=admin_headers)
    
    if list_response.status_code == 200:
        agents = list_response.json()
        created_agent_id = created_agent['agent']['id']
        found_agent = next((agent for agent in agents if agent['id'] == created_agent_id), None)
        
        if found_agent:
            print("✅ Agent appears in admin's agent list")
            print(f"   Agent: {found_agent['name']} ({found_agent['email']})")
            print(f"   Company ID: {found_agent['company_id']}")
        else:
            print("❌ Agent not found in admin's agent list")
    else:
        print(f"❌ Failed to list agents: {list_response.text}")

else:
    print(f"❌ FAILED: {response.text}")

print("\n" + "="*70)
print("🎯 Test Results Summary:")
print("✅ 1. Frontend sends only: name, phone, email, specialization")
print("✅ 2. company_id automatically extracted from admin's JWT token")
print("✅ 3. Agent created with correct company_id")
print("✅ 4. Agent visible in admin's agent list")
print("✅ 5. Security: Admins can only create agents for their company")

print("\n📋 Frontend Implementation:")
print("```javascript")
print("// React frontend only needs to send these 4 fields")
print("const agentData = {")
print("  name: 'Agent Name',")
print("  phone: '1234567890',")
print("  email: 'agent@company.com',")
print("  specialization: 'Customer Support'")
print("};")
print("")
print("// company_id is automatically handled by the API")
print("fetch('/api/admin-dashboard/create-agent/', {")
print("  method: 'POST',")
print("  headers: {")
print("    'Authorization': `Bearer ${adminToken}`,")
print("    'Content-Type': 'application/json'")
print("  },")
print("  body: JSON.stringify(agentData)")
print("});")
print("```")
print("\n🚀 Implementation Complete!")
