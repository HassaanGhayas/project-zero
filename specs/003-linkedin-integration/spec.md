# Feature Specification: LinkedIn Integration for AI Employee

**Feature Branch**: `002-gmail-integration`
**Created**: 2026-02-18
**Status**: Approved
**Phase**: Silver Tier Phase 3

## Overview

Enable the AI Employee to publish posts to the user's personal LinkedIn profile. Approved action files of type `linkedin_post` are automatically published via LinkedIn API v2 (OAuth2).

---

## User Scenarios & Testing

### User Story 1 — LinkedIn Post from Action File (P1)

As a user, I want approved LinkedIn post action files to be automatically published to my LinkedIn profile, so I can manage my professional presence through the same vault workflow without switching tools.

**Acceptance Scenarios:**

1. **Given** a `linkedin_post` action file exists in `Pending_Approval/` with `status: approved`, **When** the LinkedIn watcher runs, **Then** the post text is published to LinkedIn and the action file is moved to `Done/`
2. **Given** the LinkedIn API returns 429, **When** the watcher hits the rate limit, **Then** it backs off exponentially (2, 4, 8 min) and retries up to 3 times without crashing
3. **Given** `EMERGENCY_STOP.md` exists in the vault, **When** the watcher runs, **Then** no posts are published and the watcher logs the halt
4. **Given** a post has already been published (action file in Done/), **When** the watcher runs again, **Then** no duplicate post is made

### User Story 2 — OAuth Token Management (P2)

As a user, I want LinkedIn tokens managed automatically, so I don't need to re-authenticate every time the token expires.

**Acceptance Scenarios:**

1. **Given** the access token is expired, **When** a post is attempted, **Then** the watcher auto-refreshes using the stored refresh token
2. **Given** the refresh token is also expired, **When** a post is attempted, **Then** an alert action file is created in `Needs_Action/` prompting the user to re-authenticate via `docs/LINKEDIN_SETUP.md`

---

## Constraints

- Post only (no DMs, no connection management) — `w_member_social` scope only
- No image uploads in MVP (text posts only)
- Secrets (`LINKEDIN_CLIENT_SECRET`) must live in `.env`, never committed
- All post attempts must be audit-logged (NDJSON to `Logs/audit.json`)
- Emergency stop check mandatory before every post
