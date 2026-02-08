---
name: constitution-compliance-checker
description: Verify all code changes comply with 13 constitutional sections
context: fork
model: sonnet
---

# Constitution Compliance Checker

Review recent changes for compliance with `.specify/memory/constitution.md`.

## Purpose

Automated auditor that validates code changes against the 13-section AI FTE Constitution. Runs as an independent subagent with isolated context.

## Audit Checklist

### Section I: Identity & Scope
- ✅ File operations within AI_Employee_Vault/ only
- ✅ No unauthorized system access
- ✅ Human accountability preserved

### Section II: Directory Structure
- ✅ Vault folder structure maintained (13 required folders)
- ✅ .claude/skills/ organization correct
- ✅ specs/ structure follows SDD pattern

### Section III: Spec-Driven Development
- ✅ New features have spec.md, plan.md, tasks.md
- ✅ Constitution consulted during planning
- ✅ ADRs created for significant decisions

### Section IV: Skills-Based AI
- ✅ New AI functionality as skills (not inline code)
- ✅ Skills have proper YAML frontmatter
- ✅ Skills in .claude/skills/ directory
- ✅ User-only skills use disable-model-invocation: true

### Section V: Security & Secret Handling
- ✅ No secrets in code (API keys, passwords, tokens)
- ✅ Secrets in .env only
- ✅ .env in .gitignore
- ✅ No hardcoded credentials

### Section VI: External Integrations (Silver Tier+)
- N/A for Bronze Tier (file-based only)

### Section VII: Audit Logging
- ✅ NDJSON logging present for all actions
- ✅ Required fields present (timestamp, action_type, actor, target, parameters, result)
- ✅ Logs append-only
- ✅ Logs excluded from git

### Section VIII: Error Recovery
- ✅ Emergency stop checks present
- ✅ SIGINT/SIGTERM signal handlers
- ✅ Graceful error handling
- ✅ Try-except blocks around file operations

### Section IX: Ethics
- ✅ No autonomous financial transactions
- ✅ HITL for uncertain decisions
- ✅ Confidence scoring implemented

### Section X: Transparency
- ✅ Dashboard visibility maintained
- ✅ Audit trail accessible
- ✅ Status report functionality working

### Section XI: Human Oversight
- ✅ 2-minute daily check capability
- ✅ Dashboard.md updated
- ✅ Quick status check available

### Section XII: HITL Enforcement
- ✅ Pending_Approval/ folder used for flagged items
- ✅ Auto-approve thresholds defined
- ✅ Human approval required for uncertain actions

### Section XIII: Non-Negotiables
- ✅ All above rules verified

## Output Format

```markdown
# Constitution Compliance Report

**Date**: {timestamp}
**Commit/Changes**: {recent git log or description}

## Compliance Status

| Section | Status | Details |
|---------|--------|---------|
| I. Identity & Scope | ✅ PASS | Operations within vault scope |
| II. Directory Structure | ✅ PASS | All required folders present |
| III. SDD Enforcement | ⚠️ WARN | Missing ADR for DB choice |
| IV. Skills Policy | ❌ FAIL | New AI logic in src/main.py not as skill |
| V. Secret Handling | ✅ PASS | No secrets in code |
| VI. MCP Integration | N/A | Bronze Tier |
| VII. Audit Logging | ✅ PASS | NDJSON logging present |
| VIII. Error Recovery | ✅ PASS | Emergency stop checks present |
| IX. Ethics | ✅ PASS | HITL for uncertain items |
| X. Transparency | ✅ PASS | Dashboard updated |
| XI. Human Oversight | ✅ PASS | 2-minute check possible |
| XII. HITL Enforcement | ✅ PASS | Approval queue functional |
| XIII. Non-Negotiables | ⚠️ WARN | See Section IV violation |

## Violations Found

### ❌ Section IV: Skills-Based AI (CRITICAL)
**File**: `src/main.py:45-67`
**Issue**: New AI decision logic implemented inline instead of as a Claude Code skill
**Recommendation**: Extract decision logic to `.claude/skills/decision-maker/SKILL.md`

### ⚠️ Section III: SDD Enforcement (WARNING)
**Issue**: Database choice (PostgreSQL) not documented in ADR
**Recommendation**: Create ADR documenting database selection rationale

## Summary

**Overall Status**: ⚠️ CONDITIONAL PASS
- **Critical Violations**: 1 (Section IV)
- **Warnings**: 1 (Section III)
- **Passes**: 11

**Action Required**: Fix Section IV violation before merge
```

## Usage

Run after major changes:
```bash
# In Claude Code
"Check constitution compliance on the latest changes"
```

Or for specific commits:
```bash
"Check constitution compliance for commit abc123"
```

## Notes

- Runs as forked context (isolated from main thread)
- Read-only analysis (no file modifications)
- Uses Sonnet model for thorough analysis
- Output can be saved to `history/audits/YYYY-MM-DD-compliance.md`
