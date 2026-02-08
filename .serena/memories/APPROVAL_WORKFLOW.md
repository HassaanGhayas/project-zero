# Approval Workflow Implementation Plan

## Clarifications from User
1. **Approval Rules**: Imitate real successful automation systems
2. **Rejections**: Files move to Rejected/ folder
3. **Human Interface**: Obsidian only (YAML status field editing)
4. **Execution Trigger**: Scheduled + Continuous + Ralph Loop patterns

## Workflow Design

### State Machine
```
Needs_Action/ (pending)
    ↓ [user edits status: pending → approved]
Approved/ (approved)
    ↓ [process-inbox runs on schedule]
Done/ (completed)

If rejected:
Needs_Action/ (pending)
    ↓ [user edits status: pending → rejected]
Rejected/
```

### Approval Rules (Real-World Pattern)
Based on doc.md and common automation systems:

| Action Type | Threshold | Rule |
|---|---|---|
| Text documents (.txt, .md) | Any size | Auto-route to Done |
| Emails to known contacts | Any | Auto-route to Done |
| Payments | < $50 recurring OR to known vendor | Auto-approve |
| Payments | ≥ $50 OR new recipient | Require human approval |
| Social media | Scheduled posts | Auto-execute |
| Social media | Replies/DMs | Require human approval |
| File operations | Read/create | Auto-execute |
| File operations | Delete/move | Require human approval |

### Components to Build
1. **File Status Watcher** - Detect status changes in YAML, move files
2. **process-inbox Skill** - Execute approved actions per rules
3. **Rejection Handler** - Move to Rejected/ with reason
4. **Audit Logger** - NDJSON logging all state transitions
5. **Execution Scheduler** - cron-based triggers for process-inbox
