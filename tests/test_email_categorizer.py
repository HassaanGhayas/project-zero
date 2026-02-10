"""
Unit tests for Email Categorizer (T045)

Tests priority determination logic with various email scenarios.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock
import tempfile
import yaml

from src.watchers.email_categorizer import EmailCategorizer


@pytest.fixture
def config_with_contacts(tmp_path):
    """Create a known_contacts.yaml file for testing."""
    config_file = tmp_path / "known_contacts.yaml"

    config_data = {
        "known_contacts": [
            {
                "email": "alice@company.com",
                "name": "Alice Internal",
                "category": "internal",
                "priority_override": "medium"
            },
            {
                "email": "newsletter@techweekly.com",
                "name": "Tech Weekly",
                "category": "newsletter",
                "priority_override": "low"
            },
            {
                "email": "vendor@stripe.com",
                "name": "Stripe",
                "category": "vendor",
                "priority_override": "high"
            }
        ],
        "financial_keywords": ["payment", "invoice", "billing", "transaction"]
    }

    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)

    return config_file


@pytest.fixture
def mock_logger():
    """Create mock logger."""
    return Mock()


@pytest.fixture
def categorizer(config_with_contacts, mock_logger):
    """Create EmailCategorizer instance."""
    return EmailCategorizer(config_with_contacts, logger=mock_logger)


class TestPriorityDetermination:
    """Test priority determination logic (T038)."""

    def test_unknown_sender_high_priority(self, categorizer):
        """Unknown sender without special flags = HIGH priority."""
        priority, category, actions = categorizer.determine_priority(
            sender_email="unknown@random.com",
            subject="Random email",
            snippet="Just a random message",
            has_attachments=False
        )

        assert priority == "high"

    def test_known_sender_no_attachments_medium_priority(self, categorizer):
        """Known internal contact without attachments = MEDIUM priority."""
        priority, category, actions = categorizer.determine_priority(
            sender_email="alice@company.com",
            subject="Team meeting tomorrow",
            snippet="Let's sync on the Q4 roadmap",
            has_attachments=False
        )

        assert priority == "medium"

    def test_newsletter_low_priority(self, categorizer):
        """Newsletter sender = LOW priority."""
        priority, category, actions = categorizer.determine_priority(
            sender_email="newsletter@techweekly.com",
            subject="This week in tech",
            snippet="The top 10 AI trends...",
            has_attachments=False
        )

        assert priority == "low"
        assert category == "newsletter"

    def test_vendor_override_high_priority(self, categorizer):
        """Vendor with priority_override=high = HIGH priority."""
        priority, category, actions = categorizer.determine_priority(
            sender_email="vendor@stripe.com",
            subject="Service incident alert",
            snippet="We experienced a brief outage...",
            has_attachments=False
        )

        assert priority == "high"

    def test_attachments_always_elevate_to_high(self, categorizer):
        """Email with attachments = HIGH priority regardless of sender."""
        priority, category, actions = categorizer.determine_priority(
            sender_email="alice@company.com",
            subject="Project proposal",
            snippet="Here's the detailed proposal...",
            has_attachments=True
        )

        assert priority == "high"

    def test_financial_keywords_high_priority(self, categorizer):
        """Email with financial keywords = HIGH priority + financial category."""
        priority, category, actions = categorizer.determine_priority(
            sender_email="unknown@random.com",
            subject="Invoice #12345",
            snippet="Payment of $5,000 due this Friday",
            has_attachments=False
        )

        assert priority == "high"
        assert category == "financial"

    def test_financial_keywords_override_known_contact_priority(self, categorizer):
        """Financial keywords elevate even known contacts to HIGH."""
        priority, category, actions = categorizer.determine_priority(
            sender_email="alice@company.com",
            subject="Expense reimbursement",
            snippet="Please process payment for...",
            has_attachments=False
        )

        assert priority == "high"
        assert category == "financial"


class TestConfigurationLoading:
    """Test configuration loading with fallback (T037)."""

    def test_missing_config_file_fallback(self, tmp_path, mock_logger):
        """Missing config file should fall back to empty whitelist."""
        missing_path = tmp_path / "nonexistent.yaml"

        categorizer = EmailCategorizer(missing_path, logger=mock_logger)

        # Should still work, treating all senders as unknown
        priority, category, actions = categorizer.determine_priority(
            sender_email="anyone@example.com",
            subject="Test",
            snippet="test",
            has_attachments=False
        )

        assert priority == "high"  # Unknown sender
        mock_logger.warning.assert_called()

    def test_invalid_yaml_fallback(self, tmp_path, mock_logger):
        """Invalid YAML should fall back gracefully."""
        bad_config = tmp_path / "bad.yaml"
        bad_config.write_text("{ invalid yaml [[[")

        categorizer = EmailCategorizer(bad_config, logger=mock_logger)

        # Should still work
        priority, category, actions = categorizer.determine_priority(
            sender_email="test@example.com",
            subject="Test",
            snippet="test",
            has_attachments=False
        )

        assert priority == "high"
        mock_logger.error.assert_called()


class TestSuggestedActions:
    """Test suggested action generation."""

    def test_high_priority_actions_include_warnings(self, categorizer):
        """HIGH priority emails should include security warnings."""
        priority, category, actions = categorizer.determine_priority(
            sender_email="unknown@random.com",
            subject="Urgent: Click here",
            snippet="Verify your account...",
            has_attachments=True
        )

        actions_text = " ".join(actions).lower()
        assert "unknown" in actions_text or "verify" in actions_text

    def test_medium_priority_actions_routine(self, categorizer):
        """MEDIUM priority should suggest routine review."""
        priority, category, actions = categorizer.determine_priority(
            sender_email="alice@company.com",
            subject="Meeting next week",
            snippet="Sync on Q4 planning",
            has_attachments=False
        )

        actions_text = " ".join(actions).lower()
        assert "known" in actions_text or "routine" in actions_text

    def test_newsletter_actions(self, categorizer):
        """Newsletter should suggest appropriate actions."""
        priority, category, actions = categorizer.determine_priority(
            sender_email="newsletter@techweekly.com",
            subject="This week's stories",
            snippet="Top trends...",
            has_attachments=False
        )

        actions_text = " ".join(actions).lower()
        assert "newsletter" in actions_text or "archive" in actions_text


class TestFinancialKeywordDetection:
    """Test financial keyword detection."""

    @pytest.mark.parametrize("keyword,should_detect", [
        ("payment", True),
        ("invoice", True),
        ("billing", True),
        ("transaction", True),
        ("normal message", False),
        ("regular email", False),
    ])
    def test_financial_keyword_variants(self, categorizer, keyword, should_detect):
        """Test detection of various financial keywords."""
        priority, category, actions = categorizer.determine_priority(
            sender_email="company@bank.com",
            subject=f"Important: {keyword}",
            snippet=f"This concerns a {keyword}",
            has_attachments=False
        )

        if should_detect:
            assert category == "financial", f"Failed to detect: {keyword}"
            assert priority == "high"
        else:
            # Non-financial should be medium (known-ish) or high (unknown)
            assert category != "financial"


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_case_insensitive_contact_matching(self, categorizer):
        """Contact matching should be case-insensitive."""
        priority, category, actions = categorizer.determine_priority(
            sender_email="ALICE@COMPANY.COM",  # UPPERCASE
            subject="Test",
            snippet="test",
            has_attachments=False
        )

        # Should match alice@company.com (case-insensitive)
        assert priority == "medium"

    def test_empty_snippet_handling(self, categorizer):
        """Should handle empty snippets gracefully."""
        priority, category, actions = categorizer.determine_priority(
            sender_email="unknown@example.com",
            subject="Subject only",
            snippet="",  # Empty snippet
            has_attachments=False
        )

        assert priority == "high"  # Unknown sender

    def test_multiple_financial_keywords(self, categorizer):
        """Email with multiple financial keywords still = HIGH."""
        priority, category, actions = categorizer.determine_priority(
            sender_email="unknown@example.com",
            subject="Invoice payment for transaction",
            snippet="Billing for invoice processing payment",
            has_attachments=False
        )

        assert priority == "high"
        assert category == "financial"

    def test_attachments_with_financial_keywords(self, categorizer):
        """Attachments + financial keywords = HIGH (multiply doesn't change result)."""
        priority, category, actions = categorizer.determine_priority(
            sender_email="alice@company.com",
            subject="Budget spreadsheet",
            snippet="Q4 budget payment schedule",
            has_attachments=True
        )

        assert priority == "high"
        assert category == "financial"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
