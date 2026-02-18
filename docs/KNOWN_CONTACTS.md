# Known Contacts Configuration Guide

Complete reference for configuring email priority rules using the `config/known_contacts.yaml` file.

## Overview

The known contacts whitelist controls how emails are prioritized based on sender identity. This file is used by `email_categorizer.py` to determine whether incoming emails are marked as high, medium, or low priority in action files.

**Why this matters**: By default, unknown senders are treated as HIGH priority (security-conscious). This file lets you downgrade trusted contacts to save you from notification fatigue while keeping important new emails visible.

## Schema Reference

### Contact Entry Fields

```yaml
known_contacts:
  - email: "sender@example.com"        # Required: email address to match (case-insensitive)
    name: "Display Name"                # Required: human-readable name
    category: "client"                  # Required: one of [client|internal|vendor|newsletter]
    priority_override: "medium"         # Optional: high|medium|low (null = auto-detect)
    notes: "Free text context"          # Optional: why they're in whitelist
```

### Field Definitions

| Field | Type | Required | Values | Purpose |
|-------|------|----------|--------|---------|
| `email` | string | ✅ | Any email | Exact match for sender (case-insensitive lookup) |
| `name` | string | ✅ | Any text | Display name for audit logs and action files |
| `category` | enum | ✅ | `client`, `internal`, `vendor`, `newsletter` | Contact type for categorization |
| `priority_override` | enum | ❌ | `high`, `medium`, `low`, `null` | Force priority level (null = use default logic) |
| `notes` | string | ❌ | Any text | Documentation (e.g., "responds in 24h", "SLA: 1hr") |

### Financial Keywords Section

```yaml
financial_keywords:
  - "payment"
  - "invoice"
  - "billing"
  # ... more keywords
```

All financial keywords are case-insensitive. Any email matching these keywords in subject or snippet is marked **HIGH** priority regardless of sender.

## Priority Logic

The system uses a 5-step decision tree to assign priorities:

```
1. Is sender in known_contacts.yaml?
   ├─ YES: Is priority_override set?
   │  ├─ YES → Use override (high/medium/low)
   │  └─ NO → Go to step 2
   └─ NO → Go to step 5

2. Is sender a newsletter?
   ├─ YES → Set priority = LOW
   └─ NO → Go to step 3

3. Does email have attachments?
   ├─ YES → Set priority = HIGH (security alert)
   └─ NO → Go to step 4

4. Does email match financial keywords?
   ├─ YES → Set priority = HIGH (financial alert)
   └─ NO → Set priority = MEDIUM (known, trusted)

5. Unknown sender (not in whitelist)
   ├─ Attachments? → HIGH
   ├─ Financial keywords? → HIGH
   └─ Otherwise → HIGH (default security posture)
```

**In practice:**

| Scenario | Priority | Reasoning |
|----------|----------|-----------|
| Known client with override set to "low" | LOW | Explicit override always wins |
| Newsletter (category: newsletter) | LOW | Automated, low urgency |
| Unknown sender with PDF attachment | HIGH | Unknown + attachment = security alert |
| Known vendor, mentions "invoice" | HIGH | Financial keyword triggers override |
| Known internal team, no special flags | MEDIUM | Trusted sender, routine |
| Email from boss@company.com | MEDIUM or HIGH | Depends on override and flags |

## Categories and Defaults

### 1. **client** - External customers and accounts

```yaml
- email: "alice.client@example.com"
  name: "Alice Smith - ACME Corp"
  category: "client"
  priority_override: null  # Medium by default
  notes: "Key account manager, SLA: 24h response"

- email: "procurement@bigclient.com"
  name: "Big Client Procurement"
  category: "client"
  priority_override: "high"  # Rush projects
  notes: "Frequently urgent; always high priority"
```

**When to use:** External companies, customers, accounts you serve.

**Default priority:** MEDIUM (trusted but external)

**Override recommendations:**
- Set to HIGH for VIP accounts or rush projects
- Set to MEDIUM (null) for normal clients
- Set to LOW only for inactive/historical accounts

### 2. **internal** - Team members and company email

```yaml
- email: "bob@company.com"
  name: "Bob Johnson - Engineering Lead"
  category: "internal"
  priority_override: null  # Medium by default
  notes: "Team lead, can loop in for architecture reviews"

- email: "exec@company.com"
  name: "Executive Leadership"
  category: "internal"
  priority_override: "high"  # Always urgent
  notes: "CEO - always treat as high priority"
```

**When to use:** Team members, colleagues, internal departments.

**Default priority:** MEDIUM (trusted, internal)

**Override recommendations:**
- Set to HIGH for executives, managers, or urgent roles
- Set to MEDIUM (null) for regular team members
- Set to LOW for automated internal tools/notifications (use `newsletter` category instead)

### 3. **vendor** - Service providers and infrastructure

```yaml
- email: "billing@stripe.com"
  name: "Stripe Billing"
  category: "vendor"
  priority_override: "high"  # Payment processor
  notes: "Critical payment infrastructure - financial alerts"

- email: "support@cloudprovider.com"
  name: "Cloud Provider Support"
  category: "vendor"
  priority_override: "high"  # SLA critical
  notes: "Production infrastructure - 1-hour SLA"

- email: "info@saasservice.com"
  name: "SaaS Service"
  category: "vendor"
  priority_override: "medium"  # Regular vendor
  notes: "Software service, routine notifications"
```

**When to use:** Payment processors, cloud providers, software services, consultants.

**Default priority:** MEDIUM or HIGH (depends on criticality)

**Override recommendations:**
- Set to HIGH for payment processors, infrastructure, critical SLAs
- Set to MEDIUM for regular vendors
- Set to LOW for vendors you rarely interact with

### 4. **newsletter** - Automated and informational

```yaml
- email: "noreply@techweekly.com"
  name: "Tech Weekly Newsletter"
  category: "newsletter"
  priority_override: "low"  # Always low
  notes: "Weekly digest, review once per week"

- email: "updates@github.com"
  name: "GitHub Notifications"
  category: "newsletter"
  priority_override: "low"
  notes: "Pull request updates, low priority"

- email: "digests@medium.com"
  name: "Medium Daily Digest"
  category: "newsletter"
  priority_override: "low"
  notes: "Content digests, FYI only"
```

**When to use:** Newsletters, automated notifications, marketing emails.

**Default priority:** LOW (informational, not actionable)

**Override recommendations:**
- Always set to "low" for newsletters
- Use for any automated email that doesn't require immediate action
- Consider unsubscribing instead if not reading

## Financial Keywords

List of keywords that trigger HIGH priority for any email, regardless of sender:

```yaml
financial_keywords:
  - "payment"           # Credit card, payment processing
  - "invoice"           # Bill, statement
  - "billing"           # Account billing cycle
  - "transaction"       # Financial transaction
  - "refund"            # Money back
  - "subscription"      # Recurring billing
  - "charges"           # Account charges
  - "receipt"           # Purchase receipt
  - "purchase"          # Order, purchase
  - "order confirmation" # Order confirmation
  - "payment due"       # Bill reminder
  - "account balance"   # Financial statement
```

**How matching works:**
- Keywords are case-insensitive
- Matched against email subject + snippet
- Partial matches work (e.g., "payment" matches "payment received" and "payment method")
- Multiple keywords in one email still trigger HIGH priority (not cumulative)

**When emails get HIGH priority:**
1. Unknown sender + any of these keywords → HIGH
2. Known contact + financial keyword → HIGH (override!)
3. Any sender + financial keyword → HIGH

**Customization:**
Add more keywords to catch domain-specific financial terms:

```yaml
financial_keywords:
  - "payment"
  - "invoice"
  # Add more:
  - "wire transfer"     # For business banking
  - "cryptocurrency"    # For crypto companies
  - "dividend"          # For investment accounts
  - "tax report"        # For accountants
```

## How to Configure

### Step 1: Start with the Template

Copy the example file:

```bash
cp config/known_contacts.yaml config/known_contacts.yaml.backup
```

### Step 2: Add Your Contacts

Edit `config/known_contacts.yaml` and populate your known contacts:

```yaml
known_contacts:
  # Start with people you interact with most
  - email: "boss@company.com"
    name: "My Manager"
    category: "internal"
    priority_override: null
    notes: "Regular 1:1s and task assignments"

  - email: "client@customer.com"
    name: "Main Client Contact"
    category: "client"
    priority_override: "medium"
    notes: "Key account - responds 12-24h"

  # Add vendors incrementally
  - email: "noreply@stripe.com"
    name: "Stripe"
    category: "vendor"
    priority_override: "high"
    notes: "Payment processor - critical"
```

### Step 3: Test the Configuration

```bash
# Check if file is valid YAML
python3 -c "import yaml; yaml.safe_load(open('config/known_contacts.yaml'))"

# Should show no errors
```

### Step 4: Monitor and Adjust

Watch your vault for a few days:

```bash
# Check categorization logs
tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | grep categoriz
```

Adjust priorities if needed:
- Too many false positives → Lower priority for more contacts
- Missing important emails → Reduce financial_keywords list

### Step 5: Commit Your Changes

```bash
git add config/known_contacts.yaml
git commit -m "config: populate known contacts whitelist"
```

## Best Practices

### 1. **Start Conservative**

- Start with few known contacts (5-10)
- Add more as you see the system working
- Better to have fewer false positives than miss important emails

### 2. **Use Priority Overrides Sparingly**

- Avoid setting priority_override unless necessary
- Prefer letting the logic work (attachments, financial keywords will override)
- Use overrides only for special cases (VIPs, payment processors)

### 3. **Organize by Category**

Group your file by category for readability:

```yaml
known_contacts:
  # ===== INTERNAL TEAM =====
  - email: "bob@company.com"
    ...

  # ===== CLIENTS =====
  - email: "alice@client.com"
    ...

  # ===== VENDORS =====
  - email: "stripe@example.com"
    ...

  # ===== NEWSLETTERS =====
  - email: "noreply@example.com"
    ...
```

### 4. **Keep Notes Current**

Update notes when contact relationships change:

```yaml
- email: "ex-client@oldaccount.com"
  name: "Old Client"
  category: "client"
  priority_override: "low"
  notes: "INACTIVE - contract ended 2024-12-31"
```

### 5. **Customize Financial Keywords for Your Domain**

If you're in specific industries, add domain-specific keywords:

**E-commerce:**
```yaml
financial_keywords:
  - "order"
  - "shipment"
  - "refund"
```

**Crypto/Finance:**
```yaml
financial_keywords:
  - "blockchain"
  - "wallet"
  - "exchange"
  - "liquidity"
```

**HR/Payroll:**
```yaml
financial_keywords:
  - "payroll"
  - "deduction"
  - "401k"
```

### 6. **Review Periodically**

Every month, review your config:

```bash
# See how many of each category
grep -c "category: \"client\"" config/known_contacts.yaml
grep -c "category: \"internal\"" config/known_contacts.yaml
grep -c "category: \"vendor\"" config/known_contacts.yaml
grep -c "category: \"newsletter\"" config/known_contacts.yaml
```

Remove or update inactive contacts.

## Integration with Code

### How email_categorizer.py Uses This File

The `email_categorizer.py` module loads this file on initialization:

```python
from src.watchers.email_categorizer import EmailCategorizer

categorizer = EmailCategorizer("config/known_contacts.yaml")

priority, category, actions = categorizer.determine_priority(
    sender_email="alice@example.com",
    subject="Q4 Budget Review",
    snippet="Please review the attached budget proposal...",
    has_attachments=True
)

# Returns: ("high", "email", ["Review email...", "Contains attachments...", ...])
```

### File Format Requirement

- **Format**: YAML 1.2
- **Encoding**: UTF-8
- **Structure**: Must have top-level `known_contacts` list and optional `financial_keywords` list
- **Validation**: Run `yaml.safe_load()` - no advanced YAML features allowed

### Error Handling

If the file is missing or invalid:

- System logs a warning but continues
- All senders treated as UNKNOWN (HIGH priority)
- Financial keywords not applied
- Service degrades gracefully (security-first default)

## Troubleshooting

### Problem: Emails from known contacts still showing HIGH priority

**Check 1: Email case sensitivity**
```yaml
# Wrong - email mismatch
- email: "Alice@Example.com"

# Right - email addresses are case-insensitive in matching
- email: "alice@example.com"
```

**Check 2: Verify financial keywords**
If "high" priority but contact is known:
- Email contains a financial keyword
- Check logs: `grep "financial" AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json`

**Check 3: Verify priority_override**
```yaml
# This FORCES high priority regardless of logic
- email: "trusted@example.com"
  priority_override: "high"  # ← This wins over everything
```

### Problem: Newsletters still showing HIGH priority

**Check 1: Category must be "newsletter"**
```yaml
# Wrong - category will be auto-detected as "email"
- email: "noreply@techweekly.com"
  name: "Tech Weekly"
  # Missing category!

# Right
- email: "noreply@techweekly.com"
  name: "Tech Weekly"
  category: "newsletter"
  priority_override: "low"
```

**Check 2: Override must be explicitly set**
```yaml
# Wrong - null means "use default logic"
- email: "noreply@example.com"
  category: "newsletter"
  priority_override: null  # ← This allows other rules to override!

# Right - explicitly force low
- email: "noreply@example.com"
  category: "newsletter"
  priority_override: "low"
```

### Problem: Configuration not reloading

**Solution**: Restart the Gmail watcher

```bash
# Stop current watchers
pkill -f "python.*gmail_watcher"

# Start fresh
uv run -m src.watchers.run_all_watchers
```

The categorizer reloads config on each watcher restart.

## Examples

### Minimal Setup (5 contacts)

Perfect for getting started:

```yaml
known_contacts:
  - email: "boss@company.com"
    name: "My Manager"
    category: "internal"
    priority_override: null
    notes: "Daily work"

  - email: "payment@stripe.com"
    name: "Stripe"
    category: "vendor"
    priority_override: "high"
    notes: "Payment processor"

  - email: "noreply@github.com"
    name: "GitHub"
    category: "newsletter"
    priority_override: "low"
    notes: "PR notifications"

  - email: "main@client.com"
    name: "Key Client"
    category: "client"
    priority_override: "medium"
    notes: "Primary account"

  - email: "alerts@pingdom.com"
    name: "Pingdom Alerts"
    category: "vendor"
    priority_override: "high"
    notes: "Uptime monitoring"

financial_keywords:
  - "invoice"
  - "payment"
  - "billing"
```

### Enterprise Setup (50+ contacts)

For larger organizations:

```yaml
known_contacts:
  # ===== EXECUTIVES =====
  - email: "ceo@company.com"
    name: "CEO"
    category: "internal"
    priority_override: "high"
    notes: "C-level executive"

  - email: "cfo@company.com"
    name: "CFO"
    category: "internal"
    priority_override: "high"
    notes: "Finance leadership"

  # ===== TEAMS =====
  - email: "engineering-lead@company.com"
    name: "Engineering Team Lead"
    category: "internal"
    priority_override: null
    notes: "Tech lead - architecture reviews"

  # ===== KEY CLIENTS =====
  - email: "vip-client@bigcorp.com"
    name: "VIP Client (BigCorp)"
    category: "client"
    priority_override: "high"
    notes: "Strategic account - 24h SLA"

  # ... 45 more entries

financial_keywords:
  - "invoice"
  - "payment"
  - "billing"
  - "wire transfer"
  - "purchase order"
  - "subscription renewal"
  - "payroll"
```

## Constitution Compliance

✅ **Section XII (Safety Rules)**: Email categorization is advisory only. Human approval is always required before email action execution.

This means:
- Categorization does NOT automatically archive emails
- Even LOW priority emails require approval
- User maintains full control via Obsidian YAML editing
- All actions logged in NDJSON audit trail

## See Also

- `src/watchers/email_categorizer.py` - Implementation details
- `src/watchers/gmail_watcher.py` - How categorizer is called
- `MANUAL_E2E_TEST_GUIDE.md` - Testing email categorization
- `docs/GMAIL_SETUP.md` - Gmail API authentication
