# Feature Specification: Gmail Integration for AI Employee

**Feature Branch**: `002-gmail-integration`
**Created**: 2026-02-09
**Status**: Draft
**Input**: User description: "Build Gmail integration for the AI Employee system, extending Bronze Tier's file-based monitoring to include email monitoring. This adds real-time Gmail watching, email action file generation, and email execution via MCP servers."

## User Scenarios & Testing

### User Story 1 - Email Detection and Action File Creation (Priority: P1)

As a user, I want Gmail emails to be automatically detected and converted into action files in my Obsidian vault, so I can review and manage email actions through a unified interface without switching between email and task management tools.

**Why this priority**: This is the foundational capability that enables all other email automation. Without detecting and surfacing emails as action files, no approval or execution workflow can function. This delivers immediate value by bringing emails into the user's existing Obsidian-based workflow.

**Independent Test**: Can be fully tested by sending a test email to the configured Gmail account and verifying an action file appears in `AI_Employee_Vault/Needs_Action/` within 5 minutes containing the email metadata (sender, subject, snippet) with status: pending.

**Acceptance Scenarios**:

1. **Given** Gmail watcher is running, **When** a new unread email arrives in Gmail inbox, **Then** an action file is created in Needs_Action/ within 5 minutes with YAML frontmatter containing type: email, sender, subject, received timestamp, and status: pending
2. **Given** Gmail watcher is running, **When** multiple emails arrive simultaneously, **Then** separate action files are created for each email without duplicates
3. **Given** an email has already been processed, **When** the watcher runs again, **Then** no duplicate action file is created for the same email (message ID tracking prevents duplicates)
4. **Given** Gmail API returns a rate limit error, **When** the watcher encounters this error, **Then** the watcher implements exponential backoff and continues running without crashing

---

### User Story 2 - Email Action Approval via Obsidian (Priority: P2)

As a user, I want to approve email actions by editing YAML status fields in Obsidian, so I can maintain control over automated email operations using my existing note-taking workflow without learning new interfaces.

**Why this priority**: This extends the Bronze Tier approval workflow to email actions, maintaining consistency with the existing file-based approval pattern. It's P2 because it requires P1 (email detection) to be functional first.

**Independent Test**: Can be fully tested by manually editing an action file's YAML frontmatter (changing status: pending to status: approved), saving the file, and verifying within 2 seconds that the file moves to the Approved/ folder.

**Acceptance Scenarios**:

1. **Given** an email action file exists in Needs_Action/ with status: pending, **When** user edits YAML to status: approved and saves, **Then** within 2 seconds the file moves to Approved/ folder
2. **Given** an email action file exists in Needs_Action/ with status: pending, **When** user edits YAML to status: rejected and saves, **Then** within 2 seconds the file moves to Rejected/ folder
3. **Given** multiple email action files await approval, **When** user approves them in sequence, **Then** each file moves to Approved/ independently without interfering with others
4. **Given** EMERGENCY_STOP.md exists in vault root, **When** user attempts to approve an email action, **Then** the file remains in Needs_Action/ and no movement occurs (emergency halt active)

---

### User Story 3 - Email Execution via MCP Servers (Priority: P3)

As a user, I want approved email actions (archive, mark as read) to be executed via MCP servers, so I have complete auditability and can verify that automated actions actually happened before marking tasks complete.

**Why this priority**: This provides the "hands" for the AI Employee to take real actions on emails. It's P3 because it depends on both P1 (detection) and P2 (approval) being functional. Delivers value by closing the loop from detection to execution.

**Independent Test**: Can be fully tested by approving an email action file, waiting 5 seconds, and verifying: (1) confirmation file created in In_Progress/ showing execution result, (2) audit log contains email_executed entry, (3) actual Gmail message is archived/marked as read when checked via Gmail UI.

**Acceptance Scenarios**:

1. **Given** an email action file moves to Approved/, **When** approved watcher detects the file, **Then** Gmail MCP server is called to archive the email, a confirmation file is created in In_Progress/, and audit log records the action with result: success
2. **Given** Gmail MCP server call fails (network error), **When** execution is attempted, **Then** audit log records error, confirmation file shows failure message, and original action file remains in Approved/ for retry
3. **Given** an email has been successfully archived, **When** user reviews the confirmation file, **Then** it displays email message ID, action taken (archived), timestamp, and Gmail API response status
4. **Given** multiple approved emails exist, **When** approved watcher processes them, **Then** each email is executed independently, and failures do not block subsequent emails

---

### User Story 4 - Email Approval Rules Enforcement (Priority: P4)

As a user, I want email approval rules (known contacts whitelist, attachment requirements, etc.) enforced automatically, so I'm only bothered with emails requiring human judgment and routine emails are handled predictably.

**Why this priority**: This is a quality-of-life enhancement that reduces approval fatigue. It's P4 because it requires the full workflow (P1-P3) to be functional before rules can be applied. Delivers value by filtering noise and focusing human attention.

**Independent Test**: Can be fully tested by sending emails from both known and unknown contacts, with and without attachments, and verifying that action files are created with appropriate priority levels and suggested actions based on Company Handbook rules.

**Acceptance Scenarios**:

1. **Given** an email arrives from a known contact (in whitelist) with no attachments, **When** action file is created, **Then** priority is set to medium and suggested actions include "Auto-archive after review"
2. **Given** an email arrives from an unknown sender, **When** action file is created, **Then** priority is set to high and suggested actions include "Requires human approval before any action"
3. **Given** an email contains attachments, **When** action file is created, **Then** priority is set to high regardless of sender, and suggested actions include "Review attachments before approval"
4. **Given** an email contains payment/invoice keywords, **When** action file is created, **Then** priority is set to high, category is marked as financial, and suggested actions include "Financial review required"

---

### Edge Cases

- **What happens when Gmail API quota is exceeded?** Watcher implements exponential backoff (doubling check_interval up to max 1 hour), logs the quota error, and continues retrying. User is notified via dashboard if watcher has been backed off for >30 minutes.

- **How does the system handle emails with very large attachments (>10MB)?** Action file includes attachment metadata (filename, size) but does not download attachments. User is notified of large attachments in the action file and must manually review them in Gmail.

- **What happens if two watchers start simultaneously?** Lock file mechanism prevents concurrent watcher instances. If a second watcher starts, it detects the lock file, logs a warning, and exits gracefully.

- **How does the system handle Gmail authentication expiration?** Watcher detects OAuth token expiration, logs authentication error with clear instructions for re-authentication, and enters paused state. User must re-run Gmail OAuth flow to resume operations.

- **What happens if an action file is manually moved between folders?** Status field watcher only triggers on YAML edits (file modification events), not on file moves. Manual moves bypass the workflow and are logged as anomalies but don't crash the system.

- **How does the system handle emails in non-English languages?** Email snippets and subjects are stored verbatim in action files. The system does not perform translation. Gmail API provides text as-is, and Unicode content is preserved in UTF-8 encoded markdown files.

## Requirements

### Functional Requirements

- **FR-001**: System MUST poll Gmail API for unread important messages at a configurable interval (default: 120 seconds = 2-minute polling, ~8,640 calls/day with 16% headroom from 10k quota)
- **FR-002**: System MUST create action files in Needs_Action/ folder for each newly detected email with YAML frontmatter containing: type, original_name (from + subject), size, file_type (.eml), category (email), received timestamp, priority, status (pending), and gmail_message_id
- **FR-003**: System MUST track processed Gmail message IDs to prevent duplicate action file creation across watcher restarts
- **FR-004**: System MUST implement exponential backoff when Gmail API returns rate limit errors (HTTP 429), doubling check_interval up to a maximum of 3600 seconds (1 hour)
- **FR-005**: System MUST detect YAML frontmatter status field changes (pending → approved, pending → rejected) within 2 seconds and move files to appropriate folders (Approved/, Rejected/)
- **FR-006**: System MUST call Gmail MCP server to execute approved actions (archive_email, mark_as_read) and log all MCP calls to NDJSON audit log
- **FR-007**: System MUST create confirmation files in In_Progress/ folder after executing email actions, containing execution result, timestamp, and Gmail API response
- **FR-008**: System MUST apply email approval rules from Company Handbook to determine priority levels: high (unknown sender, attachments, financial keywords), medium (known sender), low (newsletters, automated notifications)
- **FR-009**: System MUST integrate Gmail watcher into existing run_all_watchers.py orchestrator so all watchers (filesystem, status_field, approved, gmail) start and stop together
- **FR-010**: System MUST load Gmail OAuth credentials from environment variables (.env file) and validate they exist before watcher initialization
- **FR-011**: System MUST preserve existing Bronze Tier functionality (file-based watching, status field watching, approval execution) while adding Gmail integration
- **FR-012**: System MUST gracefully handle Gmail authentication errors by pausing the watcher, logging clear error messages, and providing re-authentication instructions

### Key Entities

- **Email Action File**: Represents a Gmail message requiring review/action. Contains YAML frontmatter with email metadata (sender, subject, message ID, priority, status) and markdown body with email snippet and suggested actions. Lives in Needs_Action/ until approved or rejected.

- **Gmail MCP Server**: External service interface that executes Gmail operations (archive, mark as read, send). Called by approved watcher after human approval. Returns structured response with status and message ID.

- **Known Contacts Whitelist**: Configuration data (stored in config/known_contacts.yaml) listing trusted email addresses that receive medium/low priority instead of high priority. Used by email categorization rules.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Gmail emails are detected and converted to action files within 3-5 minutes of arrival (95th percentile, assuming 120-second poll interval)
- **SC-002**: Action file approval (YAML edit + save) triggers file movement to Approved/ folder within 2 seconds (99th percentile)
- **SC-003**: Approved email actions are executed via MCP server and confirmed within 5 seconds of approval (95th percentile)
- **SC-004**: System handles Gmail API rate limits gracefully with zero watcher crashes due to quota errors over 7-day test period
- **SC-005**: All email actions (detection, approval, execution) are logged to NDJSON audit log with 100% coverage (no unlogged actions)
- **SC-006**: Known contact whitelist correctly categorizes emails as medium/low priority in 95% of test cases, reducing high-priority noise by 40%
- **SC-007**: Gmail watcher restarts after system reboot within 30 seconds when using PM2 process manager
- **SC-008**: User can complete a full email workflow (receive → review → approve → execute → confirm) in under 3 minutes for a typical email

## Assumptions

- User has a Gmail account with API access enabled (Gmail API must be activated in Google Cloud Console)
- User can complete OAuth2 authentication flow to obtain credentials.json and token.json files
- User has Obsidian installed and configured to point to AI_Employee_Vault/
- Bronze Tier implementation (filesystem watcher, status field watcher, approved watcher) is complete and functional
- User has Python 3.12+ and uv package manager installed
- User is running on Linux/macOS or Windows with WSL (for bash script compatibility)
- Gmail API quota limits are at default free tier levels (10,000 queries/day, 250 queries/user/second)
- Network connectivity is stable enough for API calls (occasional transient failures are handled, but permanent offline states are not)

## Dependencies

### Internal Dependencies

- **Bronze Tier Foundation**: All Bronze Tier components (BaseWatcher, action file generator, status field watcher, approved watcher, logging utilities, YAML frontmatter parser) must be functional
- **Approval Workflow**: Existing two-stage approval workflow (Needs_Action → Approved → In_Progress → Done) must be operational
- **Company Handbook**: Email approval rules must be documented in AI_Employee_Vault/Company_Handbook.md

### External Dependencies

- **Gmail API**: Google API client libraries (google-auth, google-auth-oauthlib, google-api-python-client)
- **MCP Framework**: Claude Code MCP server registration system must be functional
- **Environment Configuration**: Python dotenv library for loading .env configuration
- **Process Management** (optional): PM2 for production watcher orchestration (not required for development/testing)

## Out of Scope (Silver Tier Phase 1)

- **Sending emails**: Phase 1 only supports read-only operations (archive, mark as read). Email composition and sending are deferred to later phases.
- **Email drafting**: Automated reply generation is not included. User must manually compose replies in Gmail if needed.
- **WhatsApp/LinkedIn integration**: These are separate Silver Tier phases and not part of Gmail integration.
- **Advanced email filtering**: Complex rule engines (e.g., regex patterns, machine learning classification) are not included. Only basic whitelist and keyword matching are supported.
- **Email thread tracking**: Phase 1 treats each email independently. Thread/conversation grouping is out of scope.
- **Calendar integration**: Email invites and calendar events are not parsed or processed specially.
- **Attachment processing**: Attachments are noted but not downloaded or analyzed. User must review them manually in Gmail.
- **Multi-account support**: Phase 1 supports a single Gmail account only.

## Constitutional Compliance

This feature adheres to AI FTE Constitution principles:

- **Section IV (Skills Policy)**: Gmail watcher will be implemented as a Claude skill for manual invocation during development, with automated scheduling added in later phases.
- **Section V (Security)**: Gmail OAuth credentials stored in .env file only, never hardcoded. Credentials loaded via python-dotenv.
- **Section VII (Audit Logging)**: All email detection, approval, and execution events logged to NDJSON with full context (actor, action type, parameters, result).
- **Section IX (Ethics)**: No autonomous email sending. All actions require human approval via status field editing.
- **Section XII (Human-in-the-Loop)**: Two-stage approval workflow enforced. Approved → execute → confirm pattern prevents irreversible actions without human review.
