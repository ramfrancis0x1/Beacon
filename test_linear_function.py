#!/usr/bin/env python3
"""
Standalone test for Linear issue creation function with AI-powered titles
"""

import requests
import json
import os
from datetime import datetime
import openai

# Linear API configuration using environment variables
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
LINEAR_BASE_URL = "https://api.linear.app/graphql"
LINEAR_TEAM_ID = os.getenv("LINEAR_TEAM_ID")

# Check for required environment variables
if not LINEAR_API_KEY:
    print("❌ ERROR: LINEAR_API_KEY environment variable is required!")
    print("Set it with: export LINEAR_API_KEY='your_linear_oauth_token'")
    print("Get your OAuth token from Linear app -> Settings -> API")
    exit(1)

if not LINEAR_TEAM_ID:
    print("❌ ERROR: LINEAR_TEAM_ID environment variable is required!")
    print("Set it with: export LINEAR_TEAM_ID='your_linear_team_id'")
    print("Find your team ID using the Linear API or from Linear app URLs")
    exit(1)

# Set up Linear headers based on token type
if LINEAR_API_KEY.startswith("lin_oauth_"):
    LINEAR_HEADERS = {
        "Authorization": f"Bearer {LINEAR_API_KEY}",
        "Content-Type": "application/json"
    }
    print("🔑 Using OAuth token authentication")
elif LINEAR_API_KEY.startswith("lin_api_"):
    LINEAR_HEADERS = {
        "Authorization": LINEAR_API_KEY,
        "Content-Type": "application/json"
    }
    print("🔑 Using Personal API key authentication")
else:
    LINEAR_HEADERS = {
        "Authorization": LINEAR_API_KEY,
        "Content-Type": "application/json"
    }
    print("⚠️  WARNING: Unknown API key format - trying direct authentication")

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    print("🤖 OpenAI integration: ENABLED - AI will generate better issue titles")
else:
    print("⚠️  OPENAI_API_KEY not set - using default titles")

def generate_ai_issue_title(listing):
    """
    Use OpenAI to generate a more fitting and actionable issue title
    based on the SAM.gov listing details
    """
    if not OPENAI_API_KEY:
        # Fallback to default title if OpenAI not configured
        title = listing.get('title', 'No title')
        return f"SAM.gov: {title[:80]}..." if len(title) > 80 else f"SAM.gov: {title}"
    
    try:
        # Extract key information from the listing
        title = listing.get('title', 'No title')
        notice_type = listing.get('type', 'Unknown type')
        naics = listing.get('naicsCode', 'Unknown NAICS')
        organization = listing.get('fullParentPathName', 'Unknown organization')
        set_aside = listing.get('typeOfSetAsideDescription', 'No set-aside info')
        response_deadline = listing.get('responseDeadLine', 'No deadline')
        
        # Create a prompt for OpenAI
        prompt = f"""
You are helping create actionable issue titles for a defense contracting company's project management system. 

Based on this SAM.gov opportunity, create a concise, actionable issue title that would be useful for a project manager:

Original Title: {title}
Notice Type: {notice_type}
NAICS Code: {naics}
Organization: {organization}
Set-Aside: {set_aside}
Response Deadline: {response_deadline}

The issue title should be:
- Clear and actionable (starts with a verb when possible)
- Specific to the opportunity type and industry
- Under 80 characters
- Professional but direct
- Focus on what action needs to be taken

Examples of good titles:
- "Evaluate Army 9mm Ammo RFP - 150k rounds - Due June 15"
- "Review USMC Rifle Team Equipment Sources Sought"
- "Assess Small Business Set-Aside for Navy Munitions"

Generate ONLY the title, no explanations or quotes:
"""

        # Call OpenAI API
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates concise, actionable project titles for defense contracting opportunities."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.3  # Lower temperature for more consistent results
        )
        
        ai_title = response.choices[0].message.content.strip()
        
        # Clean up the title (remove quotes if added)
        ai_title = ai_title.strip('"\'')
        
        # Ensure it's not too long
        if len(ai_title) > 80:
            ai_title = ai_title[:77] + "..."
        
        print(f"🤖 AI generated title: '{ai_title}'")
        return ai_title
        
    except Exception as e:
        print(f"⚠️  Failed to generate AI title: {e}")
        # Fallback to default title
        title = listing.get('title', 'No title')
        fallback_title = f"SAM.gov: {title[:80]}..." if len(title) > 80 else f"SAM.gov: {title}"
        print(f"📝 Using fallback title: '{fallback_title}'")
        return fallback_title

def create_linear_issue_for_listing(listing):
    """
    Create a Linear issue for a new SAM.gov listing with AI-generated title
    """
    try:
        # Extract listing information
        title = listing.get('title', 'No title')
        notice_type = listing.get('type', 'Unknown type')
        naics = listing.get('naicsCode', 'Unknown NAICS')
        posted_date = listing.get('postedDate', 'Unknown date')
        response_deadline = listing.get('responseDeadLine', 'No deadline')
        solicitation_number = listing.get('solicitationNumber', 'No solicitation number')
        organization = listing.get('fullParentPathName', 'Unknown organization')
        office_address = listing.get('officeAddress', {})
        place_of_performance = listing.get('placeOfPerformance', {})
        set_aside = listing.get('typeOfSetAsideDescription', 'No set-aside info')
        ui_link = listing.get('uiLink', 'No link available')
        uid = listing.get('noticeId') or listing.get('solicitationNumber')
        
        # Extract contact information
        contacts = listing.get('pointOfContact', [])
        primary_contact = listing.get('primaryContact', {})
        office_contact = listing.get('officeContact', {})
        
        # Extract attachments and additional links
        attachments = listing.get('attachments', [])
        additional_info_link = listing.get('additionalInfoLink', '')
        links = listing.get('links', [])
        
        # Format address info
        office_location = f"{office_address.get('city', 'Unknown')}, {office_address.get('state', 'Unknown')}"
        performance_location = "Unknown location"
        if place_of_performance:
            city_info = place_of_performance.get('city', {})
            state_info = place_of_performance.get('state', {})
            if isinstance(city_info, dict) and isinstance(state_info, dict):
                performance_location = f"{city_info.get('name', 'Unknown')}, {state_info.get('name', 'Unknown')}"
        
        # Format contact information
        contact_section = ""
        
        # Primary contact
        if primary_contact:
            contact_section += "### Primary Contact\n"
            if primary_contact.get('fullName'):
                contact_section += f"- **Name**: {primary_contact['fullName']}\n"
            if primary_contact.get('title'):
                contact_section += f"- **Title**: {primary_contact['title']}\n"
            if primary_contact.get('email'):
                contact_section += f"- **Email**: {primary_contact['email']}\n"
            if primary_contact.get('phone'):
                contact_section += f"- **Phone**: {primary_contact['phone']}\n"
            contact_section += "\n"
        
        # Office contact
        if office_contact:
            contact_section += "### Office Contact\n"
            if office_contact.get('fullName'):
                contact_section += f"- **Name**: {office_contact['fullName']}\n"
            if office_contact.get('title'):
                contact_section += f"- **Title**: {office_contact['title']}\n"
            if office_contact.get('email'):
                contact_section += f"- **Email**: {office_contact['email']}\n"
            if office_contact.get('phone'):
                contact_section += f"- **Phone**: {office_contact['phone']}\n"
            contact_section += "\n"
        
        # Additional contacts
        if contacts and isinstance(contacts, list):
            for i, contact in enumerate(contacts):
                if isinstance(contact, dict):
                    contact_section += f"### Contact {i+1}\n"
                    if contact.get('fullName'):
                        contact_section += f"- **Name**: {contact['fullName']}\n"
                    if contact.get('title'):
                        contact_section += f"- **Title**: {contact['title']}\n"
                    if contact.get('email'):
                        contact_section += f"- **Email**: {contact['email']}\n"
                    if contact.get('phone'):
                        contact_section += f"- **Phone**: {contact['phone']}\n"
                    contact_section += "\n"
        
        if not contact_section:
            contact_section = "No contact information available\n\n"
        
        # Format attachments and links
        attachments_section = ""
        
        # Attachments
        if attachments and isinstance(attachments, list):
            attachments_section += "### Documents & Attachments\n"
            for attachment in attachments:
                if isinstance(attachment, dict):
                    name = attachment.get('name', attachment.get('filename', 'Unnamed attachment'))
                    url = attachment.get('url', attachment.get('link', ''))
                    description = attachment.get('description', '')
                    
                    attachments_section += f"- **{name}**"
                    if description:
                        attachments_section += f" - {description}"
                    if url:
                        attachments_section += f"\n  - Link: {url}"
                    attachments_section += "\n"
            attachments_section += "\n"
        
        # Additional information link
        if additional_info_link:
            attachments_section += f"### Additional Information\n- {additional_info_link}\n\n"
        
        # Other links
        if links and isinstance(links, list):
            attachments_section += "### Related Links\n"
            for link in links:
                if isinstance(link, dict):
                    name = link.get('name', link.get('title', 'Link'))
                    url = link.get('url', link.get('href', ''))
                    if url:
                        attachments_section += f"- [{name}]({url})\n"
                elif isinstance(link, str):
                    attachments_section += f"- {link}\n"
            attachments_section += "\n"
        
        if not attachments_section:
            attachments_section = "No attachments or additional links available\n\n"
        
        # Create Linear issue title using AI
        print("🤖 Generating AI-powered issue title...")
        linear_title = generate_ai_issue_title(listing)
        
        # Create detailed description for Linear issue
        linear_description = f"""
# New SAM.gov Opportunity Found

## 📋 Basic Information
- **Title**: {title}
- **Solicitation Number**: {solicitation_number}
- **Notice Type**: {notice_type}
- **NAICS Code**: {naics}
- **Set-Aside**: {set_aside}
- **UID**: {uid}

## 📅 Important Dates
- **Posted Date**: {posted_date}
- **Response Deadline**: {response_deadline}

## 🏢 Organization & Location
- **Organization**: {organization}
- **Office Location**: {office_location}
- **Performance Location**: {performance_location}

## 👥 Contacts
{contact_section}

## 📎 Attachments & Links
{attachments_section}

## 🔗 SAM.gov Links
- **Opportunity Page**: {ui_link}

## 📝 Next Steps
- [ ] Review opportunity details
- [ ] Contact primary POC for clarification
- [ ] Assess capability match
- [ ] Determine bid/no-bid decision
- [ ] Prepare response if pursuing

**Detected by SAM.gov Monitor at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**
        """.strip()
        
        # Linear GraphQL mutation
        mutation = """
        mutation($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    url
                }
            }
        }
        """
        
        # Prepare input variables
        input_data = {
            "teamId": LINEAR_TEAM_ID,
            "title": linear_title,
            "description": linear_description,
            "priority": 3  # High priority for new opportunities
        }
        
        # Make the API request
        response = requests.post(
            LINEAR_BASE_URL,
            headers=LINEAR_HEADERS,
            json={
                "query": mutation,
                "variables": {"input": input_data}
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "errors" in data:
                print(f"Linear API GraphQL errors: {data['errors']}")
                return None
            
            result = data["data"]["issueCreate"]
            if result["success"]:
                issue = result["issue"]
                print(f"✅ Created Linear issue {issue['identifier']}: {issue['title']}")
                print(f"🔗 Linear issue URL: {issue['url']}")
                return issue
            else:
                print("Linear issue creation was not successful")
                return None
        else:
            print(f"Linear API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Failed to create Linear issue for listing: {e}")
        return None

def test_linear_integration():
    """Test the Linear integration with AI-powered titles using sample SAM.gov data"""
    
    print("🧪 Testing Linear Integration with AI-Powered Titles")
    print("=" * 60)
    
    # Sample SAM.gov listing data with realistic defense contracting content
    sample_listing = {
        "title": "Market Research - 5.56mm NATO Ammunition Manufacturing Capabilities for Special Operations Command",
        "type": "Sources Sought",
        "naicsCode": "332992",
        "postedDate": "2025-06-01",
        "responseDeadLine": "2025-06-20", 
        "solicitationNumber": "W91CRB-25-R-0001",
        "noticeId": "W91CRB25R0001-SS",
        "fullParentPathName": "Department of Defense > U.S. Special Operations Command > Special Operations Forces Acquisition",
        "typeOfSetAsideDescription": "Small Business Set-Aside",
        "uiLink": "https://sam.gov/test-opportunity-link",
        "officeAddress": {
            "city": "Tampa",
            "state": "FL"
        },
        "placeOfPerformance": {
            "city": {"name": "Multiple Locations"},
            "state": {"name": "CONUS"}
        },
        # Enhanced with contact information
        "primaryContact": {
            "fullName": "Major Sarah Johnson",
            "title": "Contracting Officer",
            "email": "sarah.johnson@socom.mil",
            "phone": "(813) 555-0123"
        },
        "officeContact": {
            "fullName": "Technical Sergeant Mike Chen",
            "title": "Contract Specialist",
            "email": "mike.chen@socom.mil",
            "phone": "(813) 555-0156"
        },
        "pointOfContact": [
            {
                "fullName": "Dr. Lisa Rodriguez",
                "title": "Technical Point of Contact",
                "email": "lisa.rodriguez@socom.mil",
                "phone": "(813) 555-0178"
            }
        ],
        # Enhanced with attachments and links
        "attachments": [
            {
                "name": "Statement of Work (SOW)",
                "description": "Detailed requirements for ammunition specifications",
                "url": "https://sam.gov/documents/sow-5.56mm-nato.pdf"
            },
            {
                "name": "Industry Day Presentation",
                "description": "Briefing slides from contractor information session",
                "url": "https://sam.gov/documents/industry-day-briefing.pdf"
            }
        ],
        "additionalInfoLink": "https://sam.gov/additional-info/W91CRB25R0001",
        "links": [
            {
                "name": "SOCOM Vendor Information",
                "url": "https://www.socom.mil/contracting"
            },
            {
                "name": "Security Clearance Requirements",
                "url": "https://www.dcsa.mil/is/ci/"
            }
        ]
    }
    
    print("📋 Sample Listing Data:")
    print(f"   Title: {sample_listing['title']}")
    print(f"   Type: {sample_listing['type']}")
    print(f"   NAICS: {sample_listing['naicsCode']}")
    print(f"   Solicitation: {sample_listing['solicitationNumber']}")
    print(f"   Organization: {sample_listing['fullParentPathName']}")
    print(f"   Deadline: {sample_listing['responseDeadLine']}")
    print()
    
    # Test the Linear issue creation with AI title
    print("🎯 Creating Linear issue with AI-generated title...")
    result = create_linear_issue_for_listing(sample_listing)
    
    if result:
        print("✅ SUCCESS! Linear issue created with AI-powered title:")
        print(f"   Issue ID: {result['identifier']}")
        print(f"   Title: {result['title']}")
        print(f"   URL: {result['url']}")
        print()
        print("🎉 Complete AI + Linear integration is working correctly!")
        print("   Your SAM.gov monitor will now create Linear issues with smart titles.")
    else:
        print("❌ FAILED! Linear issue was not created.")
        print("   Please check the error messages above.")
    
    print("=" * 60)

if __name__ == "__main__":
    test_linear_integration() 