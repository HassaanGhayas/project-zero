# Gmail MCP Server API Contract

**Version**: 1.0.0
**Status**: Specification
**Last Updated**: 2026-02-09

## Overview

The Gmail MCP Server provides a standardized interface for executing email operations against Gmail API. All operations are idempotent and return structured JSON responses.

---

## Tool Specifications

### 1. archive_email

**Purpose**: Archive a Gmail message (remove from INBOX, preserve in All Mail)

**Input Schema**:
```json
{
  "message_id": "string (required)"
}
```

**Input Constraints**:
- `message_id`: Must be a valid Gmail message ID (non-empty string)

**Output Schema (Success)**:
```json
{
  "status": "success",
  "action": "archived",
  "message_id": "string",
  "timestamp": "ISO 8601 datetime"
}
```

**Output Schema (Error)**:
```json
{
  "status": "error",
  "error_code": "string",
  "error_message": "string",
  "message_id": "string"
}
```

**Error Codes**:
- `NOT_FOUND`: Message ID does not exist or was already deleted
- `AUTH_ERROR`: OAuth token expired or invalid (user must re-authenticate)
- `RATE_LIMIT`: Gmail API quota exceeded (implement exponential backoff in calling code)
- `NETWORK_ERROR`: Transient network failure (caller should retry with exponential backoff)
- `PERMISSION_DENIED`: User lacks permission to archive (rare, check Gmail settings)

**Idempotency**: ✅ **FULLY IDEMPOTENT**
- Calling twice with same message_id returns success both times
- If message already archived, returns `{ status: "success", action: "already_archived" }`
- If message does not exist, returns `{ status: "error", error_code: "NOT_FOUND" }`

**Timeout**: 5 seconds

**Side Effects**:
- Removes INBOX label from message
- Preserves all other labels
- Logged to NDJSON audit log with message_id, result, timestamp

---

### 2. mark_as_read

**Purpose**: Mark a Gmail message as read (remove UNREAD label)

**Input Schema**:
```json
{
  "message_id": "string (required)"
}
```

**Input Constraints**:
- `message_id`: Must be a valid Gmail message ID (non-empty string)

**Output Schema (Success)**:
```json
{
  "status": "success",
  "action": "marked_as_read",
  "message_id": "string",
  "timestamp": "ISO 8601 datetime"
}
```

**Output Schema (Error)**:
```json
{
  "status": "error",
  "error_code": "string",
  "error_message": "string",
  "message_id": "string"
}
```

**Error Codes**: Same as archive_email
- `NOT_FOUND`
- `AUTH_ERROR`
- `RATE_LIMIT`
- `NETWORK_ERROR`
- `PERMISSION_DENIED`

**Idempotency**: ✅ **FULLY IDEMPOTENT**
- Calling twice with same message_id returns success both times
- If message already marked as read, returns `{ status: "success", action: "already_marked_as_read" }`
- If message does not exist, returns `{ status: "error", error_code: "NOT_FOUND" }`

**Timeout**: 5 seconds

**Side Effects**:
- Removes UNREAD label from message
- Preserves all other labels
- Logged to NDJSON audit log with message_id, result, timestamp

---

## Calling Conventions

### Authentication
- OAuth token must be valid and refreshed automatically before each call
- If `AUTH_ERROR` returned, calling code should:
  1. Log with level=ERROR
  2. Pause the watcher
  3. Display user message: "Gmail authentication expired. Run `scripts/setup_gmail_oauth.py` to re-authenticate."
  4. Exit gracefully

### Rate Limiting
- If `RATE_LIMIT` error received, calling code should implement exponential backoff:
  - Initial retry delay: 2 seconds
  - Backoff multiplier: 2x per attempt
  - Maximum delay: 3600 seconds (1 hour)
  - Log each backoff event to audit log

### Error Handling
- All errors include error_code and error_message for logging
- Calling code should log full error response to NDJSON audit log
- Network errors are retryable; Auth/Permission errors are not

### Audit Logging
Every call (success or error) must be logged to audit log with:
- `event_type`: "email_archive_attempt" or "email_mark_read_attempt"
- `message_id`: Gmail message ID
- `status`: "success" or "error"
- `error_code`: (if error)
- `timestamp`: ISO 8601
- `actor`: "gmail_mcp_server"

Example audit log entry:
```json
{"event_type":"email_archive_attempt","message_id":"18d4f3a2b1c9e7f6","status":"success","timestamp":"2026-02-09T15:30:45Z","actor":"gmail_mcp_server"}
```

---

## Implementation Notes

### For Task T025 (archive_email):
- Implement using Gmail API `users().messages().modify()` method
- Remove INBOX label by modifying message labels
- Handle NOT_FOUND gracefully (message may have been deleted by user)
- Return proper JSON response in both success and error cases

### For Task T026 (mark_as_read):
- Implement using Gmail API `users().messages().modify()` method
- Remove UNREAD label by modifying message labels
- Handle NOT_FOUND gracefully
- Return proper JSON response

### For Task T027 (error handling):
- Wrap both tools in try-catch
- Map Gmail API exceptions to standardized error codes
- Return error responses with proper structure

### For Task T028 (idempotency):
- Check current message state before modification
- If message already in desired state, return success with "already_X" action
- Never fail if message was already modified

### For Task T029 (audit logging):
- Call logger.log_email_operation() for every tool invocation
- Include full context: message_id, status, error_code (if applicable), timestamp
- NDJSON format: one JSON object per line, no arrays

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-09 | Initial specification for Phase 1 MVP |

---

## Compatibility

- **Gmail API Version**: v1
- **OAuth Scopes Required**: `https://www.googleapis.com/auth/gmail.modify`
- **Python Version**: 3.12+
- **Dependencies**: google-api-python-client ^2.118.0, google-auth-oauthlib ^1.2.0

