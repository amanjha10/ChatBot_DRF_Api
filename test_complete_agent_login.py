#!/usr/bin/env python3
"""Complete agent first login and test unified login"""

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
                
                print(f"Found agent: {agent_email}")
                print(f"Temp password: {agent_password}")
                print()
                
                # Complete first login
                print("Completing first login...")
                first_login_response = requests.post(f"{BASE_URL}/api/admin-dashboard/agent-first-login/", data={
                    'email': agent_email,
                    'current_password': agent_password,
                    'new_password': 'newpassword123',
                    'confirm_password': 'newpassword123'
                })
                
                print(f"First login status: {first_login_response.status_code}")
                
                if first_login_response.status_code == 200:
                    print("✅ First login completed successfully!")
                    print()
                    
                    # Now test unified login with new password
                    print("Testing unified login with new password...")
                    unified_login_response = requests.post(f"{BASE_URL}/api/auth/login/", data={
                        'username': agent_email,
                        'password': 'newpassword123'
                    })
                    
                    print(f"Unified login status: {unified_login_response.status_code}")
                    print("Response:")
                    print(json.dumps(unified_login_response.json(), indent=2))
                    
                    if unified_login_response.status_code == 200:
                        response_data = unified_login_response.json()
                        if 'agent' in response_data:
                            print("\n✅ UNIFIED LOGIN SUCCESS!")
                            print("Agent-specific data found in response:")
                            print(f"- Agent ID: {response_data['agent']['id']}")
                            print(f"- Agent Status: {response_data['agent']['status']}")  
                            print(f"- First Login: {response_data['agent']['is_first_login']}")
                            print(f"- Company ID: {response_data['agent'].get('company_id')}")
                        else:
                            print("\n❌ Missing agent data in response")
                    
                else:
                    print(f"❌ First login failed: {first_login_response.text}")
                    
            else:
                print("❌ Could not get agent debug info")
        else:
            print("❌ No agents found")
    else:
        print(f"❌ Could not get agents: {agents_response.text}")
else:
    print("❌ Could not login as superadmin")
