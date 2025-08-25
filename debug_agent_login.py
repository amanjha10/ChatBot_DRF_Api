#!/usr/bin/env python3
"""Debug agent login response"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# First get superadmin token
print("Getting SuperAdmin token...")
superadmin_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
    'username': 'superadmin',
    'password': 'superadmin123'
})

if superadmin_response.status_code == 200:
    token = superadmin_response.json()['access']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get agents list
    agents_response = requests.get(f"{BASE_URL}/api/admin-dashboard/list-agents/", headers=headers)
    
    if agents_response.status_code == 200:
        agents = agents_response.json()
        
        if agents:
            agent = agents[0]
            agent_email = agent['email']
            
            # Get agent credentials
            debug_response = requests.get(f"{BASE_URL}/api/admin-dashboard/debug-agent/{agent['id']}/", headers=headers)
            
            if debug_response.status_code == 200:
                debug_data = debug_response.json()
                agent_password = debug_data.get('generated_password')
                
                print(f"Testing agent login with:")
                print(f"Email: {agent_email}")
                print(f"Password: {agent_password}")
                print()
                
                # Test agent login
                agent_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
                    'username': agent_email,
                    'password': agent_password
                })
                
                print(f"Status Code: {agent_response.status_code}")
                print("Response:")
                print(json.dumps(agent_response.json(), indent=2))
