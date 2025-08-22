#!/usr/bin/env python3
"""Quick test of the updated admin creation API"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# Login as SuperAdmin
login_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
    'username': 'superadmin',
    'password': 'superadmin123'
})

if login_response.status_code == 200:
    token = login_response.json()['access']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Get plans
    plans_response = requests.get(f"{BASE_URL}/api/auth/list-plans/", headers=headers)
    plan_id = plans_response.json()[0]['id']
    
    # Create admin with name
    admin_data = {
        "name": "Tesla Motors",
        "email": "admin_final_test@tesla.com",
        "address": "123 Tesla St",
        "contact_person": "Elon Musk", 
        "contact_number": "123-456-7890",
        "phone_number": "098-765-4321",
        "plan_id": plan_id
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/create-admin/", headers=headers, data=json.dumps(admin_data))
    
    if response.status_code == 201:
        result = response.json()
        print("✅ SUCCESS! Admin Creation with Name Field Working!")
        print(f"📛 Name: {result.get('name')}")
        print(f"📧 Email: {result.get('email')}")
        print(f"🔑 Password: {result.get('password')}")
        print(f"🆔 Company ID: {result.get('company_id')}")
        
        # Verify company ID prefix
        company_id = result.get('company_id', '')
        if company_id.startswith('TES'):
            print("✅ Company ID generation from NAME working correctly!")
        else:
            print(f"❌ Company ID issue: {company_id}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
else:
    print("❌ Login failed")
