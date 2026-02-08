# Company Handbook

**Version**: 1.0.0
**Last Updated**: 2026-02-08T10:30:24Z

---

## Communication Rules

Guidelines for email/message handling and approval thresholds.

### Email Actions

- **Known contacts** (in whitelist): Auto-send replies < 500 characters
- **Unknown senders**: Always require human approval
- **Bulk sends** (>5 recipients): Always require human approval
- **Email with attachments**: Require human approval
- **Response tone**: Professional, concise
- **Archive handled messages**: Enabled

### Social Media Posts

- **Scheduled posts**: Auto-execute if pre-approved in content calendar
- **Replies to DMs**: Always require human approval
- **Comments on public posts**: Always require human approval
- **Posts mentioning money/pricing**: Always require human approval

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

Payment and accounting thresholds with approval requirements.

### Payment Actions

- **Recurring payments** < $50 to **known vendors**: Auto-approve
- **Recurring payments** ≥ $50 OR to **new payees**: Require human approval
- **One-time payments** < $100 to **known vendors**: Auto-approve
- **One-time payments** ≥ $100: Always require human approval
- **International transfers**: Always require human approval
- **Banking credential changes**: Always require human approval

### Accounting Actions

- **Expense logging** < $50: Auto-categorize and log
- **Expense logging** ≥ $50: Require human review
- **Invoice generation**: Auto-generate for approved contracts
- **Invoice sending**: Require human approval before send
- **Subscription audits**: Flag unused subscriptions (no login 30+ days)
- **Budget alerts**: Notify if category exceeds 80% of monthly budget

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
