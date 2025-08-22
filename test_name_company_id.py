#!/usr/bin/env python3
"""
Test script for admin creation with name field and updated company_id generation.
"""

import requests
import json
import random

# Configuration
BASE_URL = "http://127.0.0.1:8000"
SUPERADMIN_USERNAME = "superadmin"  # Changed from email to username
SUPERADMIN_PASSWORD = "superadmin123"

def test_admin_creation_with_name():
    """Test admin creation with name field and company_id generation from name."""
    
    # Step 1: Login as SuperAdmin
    print("🔐 Logging in as SuperAdmin...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
        'username': SUPERADMIN_USERNAME,
        'password': SUPERADMIN_PASSWORD
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return
    
    token = login_response.json()['access']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    print("✅ Login successful!")
    
    # Step 2: Get available plans
    print("\n📋 Getting available plans...")
    plans_response = requests.get(f"{BASE_URL}/api/auth/list-plans/", headers=headers)
    if plans_response.status_code == 200:
        plans = plans_response.json()
        if plans:
            plan_id = plans[0]['id']
            print(f"✅ Using plan: {plans[0]['plan_name_display']} (ID: {plan_id})")
        else:
            print("❌ No plans available")
            return
    else:
        print(f"❌ Failed to get plans: {plans_response.status_code}")
        return
    
    # Step 3: Test admin creation with different names
    test_cases = [
        {
            "name": "John Smith Technology",
            "email": f"john.smith{random.randint(1000,9999)}@techcorp.com",
            "expected_prefix": "JOH"  # First 3 letters from "John"
        },
        {
            "name": "Microsoft Corporation",
            "email": f"admin{random.randint(1000,9999)}@microsoft.com", 
            "expected_prefix": "MIC"  # First 3 letters from "Microsoft"
        },
        {
            "name": "Apple Inc",
            "email": f"admin{random.randint(1000,9999)}@apple.com",
            "expected_prefix": "APP"  # First 3 letters from "Apple"
        },
        {
            "name": "AI Solutions",
            "email": f"admin{random.randint(1000,9999)}@aisolutions.com",
            "expected_prefix": "AIS"  # First 3 letters from "AISolutions" (spaces removed)
        }
    ]
    
    print(f"\n🧪 Testing {len(test_cases)} admin creation scenarios...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['name']} ---")
        
        admin_data = {
            "name": test_case["name"],
            "email": test_case["email"],
            "address": "123 Business St",
            "contact_person": "Contact Person",
            "contact_number": "123-456-7890",
            "phone_number": "098-765-4321",
            "plan_id": plan_id
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/create-admin/", 
                               headers=headers, 
                               data=json.dumps(admin_data))
        
        if response.status_code == 201:
            result = response.json()
            company_id = result.get('company_id', 'N/A')
            name = result.get('name', 'N/A')
            
            print(f"✅ Admin created successfully!")
            print(f"   📛 Name: {name}")
            print(f"   📧 Email: {result.get('email', 'N/A')}")
            print(f"   🆔 Company ID: {company_id}")
            print(f"   🔑 Generated Password: {result.get('password', 'N/A')}")
            
            # Verify company_id format
            if company_id.startswith(test_case["expected_prefix"]):
                print(f"   ✅ Company ID prefix correct: {test_case['expected_prefix']}")
            else:
                print(f"   ❌ Company ID prefix incorrect. Expected: {test_case['expected_prefix']}, Got: {company_id[:3]}")
                
        else:
            print(f"❌ Admin creation failed: {response.status_code}")
            print(f"Error: {response.text}")
    
    # Step 4: Verify admin list includes name field
    print(f"\n📋 Verifying admin list includes name field...")
    list_response = requests.get(f"{BASE_URL}/api/auth/list-admins/", headers=headers)
    
    if list_response.status_code == 200:
        admins = list_response.json()
        print(f"✅ Found {len(admins)} admins")
        
        for admin in admins[-len(test_cases):]:  # Show last created admins
            print(f"   👤 {admin.get('name', 'N/A')} | {admin.get('email', 'N/A')} | {admin.get('company_id', 'N/A')}")
    else:
        print(f"❌ Failed to get admin list: {list_response.status_code}")

if __name__ == "__main__":
    test_admin_creation_with_name()
