#!/usr/bin/env python3
"""
Test script for the updated list-admins API with admin_id query parameter.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"
SUPERADMIN_USERNAME = "superadmin"
SUPERADMIN_PASSWORD = "superadmin123"

def test_list_admins_with_query_param():
    """Test the updated list-admins API with admin_id query parameter."""
    
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
    headers = {'Authorization': f'Bearer {token}'}
    print("✅ Login successful!")
    
    # Step 2: Test getting all admins (without query parameter)
    print("\n📋 Testing: Get all admins (no query parameter)")
    all_admins_response = requests.get(f"{BASE_URL}/api/auth/list-admins/", headers=headers)
    
    if all_admins_response.status_code == 200:
        all_admins = all_admins_response.json()
        print(f"✅ Success! Found {len(all_admins)} admins")
        
        if len(all_admins) > 0:
            # Show first few admins
            print("📄 Admin List (first 3):")
            for i, admin in enumerate(all_admins[:3]):
                print(f"   {i+1}. ID: {admin.get('id')}, Name: {admin.get('name', 'N/A')}, Email: {admin.get('email')}")
            
            # Step 3: Test getting specific admin by ID
            test_admin_id = all_admins[0]['id']
            print(f"\n🎯 Testing: Get specific admin (ID: {test_admin_id})")
            
            specific_admin_response = requests.get(
                f"{BASE_URL}/api/auth/list-admins/?admin_id={test_admin_id}", 
                headers=headers
            )
            
            if specific_admin_response.status_code == 200:
                specific_admin = specific_admin_response.json()
                print("✅ Success! Got specific admin:")
                print(f"   📛 Name: {specific_admin.get('name', 'N/A')}")
                print(f"   📧 Email: {specific_admin.get('email')}")
                print(f"   🆔 ID: {specific_admin.get('id')}")
                print(f"   🏢 Company ID: {specific_admin.get('company_id', 'N/A')}")
                
                # Verify it's not an array
                if isinstance(specific_admin, dict):
                    print("✅ Response is a single object (not array)")
                else:
                    print("❌ Response should be a single object, not array")
            else:
                print(f"❌ Failed to get specific admin: {specific_admin_response.status_code}")
                print(specific_admin_response.text)
        else:
            print("ℹ️  No admins found to test with")
    else:
        print(f"❌ Failed to get all admins: {all_admins_response.status_code}")
        print(all_admins_response.text)
        return
    
    # Step 4: Test error cases
    print(f"\n🧪 Testing error cases...")
    
    # Test invalid admin_id (non-numeric)
    print("Testing invalid admin_id (non-numeric):")
    invalid_response1 = requests.get(f"{BASE_URL}/api/auth/list-admins/?admin_id=abc", headers=headers)
    if invalid_response1.status_code == 400:
        print("✅ Correctly returned 400 for non-numeric admin_id")
    else:
        print(f"❌ Expected 400, got {invalid_response1.status_code}")
    
    # Test non-existent admin_id
    print("Testing non-existent admin_id (9999):")
    invalid_response2 = requests.get(f"{BASE_URL}/api/auth/list-admins/?admin_id=9999", headers=headers)
    if invalid_response2.status_code == 404:
        print("✅ Correctly returned 404 for non-existent admin_id")
    else:
        print(f"❌ Expected 404, got {invalid_response2.status_code}")
    
    print(f"\n🎉 API testing completed!")

if __name__ == "__main__":
    test_list_admins_with_query_param()
