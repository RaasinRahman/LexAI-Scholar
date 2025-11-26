#!/usr/bin/env python3
"""
Test script for email-based workspace invitations
Run this after setting up the email column in profiles table
"""

import requests
import json
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"

def test_email_lookup(email: str) -> None:
    """Test that we can look up a user by email"""
    print(f"\n🔍 Testing email lookup for: {email}")
    
    # Note: This tests the internal logic
    # You'd need to expose a debug endpoint or check directly in database
    print("   This requires direct database access or a debug endpoint")
    print("   Check in Supabase SQL Editor:")
    print(f"   SELECT * FROM profiles WHERE email = '{email}';")

def test_invite_by_email(
    workspace_id: str,
    email: str,
    role: str,
    access_token: str
) -> None:
    """Test inviting a member by email"""
    print(f"\n📧 Testing invitation for: {email}")
    
    url = f"{API_BASE_URL}/workspaces/{workspace_id}/members/invite-by-email"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "email": email,
        "role": role
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ SUCCESS: Member invited!")
            print(f"   Response: {json.dumps(result, indent=2)}")
        else:
            error = response.json()
            print(f"   ❌ ERROR: {response.status_code}")
            print(f"   Details: {error.get('detail', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ EXCEPTION: {str(e)}")

def test_workspace_members(workspace_id: str, access_token: str) -> None:
    """List all members in a workspace"""
    print(f"\n👥 Fetching workspace members...")
    
    url = f"{API_BASE_URL}/workspaces/{workspace_id}/members"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            members = result.get("members", [])
            print(f"   ✅ Found {len(members)} members:")
            for member in members:
                profile = member.get("profiles", {})
                email = profile.get("email", "no-email")
                full_name = profile.get("full_name", "Unknown")
                role = member.get("role", "unknown")
                print(f"   - {full_name} ({email}) - {role}")
        else:
            print(f"   ❌ ERROR: {response.status_code}")
            print(f"   Details: {response.json().get('detail', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ EXCEPTION: {str(e)}")

def test_health_check() -> bool:
    """Test if the API is running"""
    print("\n🏥 Checking API health...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            result = response.json()
            print("   ✅ API is healthy!")
            print(f"   Status: {result.get('status')}")
            print(f"   Supabase configured: {result.get('supabase_configured')}")
            print(f"   Vector service configured: {result.get('vector_service_configured')}")
            return True
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot reach API: {str(e)}")
        print(f"   Make sure the backend is running on {API_BASE_URL}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("Email-Based Workspace Invitation Test Suite")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health_check():
        print("\n⚠️  Backend not running. Start with: python main.py")
        return
    
    print("\n" + "=" * 60)
    print("Manual Testing Required")
    print("=" * 60)
    
    print("\nTo test email-based invitations:")
    print("\n1. Sign in to your app and get your access token")
    print("2. Create a workspace and note its ID")
    print("3. Have a colleague create an account")
    print("4. Run this test:")
    
    print("\n   test_invite_by_email(")
    print("       workspace_id='your-workspace-uuid',")
    print("       email='colleague@example.com',")
    print("       role='viewer',")
    print("       access_token='your-access-token'")
    print("   )")
    
    print("\n" + "=" * 60)
    print("Database Verification Queries")
    print("=" * 60)
    
    print("\nRun these in Supabase SQL Editor:")
    print("\n-- Check if email column exists")
    print("SELECT column_name, data_type")
    print("FROM information_schema.columns")
    print("WHERE table_name = 'profiles' AND column_name = 'email';")
    
    print("\n-- Check if profiles have emails")
    print("SELECT id, email, full_name FROM profiles LIMIT 5;")
    
    print("\n-- Count profiles with emails")
    print("SELECT")
    print("    COUNT(*) as total,")
    print("    COUNT(email) as with_email,")
    print("    COUNT(*) - COUNT(email) as without_email")
    print("FROM profiles;")
    
    print("\n" + "=" * 60)
    print("Integration Test Example")
    print("=" * 60)
    
    print("\n# Example usage (replace with real values):")
    print("""
# Get your access token from browser localStorage after signing in
ACCESS_TOKEN = "your-jwt-token-here"
WORKSPACE_ID = "workspace-uuid-here"
TEST_EMAIL = "test@example.com"

# Test invitation
test_invite_by_email(
    workspace_id=WORKSPACE_ID,
    email=TEST_EMAIL,
    role="viewer",
    access_token=ACCESS_TOKEN
)

# Verify member was added
test_workspace_members(
    workspace_id=WORKSPACE_ID,
    access_token=ACCESS_TOKEN
)
""")

if __name__ == "__main__":
    main()






