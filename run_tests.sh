#!/bin/bash

# SAM.gov Defense Contracting Monitor - Test Suite
# Run all tests in the correct order with proper error handling

echo "🧪 SAM.gov Monitor Test Suite"
echo "============================="
echo ""

# Check for required environment variables
echo "🔍 Checking environment variables..."
if [ -z "$LINEAR_API_KEY" ]; then
    echo "❌ ERROR: LINEAR_API_KEY not set"
    echo "   Run: export LINEAR_API_KEY='your_token'"
    exit 1
fi

if [ -z "$LINEAR_TEAM_ID" ]; then
    echo "❌ ERROR: LINEAR_TEAM_ID not set"
    echo "   Run: export LINEAR_TEAM_ID='your_team_id'"
    exit 1
fi

echo "✅ Required environment variables found"
echo ""

# Test 1: Basic Linear API connectivity
echo "🔌 Test 1: Basic Linear API Connectivity"
echo "========================================="
if python test_linear.py; then
    echo "✅ Test 1 PASSED: Linear API working correctly"
else
    echo "❌ Test 1 FAILED: Linear API issues detected"
    echo "   Fix Linear connectivity before proceeding"
    exit 1
fi
echo ""

# Test 2: Enhanced issue creation function
echo "🚀 Test 2: Enhanced Issue Creation"
echo "=================================="
if python test_linear_function.py; then
    echo "✅ Test 2 PASSED: Enhanced issue creation working"
else
    echo "❌ Test 2 FAILED: Enhanced function has issues"
    echo "   Check contacts/attachments implementation"
    exit 1
fi
echo ""

# Test 3: Content verification
echo "🔍 Test 3: Issue Content Verification"
echo "====================================="
if python verify_enhanced_issue.py; then
    echo "✅ Test 3 PASSED: Issue content verified"
else
    echo "❌ Test 3 FAILED: Issue content verification failed"
    echo "   Check issue description formatting"
    exit 1
fi
echo ""

# Summary
echo "🎉 ALL TESTS PASSED!"
echo "====================="
echo "Your SAM.gov monitor is ready for production use:"
echo ""
echo "✅ Linear API connectivity working"
echo "✅ Enhanced issue creation functioning"  
echo "✅ Contact and attachment extraction verified"
echo "✅ AI-powered titles generating correctly"
echo ""
echo "🚀 Ready to run: python main.py"
echo ""

# Optional: Offer to run integration test
if [ -n "$API_KEY" ] && [ -n "$API_URL" ]; then
    echo "🔗 SAM.gov API credentials detected."
    read -p "Run full integration test? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🌐 Running full integration test..."
        echo "   Press Ctrl+C after seeing a successful scan"
        python main.py
    fi
else
    echo "ℹ️  To test full SAM.gov integration, set API_KEY and API_URL"
fi 