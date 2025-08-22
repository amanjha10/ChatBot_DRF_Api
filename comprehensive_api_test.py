#!/usr/bin/env python3
"""
Comprehensive API Test Suite
Tests all authentication and admin dashboard APIs
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
AUTH_BASE = f"{BASE_URL}/api/auth"
ADMIN_BASE = f"{BASE_URL}/api/admin-dashboard"

class APITester:
    def __init__(self):
        self.token = None
        self.admin_token = None
        self.agent_token = None
        self.test_results = []
        self.created_resources = {
            'admins': [],
            'agents': [],
            'plans': []
        }

    def log_test(self, test_name, success, message="", response_data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"   {message}")
        if response_data and not success:
            print(f"   Response: {response_data}")
        print()
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })

    def test_server_health(self):
        """Test if server is running"""
        try:
            response = requests.get(f"{BASE_URL}/admin/", timeout=5)
            self.log_test("Server Health Check", True, f"Server responding (Status: {response.status_code})")
            return True
        except requests.exceptions.RequestException as e:
            self.log_test("Server Health Check", False, f"Server not accessible: {str(e)}")
            return False

    def test_superadmin_login(self):
        """Test SuperAdmin login"""
        try:
            response = requests.post(f"{AUTH_BASE}/login/", data={
                'username': 'superadmin',
                'password': 'superadmin123'
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['access']
                self.log_test("SuperAdmin Login", True, f"Role: {data['user']['role']}")
                return True
            else:
                self.log_test("SuperAdmin Login", False, f"Status: {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_test("SuperAdmin Login", False, f"Exception: {str(e)}")
            return False

    def test_profile_endpoint(self):
        """Test profile retrieval"""
        if not self.token:
            self.log_test("Profile Endpoint", False, "No token available")
            return False
            
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(f"{AUTH_BASE}/profile/", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Profile Endpoint", True, f"User: {data.get('username')}")
                return True
            else:
                self.log_test("Profile Endpoint", False, f"Status: {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_test("Profile Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_token_refresh(self):
        """Test token refresh"""
        if not self.token:
            self.log_test("Token Refresh", False, "No token available")
            return False
            
        try:
            # First get refresh token by logging in again
            login_response = requests.post(f"{AUTH_BASE}/login/", data={
                'username': 'superadmin',
                'password': 'superadmin123'
            })
            
            if login_response.status_code == 200:
                refresh_token = login_response.json()['refresh']
                
                response = requests.post(f"{AUTH_BASE}/token/refresh/", data={
                    'refresh': refresh_token
                })
                
                if response.status_code == 200:
                    self.log_test("Token Refresh", True, "Token refreshed successfully")
                    return True
                else:
                    self.log_test("Token Refresh", False, f"Status: {response.status_code}", response.json())
                    return False
            else:
                self.log_test("Token Refresh", False, "Could not get refresh token")
                return False
        except Exception as e:
            self.log_test("Token Refresh", False, f"Exception: {str(e)}")
            return False

    def test_create_plan(self):
        """Test plan creation"""
        if not self.token:
            self.log_test("Create Plan", False, "No token available")
            return False

        try:
            headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
            plan_data = {
                "plan_name": "basic",  # Must be one of: basic, pro, premium
                "max_agents": 5,
                "price": 99.99
            }

            response = requests.post(f"{AUTH_BASE}/create-plan/",
                                   headers=headers,
                                   data=json.dumps(plan_data))

            if response.status_code == 201:
                data = response.json()
                self.created_resources['plans'].append(data['id'])
                self.log_test("Create Plan", True, f"Plan ID: {data['id']}")
                return True
            else:
                self.log_test("Create Plan", False, f"Status: {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_test("Create Plan", False, f"Exception: {str(e)}")
            return False

    def test_list_plans(self):
        """Test listing plans"""
        if not self.token:
            self.log_test("List Plans", False, "No token available")
            return False
            
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(f"{AUTH_BASE}/list-plans/", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("List Plans", True, f"Found {len(data)} plans")
                return True
            else:
                self.log_test("List Plans", False, f"Status: {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_test("List Plans", False, f"Exception: {str(e)}")
            return False

    def test_create_admin(self):
        """Test admin creation"""
        if not self.token:
            self.log_test("Create Admin", False, "No token available")
            return False
            
        try:
            # Get available plans first
            headers = {'Authorization': f'Bearer {self.token}'}
            plans_response = requests.get(f"{AUTH_BASE}/list-plans/", headers=headers)
            
            if plans_response.status_code != 200:
                self.log_test("Create Admin", False, "Could not fetch plans")
                return False
                
            plans = plans_response.json()
            if not plans:
                self.log_test("Create Admin", False, "No plans available")
                return False
                
            plan_id = plans[0]['id']
            
            headers['Content-Type'] = 'application/json'
            admin_data = {
                "name": f"Test Company {datetime.now().strftime('%H%M%S')}",
                "email": f"test_admin_{datetime.now().strftime('%H%M%S')}@example.com",
                "address": "123 Test Street",
                "contact_person": "Test Person",
                "contact_number": "123-456-7890",
                "phone_number": "098-765-4321",
                "plan_id": plan_id
            }
            
            response = requests.post(f"{AUTH_BASE}/create-admin/", 
                                   headers=headers, 
                                   data=json.dumps(admin_data))
            
            if response.status_code == 201:
                data = response.json()
                admin_id = data.get('id') or data.get('user_id')  # Handle different response formats
                if admin_id:
                    self.created_resources['admins'].append(admin_id)
                self.log_test("Create Admin", True, f"Admin ID: {admin_id}, Company ID: {data.get('company_id')}")
                return True
            else:
                self.log_test("Create Admin", False, f"Status: {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_test("Create Admin", False, f"Exception: {str(e)}")
            return False

    def test_list_admins(self):
        """Test listing admins"""
        if not self.token:
            self.log_test("List Admins", False, "No token available")
            return False
            
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(f"{AUTH_BASE}/list-admins/", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("List Admins", True, f"Found {len(data)} admins")
                return True
            else:
                self.log_test("List Admins", False, f"Status: {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_test("List Admins", False, f"Exception: {str(e)}")
            return False

    def test_list_admins_paginated(self):
        """Test paginated admin listing"""
        if not self.token:
            self.log_test("List Admins Paginated", False, "No token available")
            return False
            
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(f"{AUTH_BASE}/list-admins-paginated/?page_size=5", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("List Admins Paginated", True, f"Found {data.get('count')} admins, Page {data.get('current_page')}/{data.get('total_pages')}")
                return True
            else:
                self.log_test("List Admins Paginated", False, f"Status: {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_test("List Admins Paginated", False, f"Exception: {str(e)}")
            return False

    def test_create_agent(self):
        """Test agent creation"""
        if not self.token:
            self.log_test("Create Agent", False, "No token available")
            return False

        try:
            headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
            agent_data = {
                "name": f"Test Agent {datetime.now().strftime('%H%M%S')}",
                "email": f"agent_{datetime.now().strftime('%H%M%S')}@example.com",
                "phone": "123-456-7890",  # Correct field name
                "specialization": "Customer Support"  # Required field
            }

            response = requests.post(f"{ADMIN_BASE}/create-agent/",
                                   headers=headers,
                                   data=json.dumps(agent_data))

            if response.status_code == 201:
                data = response.json()
                agent_id = data['agent']['id']
                self.created_resources['agents'].append(agent_id)
                self.log_test("Create Agent", True, f"Agent ID: {agent_id}")
                return True
            else:
                self.log_test("Create Agent", False, f"Status: {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_test("Create Agent", False, f"Exception: {str(e)}")
            return False

    def test_list_agents(self):
        """Test listing agents"""
        if not self.token:
            self.log_test("List Agents", False, "No token available")
            return False

        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(f"{ADMIN_BASE}/list-agents/", headers=headers)

            if response.status_code == 200:
                data = response.json()
                self.log_test("List Agents", True, f"Found {len(data)} agents")
                return True
            else:
                self.log_test("List Agents", False, f"Status: {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_test("List Agents", False, f"Exception: {str(e)}")
            return False

    def test_agent_first_login(self):
        """Test agent first login password setup"""
        if not self.created_resources['agents']:
            self.log_test("Agent First Login", False, "No agents created to test with")
            return False

        try:
            # Get agent details first
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(f"{ADMIN_BASE}/list-agents/", headers=headers)

            if response.status_code != 200:
                self.log_test("Agent First Login", False, "Could not fetch agents")
                return False

            agents = response.json()
            if not agents:
                self.log_test("Agent First Login", False, "No agents available")
                return False

            # Use the first agent for first login
            agent = agents[0]
            first_login_response = requests.post(f"{ADMIN_BASE}/agent-first-login/", data={
                'email': agent['email'],
                'current_password': agent.get('generated_password', ''),
                'new_password': 'NewPassword123',
                'confirm_password': 'NewPassword123'
            })

            if first_login_response.status_code == 200:
                self.log_test("Agent First Login", True, f"Password set for: {agent['email']}")
                return True
            else:
                self.log_test("Agent First Login", False, f"Status: {first_login_response.status_code}", first_login_response.json())
                return False
        except Exception as e:
            self.log_test("Agent First Login", False, f"Exception: {str(e)}")
            return False

    def test_agent_login(self):
        """Test agent login after password setup"""
        if not self.created_resources['agents']:
            self.log_test("Agent Login", False, "No agents created to test with")
            return False

        try:
            # Get agent details first
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(f"{ADMIN_BASE}/list-agents/", headers=headers)

            if response.status_code != 200:
                self.log_test("Agent Login", False, "Could not fetch agents")
                return False

            agents = response.json()
            if not agents:
                self.log_test("Agent Login", False, "No agents available")
                return False

            # Try to login with the first agent using the new password
            agent = agents[0]
            login_response = requests.post(f"{ADMIN_BASE}/agent-login/", data={
                'email': agent['email'],
                'password': 'NewPassword123'  # Use the password set in first login
            })

            if login_response.status_code == 200:
                data = login_response.json()
                self.agent_token = data['access']
                self.log_test("Agent Login", True, f"Agent: {agent['email']}")
                return True
            else:
                self.log_test("Agent Login", False, f"Status: {login_response.status_code}", login_response.json())
                return False
        except Exception as e:
            self.log_test("Agent Login", False, f"Exception: {str(e)}")
            return False

    def run_authentication_tests(self):
        """Run all authentication-related tests"""
        print("🔐 AUTHENTICATION API TESTS")
        print("=" * 50)

        if not self.test_server_health():
            return False

        if not self.test_superadmin_login():
            return False

        self.test_profile_endpoint()
        self.test_token_refresh()
        self.test_create_plan()
        self.test_list_plans()
        self.test_create_admin()
        self.test_list_admins()
        self.test_list_admins_paginated()
        self.test_list_admins_paginated()

        return True

    def run_admin_dashboard_tests(self):
        """Run all admin dashboard tests"""
        print("\n🏢 ADMIN DASHBOARD API TESTS")
        print("=" * 50)

        self.test_create_agent()
        self.test_list_agents()
        self.test_agent_first_login()
        self.test_agent_login()

        return True

    def run_all_tests(self):
        """Run all tests"""
        print(f"🚀 COMPREHENSIVE API TEST SUITE")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run authentication tests
        auth_success = self.run_authentication_tests()

        # Run admin dashboard tests
        admin_success = self.run_admin_dashboard_tests()

        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "No tests run")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        return passed == total

if __name__ == '__main__':
    tester = APITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
