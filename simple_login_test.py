#!/usr/bin/env python3
"""Simple login test to debug the authentication issue"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("🔍 Testing Login API with different formats...\n")

# Test 1: Form data (like in your working quick_test.py)
print("Test 1: Form data format")
try:
    response = requests.post(f"{BASE_URL}/api/auth/login/", data={
        'username': 'superadmin',
        'password': 'superadmin123'
    })
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 200:
        print("✅ Form data login SUCCESS!")
    else:
        print("❌ Form data login FAILED!")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*50 + "\n")

# Test 2: JSON format with proper headers
print("Test 2: JSON format with Content-Type header")
try:
    headers = {'Content-Type': 'application/json'}
    data = {
        "username": "superadmin", 
        "password": "superadmin123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login/", 
                           headers=headers, 
                           data=json.dumps(data))
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 200:
        print("✅ JSON login SUCCESS!")
    else:
        print("❌ JSON login FAILED!")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*50 + "\n")

# Test 3: JSON format using requests.json parameter
print("Test 3: JSON format using requests.json parameter")
try:
    data = {
        "username": "superadmin", 
        "password": "superadmin123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login/", json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 200:
        print("✅ JSON (requests.json) login SUCCESS!")
    else:
        print("❌ JSON (requests.json) login FAILED!")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*50 + "\n")

# Check if server is running
print("Test 4: Server connectivity check")
try:
    response = requests.get(f"{BASE_URL}/")
    print(f"Server Status: {response.status_code}")
    print("✅ Server is running!")
except Exception as e:
    print(f"❌ Server connection error: {e}")
    print("Make sure Django server is running with: python manage.py runserver")

print("\n" + "="*50 + "\n")

# Check superadmin user exists (requires Django shell)
print("To verify superadmin user exists, run:")
print('python manage.py shell -c "from authentication.models import User; print(User.objects.filter(username=\'superadmin\').first())"')