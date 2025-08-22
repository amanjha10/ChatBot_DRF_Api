#!/usr/bin/env python
"""
Test script for the authentication system.
Run this after starting the Django server to test all endpoints.
"""

import requests
import json

BASE_URL = 'http://127.0.0.1:8000/api/auth'

def test_login():
    """Test login endpoint"""
    print("Testing login...")
    response = requests.post(f'{BASE_URL}/login/', {
        'username': 'superadmin',
        'password': 'admin123'  # Use the password you set
    })
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Login successful!")
        print(f"Role: {data['user']['role']}")
        return data['access']
    else:
        print("❌ Login failed!")
        print(response.json())
        return None

def test_create_admin(token):
    """Test create admin endpoint"""
    print("\nTesting create admin...")
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post(f'{BASE_URL}/create-admin/', {
        'username': 'admin1',
        'email': 'admin1@example.com',
        'first_name': 'Admin',
        'last_name': 'User',
        'password': 'admin123456',
        'password_confirm': 'admin123456',
        'role': 'ADMIN'
    }, headers=headers)
    
    if response.status_code == 201:
        print("✅ Admin created successfully!")
        print(response.json())
    else:
        print("❌ Admin creation failed!")
        print(response.json())

def test_profile(token):
    """Test profile endpoint"""
    print("\nTesting profile...")
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{BASE_URL}/profile/', headers=headers)
    
    if response.status_code == 200:
        print("✅ Profile retrieved successfully!")
        print(response.json())
    else:
        print("❌ Profile retrieval failed!")
        print(response.json())

if __name__ == '__main__':
    print("🚀 Starting authentication system tests...")
    print("Make sure the Django server is running on http://127.0.0.1:8000")
    print("-" * 50)
    
    # Test login
    token = test_login()
    
    if token:
        # Test profile
        test_profile(token)
        
        # Test create admin
        test_create_admin(token)
    
    print("\n" + "=" * 50)
    print("Tests completed!")
