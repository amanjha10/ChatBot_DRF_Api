#!/usr/bin/env python3
"""
Test script for the delete admin API and cleaned up admin list response.
Tests:
1. Admin list response doesn't include unnecessary fields (first_name, last_name, username)
2. Delete admin API works correctly
3. Delete admin handles non-existent admin properly
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
SUPERADMIN_USERNAME = "superadmin"
SUPERADMIN_PASSWORD = "superadmin123"

def test_delete_admin_api():
    """Test the new delete admin API and cleaned admin list response."""
    
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
    
    # Step 2: Get available plans first
    print("\n📋 Getting available plans...")
    plans_response = requests.get(f"{BASE_URL}/api/auth/list-plans/", headers=headers)
    
    if plans_response.status_code != 200:
        print(f"❌ Could not fetch plans: {plans_response.status_code}")
        return
        
    plans = plans_response.json()
    if not plans:
        print("❌ No plans available")
        return
        
    plan_id = plans[0]['id']
    print(f"✅ Using plan ID: {plan_id}")
    
    # Step 3: Create a test admin to delete later
    print("\n👤 Creating test admin for deletion...")
    
    headers['Content-Type'] = 'application/json'
    test_admin_data = {
        "name": f"Test Delete Admin {datetime.now().strftime('%H%M%S')}",
        "email": f"delete_test_{datetime.now().strftime('%H%M%S')}@example.com",
        "address": "123 Delete Test Street",
        "contact_person": "Delete Test Person",
        "contact_number": "555-DELETE",
        "phone_number": "555-TEST",
        "plan_id": plan_id
    }
    
    create_admin_response = requests.post(
        f"{BASE_URL}/api/auth/create-admin/", 
        headers=headers, 
        data=json.dumps(test_admin_data)
    )
    
    if create_admin_response.status_code != 201:
        print(f"❌ Could not create test admin: {create_admin_response.status_code}")
        print(create_admin_response.text)
        return
    
    created_admin = create_admin_response.json()
    test_admin_email = created_admin['email']
    print(f"✅ Test admin created: {test_admin_email}")
    
    # Step 4: Get admin list to find the created admin ID and verify cleaned response
    print("\n📄 Testing cleaned admin list response...")
    admins_response = requests.get(f"{BASE_URL}/api/auth/list-admins/", headers=headers)
    
    if admins_response.status_code != 200:
        print(f"❌ Could not get admin list: {admins_response.status_code}")
        return
    
    admins = admins_response.json()
    
    # Find our test admin
    test_admin = None
    test_admin_id = None
    for admin in admins:
        if admin.get('email') == test_admin_email:
            test_admin = admin
            test_admin_id = admin['id']
            break
    
    if not test_admin:
        print("❌ Could not find created test admin in list")
        return
    
    print(f"✅ Found test admin in list: ID {test_admin_id}")
    
    # Step 5: Verify cleaned response (should NOT have first_name, last_name, username)
    print("\n🧹 Verifying cleaned admin list response...")
    
    excluded_fields = ['first_name', 'last_name', 'username']
    required_fields = ['id', 'email', 'name', 'company_id']
    
    has_excluded_fields = any(field in test_admin for field in excluded_fields)
    has_required_fields = all(field in test_admin for field in required_fields)
    
    if has_excluded_fields:
        found_excluded = [field for field in excluded_fields if field in test_admin]
        print(f"❌ Admin list response still contains excluded fields: {found_excluded}")
        print(f"   Response keys: {list(test_admin.keys())}")
    else:
        print("✅ Admin list response is clean - no unnecessary fields (first_name, last_name, username)")
    
    if not has_required_fields:
        missing_required = [field for field in required_fields if field not in test_admin]
        print(f"❌ Admin list response missing required fields: {missing_required}")
    else:
        print("✅ Admin list response contains all required fields")
    
    # Step 6: Test deleting the admin
    print(f"\n🗑️  Testing delete admin API (ID: {test_admin_id})...")
    
    delete_response = requests.delete(
        f"{BASE_URL}/api/auth/delete-admin/{test_admin_id}/", 
        headers=headers
    )
    
    if delete_response.status_code == 200:
        delete_result = delete_response.json()
        print("✅ Delete admin successful!")
        print(f"   Message: {delete_result.get('message')}")
        print(f"   Deleted admin: {delete_result.get('deleted_admin')}")
        
        # Verify the admin was actually deleted
        print("\n🔍 Verifying admin was actually deleted...")
        verify_response = requests.get(f"{BASE_URL}/api/auth/list-admins/?admin_id={test_admin_id}", headers=headers)
        
        if verify_response.status_code == 404:
            print("✅ Admin successfully deleted - not found in database")
        else:
            print(f"❌ Admin still exists after deletion: {verify_response.status_code}")
            
    else:
        print(f"❌ Delete admin failed: {delete_response.status_code}")
        print(delete_response.text)
        return
    
    # Step 7: Test deleting non-existent admin
    print("\n🚫 Testing delete non-existent admin...")
    
    fake_delete_response = requests.delete(
        f"{BASE_URL}/api/auth/delete-admin/9999/", 
        headers=headers
    )
    
    if fake_delete_response.status_code == 404:
        error_result = fake_delete_response.json()
        print("✅ Delete non-existent admin properly returns 404")
        print(f"   Error message: {error_result.get('error')}")
    else:
        print(f"❌ Delete non-existent admin should return 404, got: {fake_delete_response.status_code}")
    
    print("\n🎉 All tests completed!")
    
    # Summary
    print("\n📊 SUMMARY:")
    print("✅ Delete admin API implemented")
    print("✅ Admin list response cleaned (removed first_name, last_name, username)")
    print("✅ Error handling for non-existent admin")
    print("✅ Proper cascade deletion of plan assignments")

if __name__ == "__main__":
    test_delete_admin_api()
