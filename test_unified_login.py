#!/usr/bin/env python3
"""Test unified login endpoint for all user roles"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("🔍 Testing Unified Login API for All User Roles...\n")

# Test credentials
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

def test_login(role, username, password, expected_role):
    """Test login for a specific user role"""
    print(f"🧪 Testing {role} Login...")
    print(f"   Username: {username}")
    
    response = requests.post(f"{BASE_URL}/api/auth/login/", data={
        'username': username,
        'password': password
    })
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Verify response structure
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
        
        return True
    else:
        print(f"   ❌ Login failed: {response.text}")
        return False

# Test all roles
print("="*60)
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

# Test Agent login (need to get agent credentials first)
print("\n🔍 Getting Agent credentials for testing...")
superadmin_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
    'username': 'superadmin',
    'password': 'superadmin123'
})

if superadmin_response.status_code == 200:
    token = superadmin_response.json()['access']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get agents list
    agents_response = requests.get(f"{BASE_URL}/api/admin-dashboard/list-agents/", headers=headers)
    
    if agents_response.status_code == 200:
        agents = agents_response.json()
        
        if agents:
            # Test with first agent
            agent = agents[0]
            agent_email = agent['email']
            
            # Get agent credentials from debug endpoint
            debug_response = requests.get(f"{BASE_URL}/api/admin-dashboard/debug-agent/{agent['id']}/", headers=headers)
            
            if debug_response.status_code == 200:
                debug_data = debug_response.json()
                agent_password = debug_data.get('generated_password')
                
                if agent_password:
                    print(f"🧪 Testing Agent Login...")
                    print(f"   Email: {agent_email}")
                    print(f"   Password: {agent_password}")
                    
                    agent_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
                        'username': agent_email,
                        'password': agent_password
                    })
                    
                    print(f"   Status Code: {agent_response.status_code}")
                    
                    if agent_response.status_code == 200:
                        agent_data = agent_response.json()
                        
                        # Check for agent-specific fields
                        if 'agent' in agent_data:
                            print(f"   ✅ Agent login successful!")
                            print(f"   Role: {agent_data['user']['role']}")
                            print(f"   Agent Status: {agent_data['agent']['status']}")
                            print(f"   First Login: {agent_data['agent']['is_first_login']}")
                            results.append(("Agent", True))
                        else:
                            print(f"   ❌ Missing agent data in response")
                            results.append(("Agent", False))
                    else:
                        response_data = agent_response.json()
                        if 'is_first_login' in response_data:
                            print(f"   ⚠️  Agent requires first login setup")
                            print(f"   Message: {response_data.get('message', '')}")
                            results.append(("Agent (First Login)", True))
                        else:
                            print(f"   ❌ Agent login failed: {agent_response.text}")
                            results.append(("Agent", False))
                else:
                    print("   ❌ No agent password found")
                    results.append(("Agent", False))
            else:
                print("   ❌ Could not get agent debug info")
                results.append(("Agent", False))
        else:
            print("   ⚠️  No agents found to test with")
            results.append(("Agent", False))
    else:
        print(f"   ❌ Could not get agents list: {agents_response.text}")
        results.append(("Agent", False))
else:
    print("   ❌ Could not login as superadmin to get agent credentials")
    results.append(("Agent", False))

# Summary
print("\n" + "="*60)
print("🎯 UNIFIED LOGIN TEST RESULTS")
print("="*60)

all_passed = True
for role, success in results:
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{role:<20} : {status}")
    if not success:
        all_passed = False

print("-"*60)
if all_passed:
    print("🎉 ALL TESTS PASSED! Unified login working for all roles!")
else:
    print("⚠️  Some tests failed. Check individual results above.")

print("\n📋 API Usage:")
print("All user roles can now use: POST /api/auth/login/")
print("• SuperAdmin: username + password")
print("• Admin: email + password") 
print("• Agent: email + password")
print("• Response includes role-specific data automatically")
print("\n🚀 Unified authentication complete!")
