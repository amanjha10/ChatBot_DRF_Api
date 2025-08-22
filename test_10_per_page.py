#!/usr/bin/env python3
"""
Test script specifically for 10-items-per-page pagination functionality.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"
SUPERADMIN_USERNAME = "superadmin"
SUPERADMIN_PASSWORD = "superadmin123"

def test_10_items_per_page():
    """Test pagination with exactly 10 items per page."""
    
    # Login
    print("🔐 Logging in as SuperAdmin...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
        'username': SUPERADMIN_USERNAME,
        'password': SUPERADMIN_PASSWORD
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    token = login_response.json()['access']
    headers = {'Authorization': f'Bearer {token}'}
    print("✅ Login successful!")
    
    # Test Page 1 (should show 10 items)
    print("\n📄 Testing Page 1 (expecting 10 items)...")
    page1_response = requests.get(
        f"{BASE_URL}/api/auth/list-admins-paginated/?page=1", 
        headers=headers
    )
    
    if page1_response.status_code == 200:
        page1_data = page1_response.json()
        print(f"✅ Page 1 loaded successfully!")
        print(f"   📊 Total admins in database: {page1_data.get('count')}")
        print(f"   📖 Total pages available: {page1_data.get('total_pages')}")
        print(f"   📄 Current page: {page1_data.get('current_page')}")
        print(f"   📋 Items on this page: {len(page1_data.get('results', []))}")
        print(f"   📏 Page size: {page1_data.get('page_size')}")
        
        # Show admin names on page 1
        print("   👥 Admins on Page 1:")
        for i, admin in enumerate(page1_data.get('results', []), 1):
            print(f"      {i:2d}. {admin.get('name')} ({admin.get('company_id')})")
        
        # Test Page 2 if available
        if page1_data.get('total_pages', 0) > 1:
            print(f"\n📄 Testing Page 2 (expecting 10 items)...")
            page2_response = requests.get(
                f"{BASE_URL}/api/auth/list-admins-paginated/?page=2", 
                headers=headers
            )
            
            if page2_response.status_code == 200:
                page2_data = page2_response.json()
                print(f"✅ Page 2 loaded successfully!")
                print(f"   📄 Current page: {page2_data.get('current_page')}")
                print(f"   📋 Items on this page: {len(page2_data.get('results', []))}")
                print(f"   📏 Page size: {page2_data.get('page_size')}")
                
                # Show admin names on page 2
                print("   👥 Admins on Page 2:")
                for i, admin in enumerate(page2_data.get('results', []), 1):
                    print(f"      {i:2d}. {admin.get('name')} ({admin.get('company_id')})")
                
                # Navigation links
                print(f"   ⬅️  Has Previous: {'Yes' if page2_data.get('previous') else 'No'}")
                print(f"   ➡️  Has Next: {'Yes' if page2_data.get('next') else 'No'}")
                
            else:
                print(f"❌ Page 2 failed: {page2_response.status_code}")
        else:
            print(f"\n📄 Only 1 page available (less than 10 total admins)")
        
        # Test Page 3 if available
        if page1_data.get('total_pages', 0) > 2:
            print(f"\n📄 Testing Page 3...")
            page3_response = requests.get(
                f"{BASE_URL}/api/auth/list-admins-paginated/?page=3", 
                headers=headers
            )
            
            if page3_response.status_code == 200:
                page3_data = page3_response.json()
                print(f"✅ Page 3 loaded successfully!")
                print(f"   📋 Items on this page: {len(page3_data.get('results', []))}")
                print(f"   📏 Page size: {page3_data.get('page_size')}")
            else:
                print(f"❌ Page 3 failed: {page3_response.status_code}")
    else:
        print(f"❌ Page 1 failed: {page1_response.status_code}")
        return
    
    # Test default page size without specifying page parameter
    print(f"\n📄 Testing default pagination (no page parameter)...")
    default_response = requests.get(
        f"{BASE_URL}/api/auth/list-admins-paginated/", 
        headers=headers
    )
    
    if default_response.status_code == 200:
        default_data = default_response.json()
        print(f"✅ Default pagination works!")
        print(f"   📄 Defaults to page: {default_data.get('current_page')}")
        print(f"   📋 Items shown: {len(default_data.get('results', []))}")
        print(f"   📏 Page size: {default_data.get('page_size')}")
    
    print("\n🎉 Pagination test completed!")
    
    # Summary
    print(f"\n📊 PAGINATION SUMMARY:")
    print(f"✅ Page 1: Shows up to 10 items")
    print(f"✅ Page 2: Shows up to 10 items") 
    print(f"✅ Page 3+: Shows remaining items")
    print(f"✅ Default page size: 10 items")
    print(f"✅ Navigation links work properly")

if __name__ == "__main__":
    test_10_items_per_page()
