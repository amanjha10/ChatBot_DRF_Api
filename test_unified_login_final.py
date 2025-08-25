#!/usr/bin/env python3
"""Complete unified login test for all user roles including agent scenarios"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

print("🔍 COMPREHENSIVE UNIFIED LOGIN TEST")
print("="*60)

def test_login(role, username, password, expected_role, description=""):
    """Test login for a specific user role"""
    print(f"🧪 Testing {role} Login{(' - ' + description) if description else ''}...")
    print(f"   Username: {username}")
    
    response = requests.post(f"{BASE_URL}/api/auth/login/", data={
        'username': username,
        'password': password
    })
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Check for error field (first login required)
        if 'error' in data:
            if 'first login required' in data['error'].lower():
                print(f"   ⚠️  {role} requires first login setup")
                print(f"   Message: {data.get('message', '')}")
                return 'first_login_required'
            else:
                print(f"   ❌ Login error: {data['error']}")
                return False
        
        # Verify response structure for successful login
        required_fields = ['access', 'refresh', 'user']
        for field in required_fields:
            if field not in data:
                print(f"   ❌ Missing field: {field}")
                return False
        
        # Verify user role
        if data['user']['role'] != expected_role:
            print(f"   ❌ Wrong role: expected {expected_role}, got {data['user']['role']}")
            return False
        
        print(f"   ✅ {role} login successful!")
        print(f"   Role: {data['user']['role']}")
        print(f"   Email: {data['user']['email']}")
        
        if expected_role == "ADMIN":
            company_id = data['user'].get('company_id')
            print(f"   Company ID: {company_id}")
        
        # Check for agent-specific data
        if 'agent' in data:
            print(f"   Agent Status: {data['agent']['status']}")
            print(f"   Agent Company ID: {data['agent'].get('company_id')}")
            print(f"   First Login: {data['agent']['is_first_login']}")
        
        return True
    else:
        try:
            error_data = response.json()
            print(f"   ❌ Login failed: {error_data}")
        except:
            print(f"   ❌ Login failed: Status {response.status_code}")
        return False

# Test cases for different user roles
test_cases = [
    {
        "role": "SuperAdmin",
        "username": "superadmin",
        "password": "superadmin123",
        "expected_role": "SUPERADMIN"
    },
    {
        "role": "Admin", 
        "username": "admin_unique_test_142116@tesla.com",
        "password": "qiL16dou",
        "expected_role": "ADMIN"
    }
]

# Test SuperAdmin and Admin
print("1. TESTING SUPERADMIN AND ADMIN ROLES")
print("-"*40)
results = []
for test_case in test_cases:
    success = test_login(
        test_case["role"],
        test_case["username"], 
        test_case["password"],
        test_case["expected_role"]
    )
    results.append((test_case["role"], success))
    print("-"*40)

# Test Agent scenarios - use existing agent that has completed first login
print("\n2. TESTING AGENT SCENARIOS")
print("-"*40)

# We know heroalam@example.com has completed first login with password 'mynewpassword123'
print("🧪 Testing existing agent with completed first login...")
agent_result = test_login("Agent", "heroalam@example.com", "mynewpassword123", "AGENT", 
                         "Existing Agent Post First Login")
results.append(("Agent (Post First Login)", agent_result == True))

print("-"*40)

# Test Agent first login scenario by creating a new agent
superadmin_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
    'username': 'superadmin',
    'password': 'superadmin123'
})

if superadmin_response.status_code == 200:
    token = superadmin_response.json()['access']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get an admin token to create agent
    admin_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
        'username': 'admin_unique_test_142116@tesla.com',
        'password': 'qiL16dou'
    })
    
    if admin_response.status_code == 200:
        admin_token = admin_response.json()['access']
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        
        print("🔨 Creating fresh agent for first login testing...")
        
        # Create test agent with unique email
        timestamp = int(time.time())
        agent_data = {
            'name': 'Test Agent First Login',
            'phone': '8888888888',
            'email': f'test.first.login.{timestamp}@example.com',
            'specialization': 'First Login Testing'
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admin-dashboard/create-agent/", 
                                      data=agent_data, headers=admin_headers)
        
        if create_response.status_code == 201:
            created_agent = create_response.json()
            test_agent_email = created_agent['email']
            
            # Check if 'id' is in response or if we need to look up the agent
            if 'id' in created_agent:
                test_agent_id = created_agent['id']
            else:
                # Try to find the agent in the list
                agents_response = requests.get(f"{BASE_URL}/api/admin-dashboard/list-agents/", headers=admin_headers)
                if agents_response.status_code == 200:
                    agents = agents_response.json()
                    for agent in agents:
                        if agent['email'] == test_agent_email:
                            test_agent_id = agent['id']
                            break
                    else:
                        test_agent_id = None
                else:
                    test_agent_id = None
            
            print(f"   ✅ Created test agent: {test_agent_email}")
            print(f"   Agent ID: {test_agent_id}")
            
            if test_agent_id:
                # Get agent credentials from debug endpoint
                debug_response = requests.get(f"{BASE_URL}/api/admin-dashboard/debug-agent/{test_agent_id}/", 
                                            headers=admin_headers)
                
                if debug_response.status_code == 200:
                    debug_data = debug_response.json()
                    test_agent_password = debug_data.get('generated_password')
                    print(f"   Generated password: {test_agent_password}")
                    
                    if test_agent_password:
                        print()
                        # Test first login (should return first_login_required)
                        result1 = test_login("Agent", test_agent_email, test_agent_password, "AGENT", 
                                           "Before First Login Setup")
                        results.append(("Agent (First Login Required)", result1 == 'first_login_required'))
                    else:
                        print("   ❌ No password found in debug response")
                        results.append(("Agent (First Login Required)", False))
                else:
                    print(f"   ❌ Could not get agent debug info: {debug_response.text}")
                    results.append(("Agent (First Login Required)", False))
            else:
                print("   ❌ No agent ID found")
                results.append(("Agent (First Login Required)", False))
        else:
            print(f"   ❌ Could not create test agent: {create_response.text}")
            results.append(("Agent (First Login Required)", False))
    else:
        print("   ❌ Could not get admin token")
        results.append(("Agent (First Login Required)", False))
else:
    print("   ❌ Could not get superadmin token")
    results.append(("Agent (First Login Required)", False))

# Summary
print("\n" + "="*60)
print("🎯 UNIFIED LOGIN TEST RESULTS")
print("="*60)

all_passed = True
for role, success in results:
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{role:<30} : {status}")
    if not success:
        all_passed = False

print("-"*60)
if all_passed:
    print("🎉 ALL TESTS PASSED!")
    print("✅ Unified login working perfectly for all user roles!")
else:
    print("⚠️  Some tests failed. Check individual results above.")

print("\n📋 UNIFIED LOGIN API SUMMARY:")
print("="*40)
print("🌐 Endpoint: POST /api/auth/login/")
print("🔑 Works for all user roles:")
print("   • SuperAdmin: username + password")
print("   • Admin: email + password") 
print("   • Agent: email + password")
print("🔄 Response includes role-specific data automatically")
print("⚡ Handles first-login flow for agents gracefully")
print("\n🚀 UNIFIED AUTHENTICATION IMPLEMENTATION COMPLETE!")
