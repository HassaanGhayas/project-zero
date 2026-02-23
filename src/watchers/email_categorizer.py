"""
Email Categorizer - Priority Determination Logic for Gmail Integration

This module implements email priority categorization based on:
- Known contacts whitelist (config/known_contacts.yaml)
- Attachment presence
- Financial keyword detection

Priority Levels:
- HIGH: Unknown sender, has attachments, or financial keywords
- MEDIUM: Known contact without attachments
- LOW: Newsletters or automated notifications

Constitution Compliance:
    - Section XII: All categorization is advisory only - human approval still required
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import yaml


class EmailCategorizer:
    """
    Categorize emails and determine priority levels.

    Attributes:
        config_path: Path to known_contacts.yaml configuration file
        known_contacts: Dict mapping email addresses to contact metadata
        financial_keywords: List of keywords that trigger financial category
        logger: Logger instance
    """

    def __init__(
        self, config_path: str | Path, logger: Optional[logging.Logger] = None
    ):
        """
        Initialize email categorizer with known contacts configuration.

        Args:
            config_path: Path to known_contacts.yaml file
            logger: Optional logger instance
        """
        self.config_path = Path(config_path)
        self.logger = logger or logging.getLogger(__name__)

        # Load configuration with fallback (T037)
        self.known_contacts: Dict[str, Dict[str, Any]] = {}
        self.financial_keywords: List[str] = []
        self._load_configuration()

    def _load_configuration(self) -> None:
        """
        Load known_contacts.yaml configuration with fallback to empty whitelist.

        If file is missing or invalid, falls back to empty configuration
        and logs a warning. Never fails initialization.
        """
        if not self.config_path.exists():
            self.logger.warning(
                f"Known contacts file not found: {self.config_path}. "
                "Falling back to empty whitelist. All senders will be treated as unknown."
            )
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not config:
                self.logger.warning(
                    "Empty known contacts configuration. Using defaults."
                )
                return

            # Parse known contacts into lookup dictionary
            contacts_list = config.get("known_contacts", [])
            for contact in contacts_list:
                email = contact.get("email")
                if email:
                    self.known_contacts[email.lower()] = contact

            # Load financial keywords
            self.financial_keywords = [
                kw.lower() for kw in config.get("financial_keywords", [])
            ]

            self.logger.info(
                f"Loaded {len(self.known_contacts)} known contacts, "
                f"{len(self.financial_keywords)} financial keywords"
            )

        except yaml.YAMLError as e:
            self.logger.error(
                f"Failed to parse {self.config_path}: {e}. Using empty whitelist."
            )
        except Exception as e:
            self.logger.error(
                f"Unexpected error loading {self.config_path}: {e}. Using empty whitelist.",
                exc_info=True,
            )

    def _is_known_contact(
        self, sender_email: str
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if sender is in known contacts list.

        Args:
            sender_email: Email address to check

        Returns:
            Tuple of (is_known, contact_metadata)
        """
        sender_lower = sender_email.lower()
        contact = self.known_contacts.get(sender_lower)
        return (contact is not None, contact)

    def _contains_financial_keywords(self, subject: str, snippet: str) -> bool:
        """
        Check if email contains financial keywords in subject or snippet.

        Args:
            subject: Email subject line
            snippet: Email snippet/preview

        Returns:
            True if any financial keyword found, False otherwise
        """
        combined_text = f"{subject} {snippet}".lower()
        return any(keyword in combined_text for keyword in self.financial_keywords)

    def determine_priority(
        self, sender_email: str, subject: str, snippet: str, has_attachments: bool
    ) -> Tuple[str, str, List[str]]:
        """
        Determine email priority level based on categorization rules (T038).

        Priority Logic:
        1. If sender in known_contacts and priority_override set: use override
        2. Else if has_attachments: HIGH
        3. Else if financial keywords match: HIGH
        4. Else if known sender + no attachments: MEDIUM
        5. Else (unknown sender): HIGH

        Args:
            sender_email: Sender email address
            subject: Email subject line
            snippet: Email snippet/preview text
            has_attachments: Whether email has attachments

        Returns:
            Tuple of (priority, category, suggested_actions)
            - priority: "high" | "medium" | "low"
            - category: "email" | "financial" | "newsletter"
            - suggested_actions: List of action strings
        """
        # Check if known contact
        is_known, contact = self._is_known_contact(sender_email)

        # Check for financial keywords
        is_financial = self._contains_financial_keywords(subject, snippet)

        # Default values
        priority = "high"
        category = "email"
        suggested_actions = []

        # Priority determination logic
        if is_known and contact:
            # Known contact - check for override
            priority_override = contact.get("priority_override")
            contact_category = contact.get("category", "unknown")

            if priority_override:
                # Use explicit priority override
                priority = priority_override
            elif contact_category == "newsletter":
                # Newsletters always low priority unless override
                priority = "low"
                category = "newsletter"
            elif has_attachments:
                # Attachments always elevate to high
                priority = "high"
            elif is_financial:
                # Financial keywords always high
                priority = "high"
                category = "financial"
            else:
                # Known sender, no special conditions = medium
                priority = "medium"

        else:
            # Unknown sender
            if is_financial:
                priority = "high"
                category = "financial"
            elif has_attachments:
                priority = "high"
            else:
                # Unknown sender without special flags still high priority
                priority = "high"

        # Generate suggested actions based on priority and category
        suggested_actions = self._generate_suggested_actions(
            priority, category, is_known, has_attachments, is_financial
        )

        return (priority, category, suggested_actions)

    def _generate_suggested_actions(
        self,
        priority: str,
        category: str,
        is_known: bool,
        has_attachments: bool,
        is_financial: bool,
    ) -> List[str]:
        """
        Generate priority-appropriate suggested actions.

        Args:
            priority: Determined priority level
            category: Determined category
            is_known: Whether sender is known contact
            has_attachments: Whether email has attachments
            is_financial: Whether email contains financial keywords

        Returns:
            List of suggested action strings
        """
        actions = []

        # Base action: review email
        actions.append("Review email content in Gmail")

        # Priority-specific actions
        if priority == "high":
            if not is_known:
                actions.append("⚠️  Unknown sender - verify legitimacy before action")
            if has_attachments:
                actions.append(
                    "⚠️  Contains attachments - scan for security before opening"
                )
            if is_financial:
                actions.append("💰 Financial email - verify transaction details")
            actions.append("Approve for archival only after thorough review")

        elif priority == "medium":
            actions.append("Known contact - routine review")
            actions.append("Reply if action needed, otherwise approve for archival")

        else:  # low priority
            if category == "newsletter":
                actions.append("Newsletter/automated - review for relevance")
                actions.append("Archive or mark as read if not needed")

        # Common final action
        actions.append("Edit YAML status field to 'approved' or 'rejected'")

        return actions
