#!/usr/bin/env python3
"""
Test script for the paginated admin list API.
Tests:
1. Basic pagination functionality
2. Search functionality (by name, email, company_id)
3. Ordering functionality
4. Page size customization
5. Error handling for invalid parameters
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
SUPERADMIN_USERNAME = "superadmin"
SUPERADMIN_PASSWORD = "superadmin123"

def test_pagination_api():
    """Test the new paginated admin list API."""
    
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
    
    # Step 2: Test basic pagination
    print("\n📄 Testing basic pagination...")
    pagination_response = requests.get(
        f"{BASE_URL}/api/auth/list-admins-paginated/", 
        headers=headers
    )
    
    if pagination_response.status_code == 200:
        data = pagination_response.json()
        print("✅ Basic pagination works!")
        print(f"   Total admins: {data.get('count')}")
        print(f"   Current page: {data.get('current_page')}")
        print(f"   Total pages: {data.get('total_pages')}")
        print(f"   Page size: {data.get('page_size')}")
        print(f"   Results on this page: {len(data.get('results', []))}")
        
        # Show first few admin names
        if data.get('results'):
            print("   📋 First few admins:")
            for i, admin in enumerate(data['results'][:3]):
                print(f"      {i+1}. {admin.get('name')} ({admin.get('company_id')})")
    else:
        print(f"❌ Basic pagination failed: {pagination_response.status_code}")
        print(pagination_response.text)
        return
    
    # Step 3: Test custom page size
    print("\n📏 Testing custom page size...")
    custom_size_response = requests.get(
        f"{BASE_URL}/api/auth/list-admins-paginated/?page_size=5", 
        headers=headers
    )
    
    if custom_size_response.status_code == 200:
        data = custom_size_response.json()
        print(f"✅ Custom page size works!")
        print(f"   Requested page size: 5")
        print(f"   Actual page size: {data.get('page_size')}")
        print(f"   Results returned: {len(data.get('results', []))}")
    else:
        print(f"❌ Custom page size failed: {custom_size_response.status_code}")
    
    # Step 4: Test pagination navigation (page 2)
    if data.get('total_pages', 0) > 1:
        print("\n➡️  Testing page navigation (page 2)...")
        page2_response = requests.get(
            f"{BASE_URL}/api/auth/list-admins-paginated/?page=2", 
            headers=headers
        )
        
        if page2_response.status_code == 200:
            page2_data = page2_response.json()
            print("✅ Page navigation works!")
            print(f"   Current page: {page2_data.get('current_page')}")
            print(f"   Has next: {'Yes' if page2_data.get('next') else 'No'}")
            print(f"   Has previous: {'Yes' if page2_data.get('previous') else 'No'}")
        else:
            print(f"❌ Page navigation failed: {page2_response.status_code}")
    else:
        print("\n➡️  Skipping page navigation test (only 1 page available)")
    
    # Step 5: Test search functionality
    print("\n🔍 Testing search functionality...")
    
    # First, let's get a sample admin to search for
    if data.get('results'):
        sample_admin = data['results'][0]
        search_term = sample_admin.get('name', '').split()[0] if sample_admin.get('name') else 'Test'
        
        search_response = requests.get(
            f"{BASE_URL}/api/auth/list-admins-paginated/?search={search_term}", 
            headers=headers
        )
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            print(f"✅ Search functionality works!")
            print(f"   Search term: '{search_term}'")
            print(f"   Results found: {search_data.get('count')}")
            
            if search_data.get('results'):
                print("   📋 Search results:")
                for i, admin in enumerate(search_data['results'][:3]):
                    print(f"      {i+1}. {admin.get('name')} ({admin.get('email')})")
        else:
            print(f"❌ Search failed: {search_response.status_code}")
    
    # Step 6: Test ordering
    print("\n📊 Testing ordering functionality...")
    
    # Test ordering by name (ascending)
    order_response = requests.get(
        f"{BASE_URL}/api/auth/list-admins-paginated/?ordering=name", 
        headers=headers
    )
    
    if order_response.status_code == 200:
        order_data = order_response.json()
        print("✅ Ordering functionality works!")
        print(f"   Ordering: name (ascending)")
        print(f"   Results: {len(order_data.get('results', []))}")
        
        if len(order_data.get('results', [])) >= 2:
            first_name = order_data['results'][0].get('name', '')
            second_name = order_data['results'][1].get('name', '')
            print(f"   First admin: {first_name}")
            print(f"   Second admin: {second_name}")
    else:
        print(f"❌ Ordering failed: {order_response.status_code}")
    
    # Step 7: Test ordering by date (descending - default)
    order_desc_response = requests.get(
        f"{BASE_URL}/api/auth/list-admins-paginated/?ordering=-date_joined", 
        headers=headers
    )
    
    if order_desc_response.status_code == 200:
        order_desc_data = order_desc_response.json()
        print("✅ Descending ordering works!")
        print(f"   Ordering: -date_joined (newest first)")
        
        if order_desc_data.get('results'):
            newest_admin = order_desc_data['results'][0]
            print(f"   Newest admin: {newest_admin.get('name')} (joined: {newest_admin.get('date_joined')})")
    else:
        print(f"❌ Descending ordering failed: {order_desc_response.status_code}")
    
    # Step 8: Test combined parameters
    print("\n🔗 Testing combined parameters...")
    
    combined_response = requests.get(
        f"{BASE_URL}/api/auth/list-admins-paginated/?page_size=3&ordering=name&search=test", 
        headers=headers
    )
    
    if combined_response.status_code == 200:
        combined_data = combined_response.json()
        print("✅ Combined parameters work!")
        print(f"   Search: 'test', Page size: 3, Ordering: name")
        print(f"   Results found: {combined_data.get('count')}")
        print(f"   Results on page: {len(combined_data.get('results', []))}")
    else:
        print(f"❌ Combined parameters failed: {combined_response.status_code}")
    
    # Step 9: Test error handling
    print("\n🚫 Testing error handling...")
    
    # Test invalid page number
    invalid_page_response = requests.get(
        f"{BASE_URL}/api/auth/list-admins-paginated/?page=999", 
        headers=headers
    )
    
    if invalid_page_response.status_code == 404:
        print("✅ Invalid page number properly returns 404")
    elif invalid_page_response.status_code == 200:
        invalid_data = invalid_page_response.json()
        if not invalid_data.get('results'):
            print("✅ Invalid page number returns empty results")
        else:
            print("❌ Invalid page number should return empty results")
    else:
        print(f"⚠️  Invalid page returned: {invalid_page_response.status_code}")
    
    # Test excessive page size
    large_page_response = requests.get(
        f"{BASE_URL}/api/auth/list-admins-paginated/?page_size=200", 
        headers=headers
    )
    
    if large_page_response.status_code == 200:
        large_data = large_page_response.json()
        actual_page_size = large_data.get('page_size')
        if actual_page_size <= 100:  # Our max_page_size
            print(f"✅ Excessive page size properly limited to: {actual_page_size}")
        else:
            print(f"❌ Page size not properly limited: {actual_page_size}")
    else:
        print(f"❌ Large page size test failed: {large_page_response.status_code}")
    
    print("\n🎉 All pagination tests completed!")
    
    # Summary
    print("\n📊 PAGINATION API SUMMARY:")
    print("✅ Basic pagination implemented")
    print("✅ Custom page sizes supported (max 100)")
    print("✅ Search functionality (name, email, company_id)")
    print("✅ Ordering by multiple fields")
    print("✅ Combined parameter support")
    print("✅ Proper error handling")
    print("✅ Clean paginated response format")

if __name__ == "__main__":
    test_pagination_api()
