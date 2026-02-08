# Feature Specification: Bronze Tier AI FTE Foundation

**Feature Branch**: `001-bronze-fte-foundation`
**Created**: 2026-02-07
**Status**: Draft
**Input**: User description: "Bronze Tier AI FTE Foundation: An autonomous AI employee system with an Obsidian vault, file system watcher, Claude Code agent skills, and full audit logging."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - File Drop Detection and Action Creation (Priority: P1)

As a human operator, I drop a file into my AI Employee's Inbox folder. The system automatically detects the new file within seconds and creates a structured action item in the Needs_Action folder with metadata about the file (name, type, size, timestamp). This happens without any manual intervention and is logged for auditability.

**Why this priority**: This is the core perception capability — without file detection, the AI Employee cannot sense its environment. It is the foundation of the Perception → Reasoning → Action architecture and the minimum viable watcher.

**Independent Test**: Drop any file into AI_Employee_Vault/Inbox/ and verify that a corresponding .md action file appears in Needs_Action/ within 10 seconds, containing correct YAML frontmatter metadata.

**Acceptance Scenarios**:

1. **Given** the file system watcher is running and Inbox/ is empty, **When** a text file is copied into Inbox/, **Then** a markdown action file with YAML frontmatter (type, original_name, size, received timestamp, status: pending) appears in Needs_Action/ within 10 seconds.
2. **Given** the watcher is running, **When** a PDF document is dropped into Inbox/, **Then** the action file categorizes it as "document" and includes the file size in bytes.
3. **Given** the watcher is running, **When** multiple files are dropped into Inbox/ simultaneously, **Then** a separate action file is created in Needs_Action/ for each dropped file, with no duplicates.
4. **Given** the watcher is running, **When** a hidden file (starting with ".") or temporary file (ending with ".tmp") is dropped into Inbox/, **Then** no action file is created (these are silently ignored).
5. **Given** the watcher is running, **When** any file is processed, **Then** a structured log entry is appended to the daily log file in Logs/ with timestamp, action type, target, and result.

---

### User Story 2 - Vault Dashboard and Operational Visibility (Priority: P2)

As a human operator, I open my Obsidian vault and see a Dashboard.md that shows me the current state of my AI Employee at a glance: how many items are in each queue, what actions were taken recently, any errors or red flags, and system component status. This lets me do my daily 2-minute check without digging through logs.

**Why this priority**: The dashboard is the primary human interface for oversight. Without it, the operator has no visibility into what the AI is doing. The constitution mandates daily oversight capability.

**Independent Test**: Open Dashboard.md in Obsidian and verify it shows accurate folder counts, recent activity from logs, and any active alerts — all matching the actual vault state.

**Acceptance Scenarios**:

1. **Given** the vault has files in various folders, **When** the operator asks to update the dashboard, **Then** Dashboard.md is rewritten with accurate counts for every queue folder (Inbox, Needs_Action, Plans, Pending_Approval, In_Progress, Done).
2. **Given** the daily log file contains action entries, **When** the dashboard is updated, **Then** the Recent Activity section shows the last 24 hours of actions with timestamp, type, target, and result.
3. **Given** there are errors logged in today's log file, **When** the dashboard is updated, **Then** errors appear in both the Red Flags section (top of dashboard) and the Errors section.
4. **Given** there are items in Pending_Approval/ older than 24 hours, **When** the dashboard is updated, **Then** these overdue items appear in the Red Flags section as alerts.
5. **Given** EMERGENCY_STOP.md exists in the vault root, **When** the dashboard is updated, **Then** the Red Flags section prominently shows the emergency stop alert.

---

### User Story 3 - AI-Powered Inbox Processing (Priority: P3)

As a human operator, I ask my AI Employee to "process my inbox." The AI reads all pending action files in Needs_Action/, categorizes each item, determines what action to take based on the rules in Company_Handbook.md, and either processes the item (moving it to Done/) or flags it for human approval (creating an entry in Pending_Approval/). Every action is logged.

**Why this priority**: This is the reasoning capability — the AI making decisions about queued items. It depends on P1 (files must exist in Needs_Action/) and P2 (dashboard must exist to be updated). It completes the Perception → Reasoning → Action loop.

**Independent Test**: Place action files in Needs_Action/, invoke "Process my inbox" in Claude Code, and verify items are categorized, processed or flagged, moved to Done/ or Pending_Approval/, and logged.

**Acceptance Scenarios**:

1. **Given** there are action files in Needs_Action/ with status "pending", **When** the operator invokes the inbox processing skill, **Then** each file is read, categorized by type, and a processing decision is made.
2. **Given** an action file represents a routine file drop (e.g., a text document), **When** processed, **Then** the item is summarized, moved to Done/, and logged.
3. **Given** an action file has unclear or ambiguous content, **When** processed, **Then** it is flagged for human review in Pending_Approval/ with a summary of why it needs attention.
4. **Given** EMERGENCY_STOP.md exists in the vault root, **When** the operator invokes inbox processing, **Then** the system halts and reports the emergency stop condition without processing any items.
5. **Given** items are processed, **When** processing completes, **Then** Dashboard.md is updated to reflect the new state of all queue folders.

---

### User Story 4 - Quick Vault Status Report (Priority: P4)

As a human operator, I ask "What's the status?" and get an instant, read-only summary of the vault state: folder counts, recent activity, and any alerts — without modifying any files.

**Why this priority**: This is a lightweight read-only check that supports daily oversight. It depends on the vault having content (P2) but is simpler than processing (P3).

**Independent Test**: Invoke "What's the status?" in Claude Code and verify a concise text report is displayed with accurate folder counts and any alerts.

**Acceptance Scenarios**:

1. **Given** the vault has files in various folders, **When** the operator asks for a status report, **Then** a concise text summary is displayed showing item counts per folder.
2. **Given** there are log entries for today, **When** the status report is generated, **Then** the last 3 actions from today's log are shown.
3. **Given** EMERGENCY_STOP.md exists, **When** the status report is generated, **Then** it prominently warns about the emergency stop condition.
4. **Given** the status report is generated, **When** checking the vault afterward, **Then** no files have been created, modified, or moved (read-only operation).

---

### User Story 5 - Company Handbook as Rules Engine (Priority: P5)

As a human operator, I maintain a Company_Handbook.md file that contains my rules of engagement: which actions the AI can auto-approve, which require my approval, known contacts, financial thresholds, and opt-out lists. The AI Employee reads and follows these rules when making decisions.

**Why this priority**: The handbook is the configuration layer that governs AI behavior. Without it, the AI has no rules to follow. It supports P3 (inbox processing uses these rules) and enables constitution compliance.

**Independent Test**: Modify a threshold in Company_Handbook.md, then process an action item that crosses the threshold. Verify the AI's behavior changes according to the updated rules.

**Acceptance Scenarios**:

1. **Given** Company_Handbook.md defines auto-approve thresholds, **When** the AI processes an action item, **Then** it reads and applies the thresholds from the handbook.
2. **Given** a contact is listed in the opt-out list, **When** a communication to that contact is being processed, **Then** the item is always routed to Pending_Approval/ regardless of other thresholds.
3. **Given** the handbook defines financial rules (e.g., "flag payments over $500"), **When** a financial action exceeds the threshold, **Then** it is routed to Pending_Approval/ with the rule cited.
4. **Given** the handbook is modified, **When** the AI processes the next batch of items, **Then** the updated rules are used (not cached stale rules).

---

### Edge Cases

- What happens when the watcher is started but Inbox/ does not exist? The system MUST create it automatically.
- What happens when the Logs/ directory is missing? The system MUST create it before writing the first log entry.
- What happens when the daily log file is corrupted or contains invalid content? The system MUST create a new log file for the day and log a warning about the corruption.
- What happens when a file is dropped into Inbox/ while the watcher is restarting? The file MUST be detected on the next check cycle (no permanent loss).
- What happens when Needs_Action/ contains files with invalid or missing YAML frontmatter? The AI MUST flag these as "unknown" type and route to human review.
- What happens when the operator creates EMERGENCY_STOP.md? The watcher MUST halt within one check cycle, and all skills MUST check for it before processing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST monitor the Inbox/ folder for new files and detect additions within one check cycle (default 5 seconds)
- **FR-002**: System MUST create structured markdown action files in Needs_Action/ with YAML frontmatter containing: type, original_name, size, file_type, category, received timestamp, priority, and status
- **FR-003**: System MUST categorize dropped files by extension into categories: document, text, data, image, email, or unknown
- **FR-004**: System MUST write structured audit log entries to Logs/YYYY-MM-DD.json for every action (file detection, processing, errors, watcher start/stop)
- **FR-005**: System MUST check for EMERGENCY_STOP.md in the vault root before each processing cycle and halt if present
- **FR-006**: System MUST provide a Dashboard.md showing: red flags (top), system status, pending approvals, recent activity, queue folder counts, and errors
- **FR-007**: System MUST provide a Company_Handbook.md with configurable: communication rules, auto-approve thresholds, confidence scoring rules, known contacts list, opt-out list, financial rules, and watcher rules
- **FR-008**: System MUST provide an agent skill that reads Needs_Action/ items, categorizes them, processes or flags them per handbook rules, and moves completed items to Done/
- **FR-009**: System MUST provide an agent skill that scans vault folders and logs to regenerate Dashboard.md with current state
- **FR-010**: System MUST provide an agent skill that generates a read-only vault status report without modifying any files
- **FR-011**: System MUST ignore hidden files (starting with ".") and temporary files (ending with ".tmp") when detecting new files
- **FR-012**: System MUST prevent duplicate action file creation for the same source file
- **FR-013**: System MUST handle graceful shutdown when receiving termination signals without data loss or corruption
- **FR-014**: System MUST auto-create required directories (Inbox/, Needs_Action/, Logs/) if they do not exist at startup

### Key Entities

- **Action File**: A markdown file in Needs_Action/ representing a detected event. Contains YAML frontmatter with metadata (type, source, original_name, size, category, received timestamp, priority, status) and a body with suggested actions. Lifecycle: created in Needs_Action/ → processed → moved to Done/ or Pending_Approval/.
- **Audit Log Entry**: A structured record of every system action. Contains: timestamp, action_id (unique), action_type, actor, target, parameters, approval_status, result, error, and duration. Stored as entries in a daily array in Logs/YYYY-MM-DD.json.
- **Dashboard**: The Dashboard.md file — a live summary of vault state. Contains: red flags, system status, pending approvals, recent activity, queue counts, errors. Updated by the dashboard skill.
- **Company Handbook**: The Company_Handbook.md file — the rules engine. Contains: communication rules, auto-approve thresholds, confidence scoring, known contacts, opt-out list, financial rules. Read by skills to guide decision-making.

### Assumptions

- The Obsidian vault is located at AI_Employee_Vault/ in the project root
- The file system watcher monitors only the Inbox/ folder (not subdirectories)
- The watcher runs as a foreground process started manually (process management deferred to Silver Tier)
- All vault coordination happens through file-based communication (no database or message queue)
- The human operator interacts with skills through Claude Code's conversational interface
- Log retention is 90 days minimum (per constitution Section VII)
- The default check interval for the watcher is 5 seconds (configurable via environment variable)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: When a file is dropped into Inbox/, an action file appears in Needs_Action/ within 10 seconds (< 2x the default check interval)
- **SC-002**: 100% of watcher-detected files produce a corresponding audit log entry in Logs/
- **SC-003**: The dashboard accurately reflects the current vault state (folder counts match actual file counts within one update cycle)
- **SC-004**: The operator can complete a daily 2-minute status check using only Dashboard.md and the vault-report skill
- **SC-005**: The emergency stop mechanism halts the watcher within one check cycle (default 5 seconds) of EMERGENCY_STOP.md creation
- **SC-006**: All three agent skills (process-inbox, update-dashboard, vault-report) are automatically discovered and invoked by Claude Code when triggered by natural language
- **SC-007**: Zero secrets appear in any log file, action file, or vault document (constitution Section V compliance)
- **SC-008**: The system starts up and begins monitoring within 5 seconds of the run command being issued
