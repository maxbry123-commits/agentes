#!/bin/bash

# Test script for confirmation handler
# This creates a temporary rule file with a CONFIRM rule and tests the confirmation flow

set -e

echo "Testing AgentGuard Confirmation Handler"
echo "========================================"
echo ""

# Create a temporary directory for testing
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"

# Create a test rule file with a CONFIRM rule
cat > .agentguard << 'EOF'
# Test rules for confirmation
?rm -rf test*
!rm -rf /
+echo *
EOF

echo "Created test rules in $TEST_DIR/.agentguard"
echo ""
echo "Test 1: Confirmation with 'y' response"
echo "---------------------------------------"
echo "Command: rm -rf test-file"
echo "Expected: Should prompt for confirmation, then execute if 'y' is entered"
echo ""

# Note: This is a manual test - automated testing of stdin is complex
echo "To test manually:"
echo "1. cd $TEST_DIR"
echo "2. Run: node $(pwd)/../dist/bin/agentguard-shell.js -c 'rm -rf test-file'"
echo "3. Enter 'y' when prompted"
echo "4. Verify command would execute (or be blocked if file doesn't exist)"
echo ""
echo "Test 2: Confirmation with 'n' response"
echo "---------------------------------------"
echo "Command: rm -rf test-file"
echo "Expected: Should prompt for confirmation, then block if 'n' is entered"
echo ""
echo "To test manually:"
echo "1. cd $TEST_DIR"
echo "2. Run: node $(pwd)/../dist/bin/agentguard-shell.js -c 'rm -rf test-file'"
echo "3. Enter 'n' when prompted"
echo "4. Verify command is blocked"
echo ""
echo "Test 3: Confirmation timeout"
echo "----------------------------"
echo "Command: rm -rf test-file"
echo "Expected: Should prompt for confirmation, then block after 30 seconds if no input"
echo ""
echo "To test manually:"
echo "1. cd $TEST_DIR"
echo "2. Run: node $(pwd)/../dist/bin/agentguard-shell.js -c 'rm -rf test-file'"
echo "3. Wait 30 seconds without entering anything"
echo "4. Verify command is blocked with timeout message"
echo ""

echo "Test directory: $TEST_DIR"
echo "Remember to clean up: rm -rf $TEST_DIR"
