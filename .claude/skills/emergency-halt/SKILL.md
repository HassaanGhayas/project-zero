---
name: Emergency Halt
description: Immediately halt all AI FTE operations by creating EMERGENCY_STOP.md. Use when you need to stop autonomous processing. User says "emergency halt", "stop everything", "halt operations", "emergency stop".
disable-model-invocation: true
color: red
---

# Emergency Halt Skill

Create `AI_Employee_Vault/EMERGENCY_STOP.md` to immediately stop all watcher operations.

## Purpose

Provides a safe, quick way to halt all autonomous AI FTE operations without killing processes. The file system watcher checks for EMERGENCY_STOP.md before every file operation and halts if detected.

## Steps

1. **Create emergency stop file**: Write `AI_Employee_Vault/EMERGENCY_STOP.md`
2. **Add timestamp content**: `Emergency stop activated by user at {ISO8601 timestamp}`
3. **Log to audit trail**:
   ```json
   {
     "timestamp": "{ISO8601}",
     "action_id": "emergency_halt_{uuid}",
     "action_type": "emergency_halt",
     "actor": "emergency-halt-skill",
     "target": "AI_Employee_Vault/EMERGENCY_STOP.md",
     "parameters": {"reason": "User invoked emergency halt"},
     "approval_status": null,
     "approved_by": "user",
     "result": "success",
     "error": null,
     "duration": null
   }
   ```
4. **Confirm to user**: `✋ Emergency stop activated. Watcher will halt on next check cycle.`

## To Resume Operations

Delete `AI_Employee_Vault/EMERGENCY_STOP.md`:
```bash
rm AI_Employee_Vault/EMERGENCY_STOP.md
```

Watcher will resume normal operations on next file detection.

## Constitution Compliance

This skill implements:
- ✅ **Section VIII**: Graceful Degradation & Error Recovery (emergency stop mechanism)
- ✅ **Section XII**: HITL enforcement (user-controlled halt mechanism)
- ✅ **Section XIII**: Non-Negotiable Rules (emergency stop functional and accessible)

## Safety Rules

1. **User-only invocation** - Cannot be triggered by Claude autonomously (disable-model-invocation: true)
2. **Non-destructive** - Only creates a single marker file, no data loss
3. **Reversible** - Delete EMERGENCY_STOP.md to resume
4. **Logged** - All emergency halts are recorded in audit trail

## Notes

- This is a **Bronze Tier** skill: File-based emergency stop only
- Watcher checks for EMERGENCY_STOP.md before every file operation (FR-005)
- Skills also check for emergency stop and abort gracefully
- Dashboard and vault-report skills are explicitly safe to run during emergency stop (provide visibility)
