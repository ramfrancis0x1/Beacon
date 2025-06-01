# SAM.gov Defense Contracting Monitor

A comprehensive Python script that automatically monitors SAM.gov for new defense contracting opportunities and creates actionable Linear issues with AI-generated titles.

## 🎯 Overview

This tool continuously scans SAM.gov for Sources Sought notices, RFIs, and other opportunities in specific NAICS codes (primarily defense-related manufacturing), then automatically creates detailed Linear issues with:

- **AI-powered issue titles** using OpenAI GPT-3.5-turbo
- **Complete contact information** (primary contacts, office contacts, technical POCs)
- **Document attachments and links** (SOWs, specifications, vendor information)
- **Comprehensive opportunity details** (deadlines, locations, set-aside status)
- **Actionable next steps** with contact guidance

## ✨ Key Features

### 🤖 **AI-Powered Title Generation**
- Uses OpenAI to create actionable, professional issue titles
- Transforms generic titles like "Market Research - Ammunition" into "Analyze 5.56mm NATO Ammo Mfg Capabilities - SOCOM"
- Fallback to standard titles if OpenAI is unavailable

### 👥 **Comprehensive Contact Extraction**
- **Primary Contact**: Contracting officers with full contact details
- **Office Contact**: Contract specialists and administrative contacts  
- **Technical POCs**: Subject matter experts and technical contacts
- **Complete Info**: Names, titles, emails, phone numbers

### 📎 **Document & Link Management**
- **Attachments**: SOWs, specifications, industry day presentations
- **Additional Links**: Vendor portals, security clearance requirements
- **Resource Links**: Organization-specific contracting information

### 🔄 **Intelligent Monitoring**
- Configurable scan intervals (default: 60 minutes)
- Duplicate detection to avoid repeat notifications
- Comprehensive logging to `sam_monitor.log`
- Automatic retry on API failures

## 🚀 Quick Start

### Prerequisites

```bash
# Install required packages
pip install requests openai pytest

# Or use requirements.txt
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Required: SAM.gov API Access
export API_KEY="your_sam_gov_api_key"
export API_URL="https://api.sam.gov/opportunities/v2/search"

# Required: Linear Integration
export LINEAR_API_KEY="lin_oauth_your_linear_oauth_token"
export LINEAR_TEAM_ID="your_linear_team_id"

# Optional: AI-Powered Titles (Recommended)
export OPENAI_API_KEY="sk-your_openai_api_key"
```

**Quick Setup:**
```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your actual API keys
nano .env

# Source the environment variables
source .env
```

**Getting API Keys:**
- **SAM.gov**: Register at [sam.gov](https://sam.gov) and request API access
- **Linear**: Go to Linear app → Settings → API → Create OAuth Token  
- **OpenAI**: Sign up at [platform.openai.com](https://platform.openai.com) and generate an API key

### Running the Monitor

```bash
# Start continuous monitoring
python main.py

# The script will run indefinitely, checking every 60 minutes
# Press Ctrl+C to stop
```

## 📋 Configuration

### NAICS Codes
Currently monitoring `332992` (Small Arms Ammunition Manufacturing). Add more codes in `main.py`:

```python
naics_codes = ['332992', '336411', '334511']  # Add your target NAICS codes
```

### Notice Types
Monitoring these opportunity types:

```python
target_notice_types = ['Sources Sought', 'Request for Information', 'RFI', 'Sources Sought Synopsis']
```

### Timing Configuration

```python
CHECK_INTERVAL_MINUTES = 60  # How often to check (minutes)
LOOKBACK_DAYS = 90          # How far back to search (days)
```

## 🔗 API Integrations

### SAM.gov API
- **Purpose**: Fetch defense contracting opportunities
- **Authentication**: API key required
- **Rate Limits**: Respects SAM.gov API guidelines
- **Data**: Comprehensive opportunity details including contacts and attachments

### Linear API  
- **Purpose**: Create project management issues
- **Authentication**: OAuth token (recommended) or Personal API key
- **Features**: Rich markdown descriptions, priority settings, team assignment
- **GraphQL**: Uses Linear's GraphQL API for robust integration

### OpenAI API
- **Purpose**: Generate intelligent, actionable issue titles
- **Model**: GPT-3.5-turbo for cost-effectiveness
- **Fallback**: Graceful degradation to standard titles if unavailable
- **Prompt Engineering**: Optimized for defense contracting context

## 📊 Sample Output

When a new opportunity is found:

```
🆕 NEW LISTING FOUND!
================================================================================
📋 BASIC INFORMATION:
   Title: Market Research - 5.56mm NATO Ammunition Manufacturing Capabilities
   Solicitation Number: W91CRB-25-R-0001
   Notice Type: Sources Sought
   NAICS Code: 332992
   Set-Aside: Small Business Set-Aside

📅 IMPORTANT DATES:
   Posted Date: 2025-06-01
   Response Deadline: 2025-06-20

🏢 ORGANIZATION & LOCATION:
   Organization: Department of Defense > U.S. Special Operations Command
   Office Location: Tampa, FL

👥 CONTACTS:
   Primary Contact: Major Sarah Johnson (sarah.johnson@socom.mil)
   Office Contact: Technical Sergeant Mike Chen (mike.chen@socom.mil)

🎯 Creating Linear issue for new opportunity...
🤖 AI generated title: 'Analyze 5.56mm NATO Ammo Mfg Capabilities - SOCOM'
✅ Created Linear issue BUE-21: Analyze 5.56mm NATO Ammo Mfg Capabilities - SOCOM
🔗 Linear issue URL: https://linear.app/bueller/issue/BUE-21/...
```

## 📁 Project Structure

```
leader-sam/
├── main.py                    # Main monitoring script
├── test_linear.py            # Linear API test suite
├── test_linear_function.py   # Standalone Linear integration test
├── verify_enhanced_issue.py  # Issue content verification
├── run_tests.sh              # Complete test runner script
├── env.example               # Environment variables template
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── sam_monitor.log          # Runtime logs (auto-generated)
└── README.md               # This file
```

## 🧪 Testing & Validation

### 🚀 Quick Test (Recommended)
```bash
# Run complete test suite in the correct order
./run_tests.sh
```
**This automated script:**
- ✅ Validates environment variables
- ✅ Runs all tests in dependency order
- ✅ Stops on first failure with helpful error messages
- ✅ Provides comprehensive success summary
- ✅ Offers optional full integration test

### 🔧 Manual Testing (When Debugging)

When making changes, run tests in this **specific order**:

#### **1. Basic Linear API Test**
```bash
python test_linear.py
```
**What it tests:**
- Linear API authentication and connectivity
- Team discovery and access permissions
- Workflow state retrieval
- Basic issue creation and retrieval
- API response handling and error detection

**Expected output:**
```
✅ Authentication successful!
✅ Found 1 teams: Bueller (Key: BUE)
✅ Issue created successfully! (BUE-XX)
🎉 All tests passed successfully!
```

**Must pass first** - other tests depend on this connectivity.

#### **2. Enhanced Function Test**
```bash
python test_linear_function.py
```
**What it tests:**
- Enhanced issue creation with contacts/attachments
- AI-powered title generation (if OpenAI configured)
- Complete SAM.gov data extraction and formatting
- Rich markdown description generation
- Contact information parsing and display

**Expected output:**
```
🤖 AI generated title: 'Analyze 5.56mm NATO Ammo Capabilities - SOCOM'
✅ Created Linear issue BUE-XX with AI-powered title
🎉 Complete AI + Linear integration working correctly!
```

#### **3. Content Verification Test**
```bash
python verify_enhanced_issue.py
```
**What it tests:**
- Issue content contains all expected sections
- Contact information properly formatted
- Attachments and links correctly parsed
- Enhancement scoring (9/9 = perfect)

**Expected output:**
```
📞 Contact Information: ✅ All sections present
📎 Attachments & Links: ✅ All sections present
🎯 Enhancement Score: 9/9
🎉 EXCELLENT! Comprehensive contact and attachment information
```

#### **4. Full Integration Test (Optional)**
```bash
# Only if you have SAM.gov API credentials
export API_KEY="your_sam_api_key"
export API_URL="https://api.sam.gov/opportunities/v2/search"
python main.py
```
**What it tests:**
- Complete SAM.gov API integration
- Real opportunity detection and processing
- End-to-end Linear issue creation
- Continuous monitoring loop

**Press Ctrl+C after seeing successful scan**

### 📊 Test Results Interpretation

| Result | Meaning | Next Steps |
|--------|---------|------------|
| 🎉 **ALL TESTS PASSED** | System ready for production | Deploy with confidence |
| ❌ **Test 1 Failed** | Linear API connectivity issues | Check credentials, network, permissions |
| ❌ **Test 2 Failed** | Enhanced function problems | Review contact/attachment parsing logic |
| ❌ **Test 3 Failed** | Issue content missing features | Check description formatting |

### 🔍 Test Coverage

The test suite validates:
- **Authentication**: All API credentials and permissions
- **Core Functions**: Basic Linear operations (create, read, update)
- **Enhanced Features**: Contact extraction, attachment parsing, AI titles
- **Error Handling**: Graceful failure and recovery scenarios  
- **End-to-End**: Complete workflow from SAM.gov to Linear

### ⚠️ Testing Prerequisites

**Required Environment Variables:**
```bash
export LINEAR_API_KEY="lin_oauth_your_token"
export LINEAR_TEAM_ID="your_team_id"
```

**Optional (but recommended):**
```bash
export OPENAI_API_KEY="sk-your_openai_key"  # For AI titles
export API_KEY="your_sam_key"               # For full integration test
export API_URL="https://api.sam.gov/..."    # For full integration test  
```

### 🚨 Common Test Failures

**"LINEAR_API_KEY not set"**
```bash
# Fix: Set your Linear OAuth token
export LINEAR_API_KEY="lin_oauth_your_linear_oauth_token"
```

**"Linear API request failed with status 401"**
- Token expired or invalid
- Insufficient permissions
- Team ID doesn't match accessible teams

**"Enhancement Score: 5/9"** 
- Issue missing contact information
- Attachments not properly parsed
- Description formatting issues

**"OpenAI API errors"**
- API key invalid or quota exceeded
- Network connectivity issues
- Model availability problems (script continues with fallback titles)

## 🛠 Troubleshooting

### Common Issues

**"API_KEY environment variable is not set!"**
- Set your SAM.gov API key: `export API_KEY="your_key"`
- Ensure the key is valid and not expired

**"Linear API request failed"**
- Verify Linear OAuth token is correctly formatted (`lin_oauth_...`)
- Check team ID corresponds to an accessible Linear team
- Ensure proper permissions for issue creation

**"OpenAI API errors"**
- Verify OpenAI API key format (`sk-...`)
- Check API quota and billing status
- Script will fallback to standard titles if OpenAI fails

### Logs and Debugging

- **Log File**: `sam_monitor.log` contains detailed execution logs
- **Console Output**: Real-time status and error messages
- **Log Levels**: INFO for normal operation, ERROR for failures

### Performance Notes

- **Memory Usage**: Lightweight - stores only opportunity IDs in memory
- **Network**: Respectful API usage with proper error handling
- **Reliability**: Automatic retry logic for transient failures

## 🔐 Security Considerations

- **API Keys**: Store in environment variables, never commit to version control
- **Tokens**: Use OAuth tokens for Linear (more secure than Personal API keys)
- **Logs**: May contain opportunity details - secure log file access appropriately
- **Network**: All API communications use HTTPS

## 📈 Future Enhancements

- **Multi-NAICS Support**: Easily expandable to additional manufacturing codes
- **Slack Integration**: Optional notifications via Slack webhooks
- **Dashboard**: Web interface for monitoring status and statistics
- **Advanced Filtering**: Custom opportunity filtering beyond NAICS codes
- **Email Alerts**: Direct email notifications for high-priority opportunities

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📜 License

This project is for internal business use. Ensure compliance with SAM.gov API terms of service and applicable regulations.

---

**Built for defense contractors who need to stay ahead of opportunities.** 🎯 
