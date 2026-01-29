# access-database Specification

## MODIFIED Requirements
### Requirement: Placeholder users model
The shared database module SHALL define a `users` table model with the following columns:
- `id` (Integer, primary key, auto-increment)
- `telegram_user_id` (BigInteger, unique, indexed)
- `username` (String, optional)
- `first_name` (String, optional)
- `last_name` (String, optional)
- `language_code` (String, optional)
- `is_premium` (Boolean, optional)
- `created_at` (DateTime, required, server default `now()`)
- `last_login_at` (DateTime, optional)

`telegram_user_id` SHALL be treated as the external identity for Telegram users.

#### Scenario: Users table definition
- **WHEN** SQLModel metadata is inspected
- **THEN** the `users` table includes the specified columns and a uniqueness constraint or index on `telegram_user_id`
