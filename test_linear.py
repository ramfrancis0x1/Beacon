import requests
import json
import os
import pytest
from datetime import datetime
import time

class LinearAPITest:
    """Test class for Linear API operations"""
    
    def __init__(self, api_key=None):
        # Linear API configuration using environment variables
        self.api_key = api_key or os.getenv("LINEAR_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "LINEAR_API_KEY environment variable is required!\n"
                "Set it with: export LINEAR_API_KEY='your_linear_api_key'\n"
                "Get your API key from Linear app -> Settings -> API"
            )
        
        self.base_url = "https://api.linear.app/graphql"
        
        # Determine authentication header format based on token type
        if self.api_key.startswith("lin_oauth_"):
            # OAuth tokens use Bearer format
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            print(f"🔑 Using OAuth token authentication")
        elif self.api_key.startswith("lin_api_"):
            # Personal API keys use direct format
            self.headers = {
                "Authorization": self.api_key,
                "Content-Type": "application/json"
            }
            print(f"🔑 Using Personal API key authentication")
        else:
            # Unknown format - try direct format
            self.headers = {
                "Authorization": self.api_key,
                "Content-Type": "application/json"
            }
            print("⚠️  WARNING: Unknown API key format - trying direct authentication")
            print("   Valid Linear API keys typically start with 'lin_api_' or 'lin_oauth_'")
            print("   To get a valid API key:")
            print("   1. Go to Linear app -> Settings -> API")
            print("   2. Create a new Personal API key")
            print("   3. Copy the key and use it in this test")
            print()
    
    def test_authentication(self):
        """Test Linear API authentication"""
        print("🔐 Testing Linear API authentication...")
        
        query = """
        query {
            viewer {
                id
                name
                email
            }
        }
        """
        
        response = requests.post(
            self.base_url,
            headers=self.headers,
            json={"query": query}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response body: {response.text}")
        
        if response.status_code != 200:
            print(f"❌ Authentication failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        data = response.json()
        
        if "errors" in data:
            print(f"❌ GraphQL errors: {data['errors']}")
            return None
            
        if "data" not in data or "viewer" not in data["data"]:
            print(f"❌ Unexpected response structure: {data}")
            return None
        
        viewer = data["data"]["viewer"]
        print(f"✅ Authentication successful!")
        print(f"   User ID: {viewer.get('id', 'N/A')}")
        print(f"   Name: {viewer.get('name', 'N/A')}")
        print(f"   Email: {viewer.get('email', 'N/A')}")
        
        return viewer
    
    def get_teams(self):
        """Get available teams"""
        print("🏢 Fetching available teams...")
        
        query = """
        query {
            teams {
                nodes {
                    id
                    name
                    key
                }
            }
        }
        """
        
        response = requests.post(
            self.base_url,
            headers=self.headers,
            json={"query": query}
        )
        
        assert response.status_code == 200, f"Failed to fetch teams with status {response.status_code}"
        
        data = response.json()
        teams = data["data"]["teams"]["nodes"]
        
        print(f"✅ Found {len(teams)} teams:")
        for team in teams:
            print(f"   - {team['name']} (Key: {team['key']}, ID: {team['id']})")
        
        return teams
    
    def get_team_states(self, team_id):
        """Get workflow states for a team"""
        print(f"📋 Fetching workflow states for team {team_id}...")
        
        query = """
        query($teamId: String!) {
            team(id: $teamId) {
                states {
                    nodes {
                        id
                        name
                        type
                    }
                }
            }
        }
        """
        
        response = requests.post(
            self.base_url,
            headers=self.headers,
            json={
                "query": query,
                "variables": {"teamId": team_id}
            }
        )
        
        assert response.status_code == 200, f"Failed to fetch states with status {response.status_code}"
        
        data = response.json()
        states = data["data"]["team"]["states"]["nodes"]
        
        print(f"✅ Found {len(states)} workflow states:")
        for state in states:
            print(f"   - {state['name']} (Type: {state['type']}, ID: {state['id']})")
        
        return states
    
    def create_issue(self, team_id, title, description=None, priority=None):
        """Create a new Linear issue"""
        print(f"🎯 Creating Linear issue: '{title}'...")
        
        # Build the mutation
        mutation = """
        mutation($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    description
                    url
                    createdAt
                    state {
                        name
                    }
                    team {
                        name
                    }
                    priority
                }
            }
        }
        """
        
        # Prepare input variables
        input_data = {
            "teamId": team_id,
            "title": title
        }
        
        if description:
            input_data["description"] = description
        
        if priority:
            input_data["priority"] = priority
        
        response = requests.post(
            self.base_url,
            headers=self.headers,
            json={
                "query": mutation,
                "variables": {"input": input_data}
            }
        )
        
        assert response.status_code == 200, f"Failed to create issue with status {response.status_code}"
        
        data = response.json()
        
        # Check for GraphQL errors
        if "errors" in data:
            error_messages = [error["message"] for error in data["errors"]]
            raise Exception(f"GraphQL errors: {', '.join(error_messages)}")
        
        result = data["data"]["issueCreate"]
        assert result["success"], "Issue creation was not successful"
        
        issue = result["issue"]
        print(f"✅ Issue created successfully!")
        print(f"   ID: {issue['id']}")
        print(f"   Identifier: {issue['identifier']}")
        print(f"   Title: {issue['title']}")
        print(f"   Description: {issue.get('description', 'No description')}")
        print(f"   URL: {issue['url']}")
        print(f"   Team: {issue['team']['name']}")
        print(f"   State: {issue['state']['name']}")
        print(f"   Priority: {issue.get('priority', 'No priority set')}")
        print(f"   Created: {issue['createdAt']}")
        
        return issue
    
    def get_issue(self, issue_id):
        """Retrieve an issue by ID"""
        print(f"🔍 Fetching issue {issue_id}...")
        
        query = """
        query($id: String!) {
            issue(id: $id) {
                id
                identifier
                title
                description
                url
                createdAt
                updatedAt
                state {
                    name
                }
                team {
                    name
                }
                priority
                assignee {
                    name
                    email
                }
            }
        }
        """
        
        response = requests.post(
            self.base_url,
            headers=self.headers,
            json={
                "query": query,
                "variables": {"id": issue_id}
            }
        )
        
        assert response.status_code == 200, f"Failed to fetch issue with status {response.status_code}"
        
        data = response.json()
        issue = data["data"]["issue"]
        
        print(f"✅ Issue retrieved successfully!")
        print(f"   Identifier: {issue['identifier']}")
        print(f"   Title: {issue['title']}")
        print(f"   State: {issue['state']['name']}")
        
        return issue
    
    def run_comprehensive_test(self):
        """Run a comprehensive test of Linear API functionality"""
        print("🚀 Starting comprehensive Linear API test...")
        print("=" * 60)
        
        try:
            # Test 1: Authentication
            viewer = self.test_authentication()
            print()
            
            if not viewer:
                print("❌ Authentication failed. Cannot proceed with other tests.")
                print("Please check:")
                print("1. API key is valid and not expired")
                print("2. API key has proper permissions")
                print("3. Linear API endpoint is accessible")
                return None
            
            # Test 2: Get teams
            teams = self.get_teams()
            print()
            
            if not teams:
                print("❌ No teams found. Cannot proceed with issue creation.")
                return
            
            # Use the first available team
            selected_team = teams[0]
            print(f"📌 Selected team: {selected_team['name']} (ID: {selected_team['id']})")
            print()
            
            # Test 3: Get team states
            states = self.get_team_states(selected_team['id'])
            print()
            
            # Test 4: Create a test issue
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            issue_title = f"Test Issue - Linear API Test {timestamp}"
            issue_description = f"""
This is a test issue created by the Linear API test suite.

**Test Details:**
- Created at: {timestamp}
- API Key: {self.api_key[:8]}...
- Team: {selected_team['name']}
- Purpose: Verify Linear API integration

**Test Objectives:**
✅ Authentication
✅ Team retrieval
✅ Workflow state retrieval
✅ Issue creation
⏳ Issue retrieval (in progress)

This issue can be safely closed or deleted after verification.
            """.strip()
            
            created_issue = self.create_issue(
                team_id=selected_team['id'],
                title=issue_title,
                description=issue_description,
                priority=2  # Normal priority
            )
            print()
            
            # Test 5: Retrieve the created issue
            retrieved_issue = self.get_issue(created_issue['id'])
            print()
            
            # Verify the issue was created correctly
            assert retrieved_issue['id'] == created_issue['id'], "Issue IDs don't match"
            assert retrieved_issue['title'] == issue_title, "Issue titles don't match"
            
            print("🎉 All tests passed successfully!")
            print("=" * 60)
            print(f"📋 Created issue: {created_issue['identifier']}")
            print(f"🔗 Issue URL: {created_issue['url']}")
            print("=" * 60)
            
            return created_issue
            
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
            raise


def test_linear_api():
    """Main test function that can be run with pytest"""
    linear_test = LinearAPITest()
    return linear_test.run_comprehensive_test()


if __name__ == "__main__":
    # Run the test directly
    print("Linear API Test Suite")
    print("=" * 60)
    
    try:
        linear_test = LinearAPITest()
        created_issue = linear_test.run_comprehensive_test()
        
        print("\n🎯 Test Summary:")
        print(f"✅ Linear API integration working correctly")
        print(f"✅ Issue created: {created_issue['identifier']}")
        print(f"✅ All API endpoints tested successfully")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        exit(1)
