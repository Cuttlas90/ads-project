# Change: Add deal auto-posting, verification, and TON payout/refund workflow

## Why
The current system stops at escrow funding and does not complete the posting → verification → payout/refund lifecycle required by the project constitution. This change completes the core escrow flow so real TON deals can be fulfilled and settled automatically.

## What Changes
- Add auto-post scheduling and bot publishing for approved creatives with stored message metadata.
- Add periodic verification to detect deletions/edits and enforce a verification window.
- Add TON release/refund execution with fee and transaction logging.
- Add wallet address storage for payouts.

## Impact
- Affected specs: deal-management, escrow-management, ton-integration, new deal-posting, new deal-verification, new user-wallets.
- Affected code: backend Celery workers, deal FSM transitions, Telegram Bot API posting, Telethon message checks, TON outbound transfer service, database schema + migrations.
