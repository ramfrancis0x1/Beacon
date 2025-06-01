import requests
import json
import os

# Linear API configuration using environment variables
LINEAR_BASE_URL = "https://api.linear.app/graphql"
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")

# Check for required environment variable
if not LINEAR_API_KEY:
    print("❌ ERROR: LINEAR_API_KEY environment variable is required!")
    print("Set it with: export LINEAR_API_KEY='your_linear_oauth_token'")
    print("Get your OAuth token from Linear app -> Settings -> API")
    exit(1)

# Set up Linear headers based on token type
if LINEAR_API_KEY.startswith("lin_oauth_"):
    LINEAR_HEADERS = {
        "Authorization": f"Bearer {LINEAR_API_KEY}",
        "Content-Type": "application/json"
    }
elif LINEAR_API_KEY.startswith("lin_api_"):
    LINEAR_HEADERS = {
        "Authorization": LINEAR_API_KEY,
        "Content-Type": "application/json"
    }
else:
    LINEAR_HEADERS = {
        "Authorization": LINEAR_API_KEY,
        "Content-Type": "application/json"
    }

def get_recent_issues():
    """Get recent issues to verify the latest one has enhanced content"""
    print("🔍 Fetching recent Linear issues...")
    
    query = """
    query {
        issues(
            first: 5,
            orderBy: createdAt,
            filter: {
                team: {
                    key: {
                        eq: "BUE"
                    }
                }
            }
        ) {
            nodes {
                id
                identifier
                title
                description
                createdAt
                url
                state {
                    name
                }
            }
        }
    }
    """
    
    response = requests.post(
        LINEAR_BASE_URL,
        headers=LINEAR_HEADERS,
        json={"query": query}
    )
    
    if response.status_code == 200:
        data = response.json()
        issues = data["data"]["issues"]["nodes"]
        
        print(f"✅ Found {len(issues)} recent issues:")
        for issue in issues:
            print(f"   - {issue['identifier']}: {issue['title']}")
        
        return issues
    else:
        print(f"❌ Failed to fetch issues: {response.status_code}")
        return []

def analyze_issue_content(issue):
    """Analyze if an issue contains enhanced contact and attachment info"""
    description = issue.get('description', '')
    
    # Check for contact sections
    has_contacts = "## 👥 Contacts" in description
    has_primary_contact = "### Primary Contact" in description
    has_office_contact = "### Office Contact" in description
    has_contact_names = "Major Sarah Johnson" in description or "Technical Sergeant Mike Chen" in description
    
    # Check for attachments sections
    has_attachments = "## 📎 Attachments & Links" in description
    has_documents = "### Documents & Attachments" in description
    has_sow_attachment = "Statement of Work (SOW)" in description
    has_additional_links = "### Related Links" in description
    
    # Check for enhanced structure
    has_next_steps = "Contact primary POC for clarification" in description
    
    print(f"\n📋 Analyzing issue {issue['identifier']}: {issue['title']}")
    print(f"   Created: {issue['createdAt']}")
    print(f"   URL: {issue['url']}")
    
    print(f"\n📞 Contact Information:")
    print(f"   ✅ Has contacts section: {has_contacts}")
    print(f"   ✅ Has primary contact: {has_primary_contact}")
    print(f"   ✅ Has office contact: {has_office_contact}")
    print(f"   ✅ Has contact names: {has_contact_names}")
    
    print(f"\n📎 Attachments & Links:")
    print(f"   ✅ Has attachments section: {has_attachments}")
    print(f"   ✅ Has documents subsection: {has_documents}")
    print(f"   ✅ Has SOW attachment: {has_sow_attachment}")
    print(f"   ✅ Has additional links: {has_additional_links}")
    
    print(f"\n🔧 Enhanced Features:")
    print(f"   ✅ Has enhanced next steps: {has_next_steps}")
    
    # Overall assessment
    enhancement_score = sum([
        has_contacts, has_primary_contact, has_office_contact, has_contact_names,
        has_attachments, has_documents, has_sow_attachment, has_additional_links,
        has_next_steps
    ])
    
    print(f"\n🎯 Enhancement Score: {enhancement_score}/9")
    
    if enhancement_score >= 8:
        print(f"🎉 EXCELLENT! Issue has comprehensive contact and attachment information.")
    elif enhancement_score >= 6:
        print(f"✅ GOOD! Issue has most enhanced features.")
    else:
        print(f"⚠️  BASIC: Issue may be missing some enhanced features.")
    
    return enhancement_score

def main():
    print("🔍 Linear Issue Enhancement Verification")
    print("=" * 60)
    
    # Get recent issues
    issues = get_recent_issues()
    
    if not issues:
        print("❌ No issues found to analyze")
        return
    
    # Analyze the most recent issue (should be BUE-21)
    latest_issue = issues[0]
    score = analyze_issue_content(latest_issue)
    
    print(f"\n" + "=" * 60)
    if score >= 8:
        print("🎉 SUCCESS! The Linear integration now includes comprehensive contact")
        print("   and attachment information from SAM.gov listings!")
        print("\n💡 Your SAM.gov monitor will now create issues with:")
        print("   • Primary contact information (name, title, email, phone)")
        print("   • Office contact information")
        print("   • Additional points of contact")
        print("   • Document attachments with descriptions")
        print("   • Additional information links")
        print("   • Related resource links")
        print("   • Enhanced next steps with contact instructions")
    else:
        print("⚠️  The enhancement may not be fully working. Check the implementation.")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 