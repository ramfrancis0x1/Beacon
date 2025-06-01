import requests 
import os
import time
import logging
import json
from datetime import datetime, timedelta 
import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sam_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
naics_codes = ['332992']  # Add more NAICS codes here if needed
target_notice_types = ['Sources Sought', 'Request for Information', 'RFI', 'Sources Sought Synopsis']
CHECK_INTERVAL_MINUTES = 60  # How often to check for new listings (in minutes)
LOOKBACK_DAYS = 90  # How many days back to search

# SAM.gov API configuration
api_key = os.getenv("API_KEY")
url = os.getenv("API_URL")

# Linear API configuration
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
LINEAR_BASE_URL = "https://api.linear.app/graphql"
LINEAR_TEAM_ID = os.getenv("LINEAR_TEAM_ID")  # Bueller team ID
LINEAR_HEADERS = {
    "Authorization": f"Bearer {LINEAR_API_KEY}" if LINEAR_API_KEY else "",
    "Content-Type": "application/json"
}

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    logger.info("🤖 OpenAI integration: ENABLED - AI will generate better issue titles")
else:
    logger.warning("⚠️  OPENAI_API_KEY not set - using default titles")

# Check if environment variables are set
if not api_key:
    logger.error("API_KEY environment variable is not set!")
    logger.error("Please set it with: export API_KEY='your_actual_api_key'")
    exit(1)

if not url:
    logger.error("API_URL environment variable is not set!")
    logger.error("Please set it with: export API_URL='https://your-actual-api-endpoint.com'")
    exit(1)

if not LINEAR_API_KEY:
    logger.error("LINEAR_API_KEY environment variable is not set!")
    logger.error("Please set it with: export LINEAR_API_KEY='your_linear_api_key'")
    exit(1)

if not LINEAR_TEAM_ID:
    logger.error("LINEAR_TEAM_ID environment variable is not set!")
    logger.error("Please set it with: export LINEAR_TEAM_ID='your_linear_team_id'")
    exit(1)

# In-memory storage
existing_ids = set()
items_list = [] 

def fetch_listing_details(listing):
    """
    Fetch detailed information for a listing using the description URL
    """
    description_url = listing.get('description')
    if not description_url:
        return "No detailed description available"
    
    try:
        # Add API key to the description URL
        if '?' in description_url:
            detail_url = f"{description_url}&api_key={api_key}"
        else:
            detail_url = f"{description_url}?api_key={api_key}"
        
        response = requests.get(detail_url)
        if response.status_code == 200:
            detail_data = response.json()
            return detail_data.get('description', 'No description found')
        else:
            logger.warning(f"Failed to fetch details. Status: {response.status_code}")
            return "Failed to fetch detailed description"
    except Exception as e:
        logger.warning(f"Error fetching listing details: {e}")
        return "Error fetching detailed description"

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
        
        logger.info(f"🤖 AI generated title: '{ai_title}'")
        return ai_title
        
    except Exception as e:
        logger.warning(f"⚠️  Failed to generate AI title: {e}")
        # Fallback to default title
        title = listing.get('title', 'No title')
        fallback_title = f"SAM.gov: {title[:80]}..." if len(title) > 80 else f"SAM.gov: {title}"
        logger.info(f"📝 Using fallback title: '{fallback_title}'")
        return fallback_title

def create_linear_issue_for_listing(listing):
    """
    Create a Linear issue for a new SAM.gov listing
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
        
        # Format address info
        office_location = f"{office_address.get('city', 'Unknown')}, {office_address.get('state', 'Unknown')}"
        performance_location = "Unknown location"
        if place_of_performance:
            city_info = place_of_performance.get('city', {})
            state_info = place_of_performance.get('state', {})
            if isinstance(city_info, dict) and isinstance(state_info, dict):
                performance_location = f"{city_info.get('name', 'Unknown')}, {state_info.get('name', 'Unknown')}"
        
        # Create Linear issue title using AI
        logger.info("🤖 Generating AI-powered issue title...")
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

## 🔗 Links
- **SAM.gov Link**: {ui_link}

## 📝 Next Steps
- [ ] Review opportunity details
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
                logger.error(f"Linear API GraphQL errors: {data['errors']}")
                return None
            
            result = data["data"]["issueCreate"]
            if result["success"]:
                issue = result["issue"]
                logger.info(f"✅ Created Linear issue {issue['identifier']}: {issue['title']}")
                logger.info(f"🔗 Linear issue URL: {issue['url']}")
                return issue
            else:
                logger.error("Linear issue creation was not successful")
                return None
        else:
            logger.error(f"Linear API request failed with status {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to create Linear issue for listing: {e}")
        return None

def check_and_add_listings(new_listings):
    """
    Check new listings against existing IDs and add only new ones.
    Returns a list of newly added listings.
    """
    global existing_ids, items_list
    
    newly_added = []
    
    for listing in new_listings:
        # Get the unique identifier (prefer noticeId, fallback to solicitationNumber)
        uid = listing.get('noticeId') or listing.get('solicitationNumber')
        
        if uid and uid not in existing_ids:
            # This is a new listing
            existing_ids.add(uid)
            items_list.append(listing)
            newly_added.append(listing)
            
            # Get basic listing info
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
            
            # Format address info
            office_location = f"{office_address.get('city', 'Unknown')}, {office_address.get('state', 'Unknown')}"
            performance_location = "Unknown location"
            if place_of_performance:
                city_info = place_of_performance.get('city', {})
                state_info = place_of_performance.get('state', {})
                if isinstance(city_info, dict) and isinstance(state_info, dict):
                    performance_location = f"{city_info.get('name', 'Unknown')}, {state_info.get('name', 'Unknown')}"
            
            # Fetch detailed description
            logger.info("Fetching detailed listing information...")
            detailed_description = fetch_listing_details(listing)
            
            # Log comprehensive new listing information
            logger.info("=" * 80)
            logger.info("🆕 NEW LISTING FOUND!")
            logger.info("=" * 80)
            logger.info(f"📋 BASIC INFORMATION:")
            logger.info(f"   Title: {title}")
            logger.info(f"   Solicitation Number: {solicitation_number}")
            logger.info(f"   Notice Type: {notice_type}")
            logger.info(f"   NAICS Code: {naics}")
            logger.info(f"   Set-Aside: {set_aside}")
            logger.info(f"   UID: {uid}")
            logger.info("")
            logger.info(f"📅 IMPORTANT DATES:")
            logger.info(f"   Posted Date: {posted_date}")
            logger.info(f"   Response Deadline: {response_deadline}")
            logger.info("")
            logger.info(f"🏢 ORGANIZATION & LOCATION:")
            logger.info(f"   Organization: {organization}")
            logger.info(f"   Office Location: {office_location}")
            logger.info(f"   Performance Location: {performance_location}")
            logger.info("")
            logger.info(f"🔗 LINKS:")
            logger.info(f"   SAM.gov Link: {ui_link}")
            logger.info("")
            logger.info(f"📝 DETAILED DESCRIPTION:")
            logger.info(f"{detailed_description}")
            logger.info("=" * 80)
            
            # Create Linear issue for this new listing
            logger.info("🎯 Creating Linear issue for new opportunity...")
            linear_issue = create_linear_issue_for_listing(listing)
            if linear_issue:
                logger.info(f"📋 Linear issue created successfully: {linear_issue['identifier']}")
            else:
                logger.warning("⚠️  Failed to create Linear issue, but continuing with monitoring...")
            logger.info("=" * 80)
            
        elif uid:
            logger.debug(f"Already seen: {listing.get('title', 'No title')} (ID: {uid})")
        else:
            logger.warning(f"Listing has no UID: {listing.get('title', 'No title')}")
    
    return newly_added

def fetch_new_listings(naics_codes):
    global existing_ids, items_list
    all_opportunities = []
    
    # Calculate search window
    end_time = datetime.now()
    start_time = end_time - timedelta(days=LOOKBACK_DAYS)
    
    # Search for each NAICS code separately
    for naics_code in naics_codes:
        logger.debug(f"Searching for NAICS code: {naics_code}")
        
        params = {
            "api_key": api_key,
            "postedFrom": start_time.strftime("%m/%d/%Y"),
            "postedTo": end_time.strftime("%m/%d/%Y"),
            "limit": 1000,
            "naics": naics_code,
            "ptype": "r"  # r = Sources Sought
        }
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f'API request failed for NAICS {naics_code}. Status: {response.status_code}')
                logger.error(f"Response: {response.text}")
                continue
                
            data = response.json()
            opportunities = data.get('opportunitiesData', [])
            logger.debug(f"API returned {len(opportunities)} opportunities for NAICS {naics_code}")
            
            # Filter to ensure only the specified NAICS codes and notice types are included
            filtered_opportunities = []
            for opp in opportunities:
                opp_naics = opp.get('naicsCode', '')
                notice_type = opp.get('type', '').strip() if opp.get('type') else ''
                
                # Check NAICS code match
                naics_match = False
                if opp_naics:
                    naics_match = any(target_naics in str(opp_naics) for target_naics in naics_codes)
                
                # Check notice type match (case-insensitive)
                notice_type_match = any(target_type.lower() in notice_type.lower() for target_type in target_notice_types) if notice_type else False
                
                if naics_match and notice_type_match:
                    filtered_opportunities.append(opp)
                    
            logger.debug(f"Found {len(filtered_opportunities)} matching opportunities for NAICS {naics_code}")
            all_opportunities.extend(filtered_opportunities)
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for NAICS {naics_code}: {e}")
            continue
        except Exception as e:
            logger.error(f"Error occurred for NAICS {naics_code}: {e}")
            continue
    
    # Remove duplicates based on opportunity ID
    unique_opportunities = {}
    for opp in all_opportunities:
        opp_id = opp.get('noticeId', opp.get('solicitationNumber', ''))
        if opp_id and opp_id not in unique_opportunities:
            unique_opportunities[opp_id] = opp
    
    return list(unique_opportunities.values())

def monitor_continuously():
    """
    Main monitoring loop that runs continuously
    """
    logger.info("🚀 Starting SAM.gov Sources Sought Monitor")
    logger.info(f"Target NAICS codes: {naics_codes}")
    logger.info(f"Check interval: {CHECK_INTERVAL_MINUTES} minutes")
    logger.info(f"Lookback period: {LOOKBACK_DAYS} days")
    logger.info(f"Currently tracking {len(existing_ids)} existing listings")
    if LINEAR_API_KEY and LINEAR_TEAM_ID:
        logger.info("\U0001F517 Linear integration: ENABLED - New opportunities will create Linear issues")
    else:
        logger.info("⚠️ Linear integration: DISABLED - Linear API key or Team ID not configured")
    logger.info("=" * 60)
    
    while True:
        try:
            logger.info(f"🔍 Starting scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Fetch all matching listings from API
            all_listings = fetch_new_listings(naics_codes)
            
            # Check and add only new listings
            new_listings = check_and_add_listings(all_listings)
            
            # Log summary
            logger.info(f"📊 Scan complete:")
            logger.info(f"   Total matching opportunities: {len(all_listings)}")
            logger.info(f"   New listings found: {len(new_listings)}")
            logger.info(f"   Total in database: {len(items_list)}")
            logger.info(f"   Next scan in {CHECK_INTERVAL_MINUTES} minutes")
            
            if len(new_listings) == 0:
                logger.info("✅ No new listings found")
            
            logger.info("-" * 60)
            
            # Wait for next check
            time.sleep(CHECK_INTERVAL_MINUTES * 60)
            
        except KeyboardInterrupt:
            logger.info("🛑 Monitor stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Unexpected error in monitoring loop: {e}")
            logger.info(f"⏳ Waiting {CHECK_INTERVAL_MINUTES} minutes before retry...")
            time.sleep(CHECK_INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    monitor_continuously()

