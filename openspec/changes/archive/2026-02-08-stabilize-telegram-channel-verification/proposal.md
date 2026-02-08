## Why

Channel verification currently depends on external MTProto connectivity and a pre-authorized Telethon session, but those prerequisites are not fully formalized in the spec workflow. In real environments this leads to verification attempts failing due to blocked MTProto paths or unauthorized sessions, with unclear operator guidance and inconsistent failure behavior at the API boundary.

## What Changes

- Define an explicit verification preflight for Telethon-dependent channel verification:
  - validate connection path readiness
  - validate Telethon session authorization state before stats calls
  - surface actionable failure reasons for operators and clients
- Formalize Telegram MTProto transport configuration requirements, including optional MTProxy settings and validation rules.
- Introduce a production session lifecycle model for the Telethon service account (bootstrap, persistence, verification, and rotation expectations).
- Define a controlled operator login flow to authorize Telethon for the service account (phone/code/2FA), so teams can bootstrap or re-authorize sessions without manual ad-hoc container steps.
- Clarify verification endpoint behavior when Telegram upstream dependencies fail so failures are controlled and predictable, and verification side effects are not persisted.
- Add observability expectations for verification failures so operational diagnosis is fast and repeatable.

## Capabilities

### New Capabilities
- `telethon-session-management`: Define requirements for provisioning, validating, and maintaining an authorized Telethon session used by backend verification flows.
- `telethon-auth-bootstrap`: Define how authorized personnel can initiate and complete Telethon login for the service account, including secure handling of OTP/2FA and session persistence.

### Modified Capabilities
- `channel-verification`: Expand requirements to cover Telethon preflight checks, controlled upstream failure behavior, and persistence guardrails when verification cannot complete.
- `telegram-integration`: Expand settings and client wrapper requirements to include optional MTProxy configuration and authorization-state aware Telethon usage.

## Impact

- Affected code paths: `backend/app/services/channel_verify.py`, `backend/app/api/routes/channels.py`, `shared/telegram/telethon_client.py`, `backend/app/settings.py`.
- Runtime configuration impact: MTProto proxy and session-related environment/secret management expectations.
- Operational impact: one-time Telethon authorization and ongoing session maintenance become explicit production requirements.
- Testing impact: new and updated tests for unauthorized sessions, proxy configuration errors, and deterministic API error mapping.
