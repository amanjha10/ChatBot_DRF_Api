#!/usr/bin/env python3
"""Test complete agent login flow with first login completion"""

import requests

BASE_URL = "http://127.0.0.1:8000"

# Complete first login for the test agent we just created
print("🔧 Completing first login for test agent...")

agent_email = "test.first.login.1756061816@example.com"
temp_password = "nayzBodc"
new_password = "mynewpassword123"

first_login_response = requests.post(f"{BASE_URL}/api/admin-dashboard/agent-first-login/", data={
    'email': agent_email,
    'current_password': temp_password,
    'new_password': new_password,
    'confirm_password': new_password
})

print(f"First login status: {first_login_response.status_code}")

if first_login_response.status_code == 200:
    print("✅ First login completed successfully!")
    
    # Now test unified login with new password
    print("\n🧪 Testing unified login with new password...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
        'username': agent_email,
        'password': new_password
    })
    
    print(f"Login status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        data = login_response.json()
        print("✅ UNIFIED LOGIN SUCCESS!")
        print(f"Role: {data['user']['role']}")
        if 'agent' in data:
            print(f"Agent Status: {data['agent']['status']}")
            print(f"Agent Company ID: {data['agent']['company_id']}")
            print(f"First Login: {data['agent']['is_first_login']}")
            print("\n🎉 COMPLETE AGENT LOGIN FLOW WORKING!")
        else:
            print("❌ Missing agent data")
    else:
        print(f"❌ Login failed: {login_response.text}")
else:
    print(f"❌ First login failed: {first_login_response.text}")
