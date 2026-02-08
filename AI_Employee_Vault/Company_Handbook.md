# Company Handbook

**Version**: 1.0.0
**Last Updated**: 2026-02-08T10:30:24Z

---

## Communication Rules

Guidelines for email/message handling (Bronze Tier foundation, no email MCP integration yet).

- Auto-reply to known contacts: disabled
- Flag messages from unknown senders: yes
- Response tone: professional
- Archive handled messages: enabled

---

## Auto-Approve Thresholds

Rules for autonomous action without human approval.

### File Processing

- **Text files** (*.txt, *.md, *.rtf): Auto-process if < 1MB
- **Documents** (*.pdf, *.docx, *.pptx): Require human review
- **Data files** (*.csv, *.xlsx, *.json, *.xml): Require human review
- **Image files** (*.jpg, *.png, *.gif, *.svg): Auto-process
- **Unknown file types**: Always flag for approval

### Financial Actions

- Payments < $50 to known vendors: Auto-approve (Silver Tier feature)
- Payments ≥ $50 OR new payees: Require approval (Silver Tier feature)

---

## Confidence Scoring Rules

How to assess whether to auto-process or flag for human review.

- **High confidence**: File type recognized, size < 1MB, common format (text/image)
- **Medium confidence**: Large file (> 1MB), unusual extension, document type
- **Low confidence**: Corrupted file, invalid frontmatter, permission errors, unknown type

---

## Known Contacts

Whitelist for auto-approve decisions (Bronze Tier: file system only, no external contacts).

(No external contacts in Bronze Tier - file system operations only)

---

## Opt-Out List

Contacts requiring human approval for ALL actions (Bronze Tier: file system only).

(No external contacts in Bronze Tier - file system operations only)

---

## Financial Rules

Payment and accounting thresholds (deferred to Silver Tier - Bronze has no payment integration).

- Flag payments > $500 (Silver Tier feature)
- Flag recurring subscriptions > $100/month (Silver Tier feature)
- Auto-log routine expenses < $50 (Silver Tier feature)

---

## Watcher Rules

Inbox monitoring behavior for filesystem_watcher.

- **Check interval**: N/A (event-driven Observer pattern in use)
- **Ignore hidden files**: Yes (files starting with .)
- **Ignore temp files**: Yes (*.tmp, *.swp, *.lock)
- **Auto-create missing folders**: Yes
- **Duplicate prevention**: Enabled (prevent FILE_X.md duplicates)
- **Log retention**: 30 days (manual rotation in Bronze)
- **Emergency stop checks**: Every cycle (EMERGENCY_STOP.md detection)
