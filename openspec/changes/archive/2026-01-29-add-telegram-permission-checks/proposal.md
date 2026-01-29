# Change: Centralized Telegram permission checks

## Why
Sensitive actions require accurate, Telegram-sourced permission checks for both the system bot and human admins. Today there is no single authoritative module or spec that defines required bot rights, structured results, or reusable domain enforcement.

## What Changes
- Add a new `telegram-permissions` capability spec focused on Telegram permission checks.
- Define a single source of truth for required bot rights and structured permission check results.
- Add async checks for bot and user permissions that rely only on Telegram data and return structured results.
- Add a small domain helper to convert structured permission results into explicit domain errors.

## Impact
- Affected specs: new `telegram-permissions` capability (no changes to existing specs).
- Affected code: `backend/app/telegram/permissions.py`, `backend/app/domain/permissions.py`, and new backend tests under `backend/tests/telegram/`.
