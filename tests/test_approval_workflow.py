"""
Test suite for complete approval workflow.

Tests the end-to-end approval and execution pipeline:
1. File drop in Inbox/ → Action file in Needs_Action/
2. User edits status to 'approved' → Moves to Approved/
3. Action executes → Confirmation in In_Progress/
4. User confirms → Moves to Done/

Also tests rejection workflow:
1. User edits status to 'rejected' → Moves to Rejected/
"""

import time
from pathlib import Path

import pytest
import yaml


def test_approval_workflow_end_to_end(
    vault_path,
    inbox_path,
    needs_action_path,
    approved_path,
    in_progress_path,
    done_path
):
    """
    Test complete approval workflow from Inbox to Done.

    Workflow:
      Inbox/ → Needs_Action/ → Approved/ → In_Progress/ → Done/
    """
    # Step 1: Create test file in Inbox/
    test_file = inbox_path / "test_approval.txt"
    test_file.write_text("Test content for approval workflow", encoding="utf-8")

    # Wait for filesystem watcher to create action file
    time.sleep(0.5)

    # Step 2: Verify action file created in Needs_Action/
    action_files = list(needs_action_path.glob("FILE_test_approval.txt.md"))
    assert len(action_files) == 1, "Action file should be created"

    action_file = action_files[0]

    # Read action file YAML
    content = action_file.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    frontmatter = yaml.safe_load(parts[1])

    assert frontmatter["status"] == "pending", "Initial status should be pending"
    assert frontmatter["type"] == "text", "File type should be text"

    # Step 3: Simulate user approval (edit status to 'approved')
    frontmatter["status"] = "approved"
    updated_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    updated_content = f"---\n{updated_yaml}---\n{parts[2]}"
    action_file.write_text(updated_content, encoding="utf-8")

    # Wait for status field watcher to move file to Approved/
    time.sleep(0.5)

    # Step 4: Verify file moved to Approved/
    assert not action_file.exists(), "Original file should be moved from Needs_Action/"

    approved_files = list(approved_path.glob("FILE_test_approval.txt.md"))
    # Note: Approved watcher processes immediately, so file might already be gone
    # Check In_Progress/ instead

    # Step 5: Verify execution happened and confirmation created in In_Progress/
    confirmation_files = list(in_progress_path.glob("CONFIRM_FILE_test_approval.txt.md"))
    assert len(confirmation_files) == 1, "Confirmation file should be created"

    executed_files = list(in_progress_path.glob("EXECUTED_FILE_test_approval*.md"))
    assert len(executed_files) == 1, "Executed file should be in In_Progress/"

    # Step 6: Read confirmation file
    confirmation_file = confirmation_files[0]
    confirmation_content = confirmation_file.read_text(encoding="utf-8")
    assert "Action Executed" in confirmation_content
    assert "Confirmation Required" in confirmation_content

    confirmation_parts = confirmation_content.split("---", 2)
    confirmation_fm = yaml.safe_load(confirmation_parts[1])
    assert confirmation_fm["type"] == "confirmation"
    assert confirmation_fm["status"] == "awaiting_confirmation"

    # Step 7: Simulate user confirmation (move to Done/)
    done_file = done_path / confirmation_file.name
    confirmation_file.rename(done_file)

    # Verify move successful
    assert done_file.exists(), "Confirmation file should be in Done/"
    assert not confirmation_file.exists(), "Confirmation file should be moved from In_Progress/"


def test_rejection_workflow(
    vault_path,
    inbox_path,
    needs_action_path,
    rejected_path
):
    """
    Test rejection workflow from Needs_Action to Rejected.

    Workflow:
      Inbox/ → Needs_Action/ → Rejected/
    """
    # Step 1: Create test file in Inbox/
    test_file = inbox_path / "test_rejection.txt"
    test_file.write_text("Test content for rejection workflow", encoding="utf-8")

    # Wait for filesystem watcher
    time.sleep(0.5)

    # Step 2: Verify action file created
    action_files = list(needs_action_path.glob("FILE_test_rejection.txt.md"))
    assert len(action_files) == 1

    action_file = action_files[0]

    # Step 3: Simulate user rejection (edit status to 'rejected')
    content = action_file.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    frontmatter = yaml.safe_load(parts[1])
    frontmatter["status"] = "rejected"
    updated_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    updated_content = f"---\n{updated_yaml}---\n{parts[2]}"
    action_file.write_text(updated_content, encoding="utf-8")

    # Wait for status field watcher
    time.sleep(0.5)

    # Step 4: Verify file moved to Rejected/
    assert not action_file.exists(), "Original file should be moved from Needs_Action/"

    rejected_files = list(rejected_path.glob("FILE_test_rejection.txt.md"))
    assert len(rejected_files) == 1, "Rejected file should be in Rejected/"

    rejected_file = rejected_files[0]

    # Verify status updated
    content = rejected_file.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    frontmatter = yaml.safe_load(parts[1])
    assert frontmatter["status"] == "rejected"


def test_multiple_approvals_in_sequence(
    vault_path,
    inbox_path,
    needs_action_path,
    in_progress_path
):
    """
    Test processing multiple files in sequence.

    Ensures watchers handle multiple files without conflicts.
    """
    # Create 3 test files
    for i in range(1, 4):
        test_file = inbox_path / f"test_multi_{i}.txt"
        test_file.write_text(f"Test content {i}", encoding="utf-8")

    # Wait for all action files to be created
    time.sleep(1.0)

    # Verify all 3 action files created
    action_files = list(needs_action_path.glob("FILE_test_multi_*.md"))
    assert len(action_files) == 3, "All 3 action files should be created"

    # Approve all files
    for action_file in action_files:
        content = action_file.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])
        frontmatter["status"] = "approved"
        updated_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        updated_content = f"---\n{updated_yaml}---\n{parts[2]}"
        action_file.write_text(updated_content, encoding="utf-8")
        time.sleep(0.3)  # Stagger approvals

    # Wait for all executions
    time.sleep(1.0)

    # Verify all confirmations created
    confirmation_files = list(in_progress_path.glob("CONFIRM_FILE_test_multi_*.md"))
    assert len(confirmation_files) == 3, "All 3 confirmations should be created"


def test_approval_rules_text_file(
    vault_path,
    inbox_path,
    needs_action_path
):
    """
    Test approval rules for text files (auto-approve < 1MB).
    """
    # Create small text file
    test_file = inbox_path / "small_text.txt"
    test_file.write_text("Small text content", encoding="utf-8")

    time.sleep(0.5)

    # Verify action file categorized correctly
    action_files = list(needs_action_path.glob("FILE_small_text.txt.md"))
    assert len(action_files) == 1

    content = action_files[0].read_text(encoding="utf-8")
    parts = content.split("---", 2)
    frontmatter = yaml.safe_load(parts[1])

    assert frontmatter["type"] == "text"
    assert frontmatter["priority"] == "low"
    assert frontmatter["status"] == "pending"


def test_emergency_stop_blocks_approval(
    vault_path,
    inbox_path,
    needs_action_path,
    approved_path
):
    """
    Test that EMERGENCY_STOP.md blocks approval processing.
    """
    # Create emergency stop file
    emergency_file = vault_path / "EMERGENCY_STOP.md"
    emergency_file.write_text("# EMERGENCY STOP", encoding="utf-8")

    # Create and approve a test file
    test_file = inbox_path / "test_emergency.txt"
    test_file.write_text("Test emergency stop", encoding="utf-8")

    time.sleep(0.5)

    action_files = list(needs_action_path.glob("FILE_test_emergency.txt.md"))
    
    if len(action_files) == 1:
        # Watcher created action file before emergency stop
        action_file = action_files[0]
        
        # Try to approve
        content = action_file.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])
        frontmatter["status"] = "approved"
        updated_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        updated_content = f"---\n{updated_yaml}---\n{parts[2]}"
        action_file.write_text(updated_content, encoding="utf-8")

        time.sleep(0.5)

        # File should NOT move to Approved/ (emergency stop active)
        assert action_file.exists(), "File should remain in Needs_Action/ during emergency stop"

    # Cleanup emergency stop
    emergency_file.unlink()
