#!/bin/bash
#
# End-to-end test flow for AI FTE Bronze Tier
#
# Tests the complete workflow:
# 1. File drop in Inbox/
# 2. Action file creation in Needs_Action/
# 3. Audit logging to Logs/
# 4. Emergency stop mechanism
# 5. Dashboard generation
#
# Usage: bash tests/e2e_test_flow.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
TEST_VAULT="/tmp/ai_fte_test_vault_$$"
TEST_TIMEOUT=30

# Cleanup function
cleanup() {
    echo -e "${YELLOW}Cleaning up test vault...${NC}"
    rm -rf "$TEST_VAULT"
}

trap cleanup EXIT

# Utility functions
pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    exit 1
}

info() {
    echo -e "${YELLOW}→${NC} $1"
}

# Create test vault structure
setup_vault() {
    info "Setting up test vault at $TEST_VAULT"

    mkdir -p "$TEST_VAULT"/{Inbox,Needs_Action,Plans,Pending_Approval,Approved,Rejected,In_Progress,Done,Logs,Briefings,Accounting,Invoices}

    # Create .env configuration
    cat > "$TEST_VAULT/../.env.test" <<EOF
VAULT_PATH=$TEST_VAULT
INBOX_WATCH_PATH=$TEST_VAULT/Inbox
WATCHER_CHECK_INTERVAL=1
DRY_RUN=false
DEV_MODE=true
EOF

    pass "Test vault structure created"
}

# Test 1: File detection
test_file_detection() {
    info "Test 1: File detection and action file creation"

    # Create test file
    echo "Test invoice content" > "$TEST_VAULT/Inbox/invoice.pdf"

    # Start watcher in background
    info "Starting watcher..."
    python src/watchers/run_watcher.py --vault-path "$TEST_VAULT" --config "$TEST_VAULT/../.env.test" &
    WATCHER_PID=$!

    # Wait for processing
    sleep 5

    # Check action file exists
    if [ -f "$TEST_VAULT/Needs_Action/FILE_invoice.pdf.md" ]; then
        pass "Action file created"
    else
        fail "Action file not created"
    fi

    # Verify YAML frontmatter
    if grep -q "type: document" "$TEST_VAULT/Needs_Action/FILE_invoice.pdf.md"; then
        pass "YAML frontmatter contains correct type"
    else
        fail "YAML frontmatter missing or incorrect"
    fi

    if grep -q "status: pending" "$TEST_VAULT/Needs_Action/FILE_invoice.pdf.md"; then
        pass "Status field set to pending"
    else
        fail "Status field incorrect"
    fi

    # Stop watcher
    kill $WATCHER_PID 2>/dev/null || true
    wait $WATCHER_PID 2>/dev/null || true
}

# Test 2: Audit logging
test_audit_logging() {
    info "Test 2: Audit logging verification"

    # Check log file exists
    TODAY=$(date +%Y-%m-%d)
    LOG_FILE="$TEST_VAULT/Logs/${TODAY}.json"

    if [ -f "$LOG_FILE" ]; then
        pass "Audit log file created"
    else
        fail "Audit log file not found"
    fi

    # Verify NDJSON format
    if jq empty "$LOG_FILE" 2>/dev/null; then
        pass "Audit log is valid NDJSON"
    else
        fail "Audit log has invalid JSON"
    fi

    # Check for required fields
    if jq -e '.timestamp' "$LOG_FILE" >/dev/null 2>&1; then
        pass "Audit log contains timestamp"
    else
        fail "Audit log missing timestamp"
    fi

    if jq -e '.action_type' "$LOG_FILE" >/dev/null 2>&1; then
        pass "Audit log contains action_type"
    else
        fail "Audit log missing action_type"
    fi
}

# Test 3: Emergency stop mechanism
test_emergency_stop() {
    info "Test 3: Emergency stop mechanism"

    # Create emergency stop file
    echo "Emergency stop active" > "$TEST_VAULT/EMERGENCY_STOP.md"
    pass "Emergency stop file created"

    # Start watcher
    python src/watchers/run_watcher.py --vault-path "$TEST_VAULT" --config "$TEST_VAULT/../.env.test" &
    WATCHER_PID=$!

    # Create test file
    echo "Test during emergency" > "$TEST_VAULT/Inbox/emergency_test.txt"

    # Wait for processing attempt
    sleep 5

    # Verify action file was NOT created
    if [ ! -f "$TEST_VAULT/Needs_Action/FILE_emergency_test.txt.md" ]; then
        pass "Emergency stop prevented action file creation"
    else
        fail "Emergency stop did not prevent action file creation"
    fi

    # Clean up
    kill $WATCHER_PID 2>/dev/null || true
    wait $WATCHER_PID 2>/dev/null || true
    rm "$TEST_VAULT/EMERGENCY_STOP.md"
}

# Test 4: Duplicate prevention
test_duplicate_prevention() {
    info "Test 4: Duplicate action file prevention"

    # Create action file manually
    cat > "$TEST_VAULT/Needs_Action/FILE_duplicate.txt.md" <<EOF
---
status: pending
---
# Original Content
EOF

    # Start watcher
    python src/watchers/run_watcher.py --vault-path "$TEST_VAULT" --config "$TEST_VAULT/../.env.test" &
    WATCHER_PID=$!

    # Create file with same name
    echo "Duplicate test" > "$TEST_VAULT/Inbox/duplicate.txt"

    # Wait for processing
    sleep 5

    # Verify original content preserved
    if grep -q "Original Content" "$TEST_VAULT/Needs_Action/FILE_duplicate.txt.md"; then
        pass "Duplicate action file prevented, original preserved"
    else
        fail "Duplicate action file overwrote original"
    fi

    # Clean up
    kill $WATCHER_PID 2>/dev/null || true
    wait $WATCHER_PID 2>/dev/null || true
}

# Test 5: File categorization
test_file_categorization() {
    info "Test 5: File categorization accuracy"

    # Start watcher
    python src/watchers/run_watcher.py --vault-path "$TEST_VAULT" --config "$TEST_VAULT/../.env.test" &
    WATCHER_PID=$!

    # Create various file types
    echo "Text content" > "$TEST_VAULT/Inbox/document.txt"
    echo "col1,col2" > "$TEST_VAULT/Inbox/data.csv"
    echo "Image data" > "$TEST_VAULT/Inbox/photo.jpg"

    # Wait for processing
    sleep 5

    # Verify categorization
    if grep -q "type: text" "$TEST_VAULT/Needs_Action/FILE_document.txt.md"; then
        pass "Text file categorized correctly"
    else
        fail "Text file categorization incorrect"
    fi

    if grep -q "type: data" "$TEST_VAULT/Needs_Action/FILE_data.csv.md"; then
        pass "Data file categorized correctly"
    else
        fail "Data file categorization incorrect"
    fi

    if grep -q "type: image" "$TEST_VAULT/Needs_Action/FILE_photo.jpg.md"; then
        pass "Image file categorized correctly"
    else
        fail "Image file categorization incorrect"
    fi

    # Clean up
    kill $WATCHER_PID 2>/dev/null || true
    wait $WATCHER_PID 2>/dev/null || true
}

# Main test execution
main() {
    echo "============================================"
    echo "AI FTE Bronze Tier - End-to-End Test Suite"
    echo "============================================"
    echo ""

    setup_vault
    test_file_detection
    test_audit_logging
    test_emergency_stop
    test_duplicate_prevention
    test_file_categorization

    echo ""
    echo "============================================"
    echo -e "${GREEN}All tests passed!${NC}"
    echo "============================================"
}

main
