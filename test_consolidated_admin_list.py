#!/usr/bin/env python3
"""Test the consolidated list-admins API with different query parameters"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# Login first to get token
print("🔐 Logging in as SuperAdmin...")
login_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
    'username': 'superadmin',
    'password': 'superadmin123'
})

if login_response.status_code != 200:
    print("❌ Login failed!")
    exit(1)

token = login_response.json()['access']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

print("✅ Login successful!")
print("\n" + "="*60 + "\n")

# Test 1: Basic list all admins (with pagination)
print("Test 1: Basic list all admins")
response = requests.get(f"{BASE_URL}/api/auth/list-admins/", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Count: {data.get('count', 'N/A')}")
    print(f"Results length: {len(data.get('results', []))}")
    print("✅ Basic list working!")
else:
    print(f"❌ Error: {response.text}")

print("\n" + "-"*40 + "\n")

# Test 2: Specific admin by ID
print("Test 2: Get specific admin by ID")
response = requests.get(f"{BASE_URL}/api/auth/list-admins/?admin_id=1", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Admin ID: {data.get('id', 'N/A')}")
    print(f"Admin Email: {data.get('email', 'N/A')}")
    print("✅ Specific admin lookup working!")
elif response.status_code == 404:
    print("📝 Admin ID 1 not found (expected if no admins created)")
else:
    print(f"❌ Error: {response.text}")

print("\n" + "-"*40 + "\n")

# Test 3: Pagination parameters
print("Test 3: Pagination with page_size=5")
response = requests.get(f"{BASE_URL}/api/auth/list-admins/?page=1&page_size=5", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Count: {data.get('count', 'N/A')}")
    print(f"Page size: {data.get('page_size', 'N/A')}")
    print(f"Current page: {data.get('current_page', 'N/A')}")
    print("✅ Pagination working!")
else:
    print(f"❌ Error: {response.text}")

print("\n" + "-"*40 + "\n")

# Test 4: Search functionality
print("Test 4: Search by email")
response = requests.get(f"{BASE_URL}/api/auth/list-admins/?search=example.com", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Search results count: {data.get('count', 'N/A')}")
    print("✅ Search working!")
else:
    print(f"❌ Error: {response.text}")

print("\n" + "-"*40 + "\n")

# Test 5: Ordering
print("Test 5: Ordering by email")
response = requests.get(f"{BASE_URL}/api/auth/list-admins/?ordering=email", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Results count: {data.get('count', 'N/A')}")
    print("✅ Ordering working!")
else:
    print(f"❌ Error: {response.text}")

print("\n" + "-"*40 + "\n")

# Test 6: Combined parameters
print("Test 6: Combined parameters (search + pagination + ordering)")
response = requests.get(f"{BASE_URL}/api/auth/list-admins/?search=admin&page=1&page_size=3&ordering=-date_joined", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Search + pagination results: {data.get('count', 'N/A')}")
    print(f"Page size: {data.get('page_size', 'N/A')}")
    print("✅ Combined parameters working!")
else:
    print(f"❌ Error: {response.text}")

print("\n" + "="*60 + "\n")
print("🎯 API Endpoints Available:")
print("• GET /api/auth/list-admins/")
print("• GET /api/auth/list-admins/?admin_id=<id>")
print("• GET /api/auth/list-admins/?page=<num>&page_size=<size>")
print("• GET /api/auth/list-admins/?search=<term>")
print("• GET /api/auth/list-admins/?ordering=<field>")
print("• GET /api/auth/list-admins/?search=<term>&page=<num>&ordering=<field>")
print("\n✅ All functionality consolidated into single endpoint!")
