## 1. Implementation
- [x] 1.1 Add `deal_message_selections` model + migration
- [x] 1.2 Modify bot service to poll Telegram `getUpdates` and route messages/commands
- [x] 1.3 Implement `/deals` menu and `/deal <id>` selection flow with DB persistence
- [x] 1.4 Implement text message forwarding with deal context, event logging, and reply-keyboard shortcut
- [x] 1.5 Add bot tests for selection, messaging, and error handling
- [x] 1.6 Run bot test suite using: `cd /home/mohsen/ads-project/bot && source .venv/bin/activate && DATABASE_URL=postgresql+psycopg://ads:ads@localhost:5432/ads pytest`
