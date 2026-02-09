## ADDED Requirements

### Requirement: Marketplace channel-name navigation to stats
The advertiser marketplace UI SHALL render channel name/title in each listing card as a tappable navigation target to `/advertiser/channels/:channelId/stats`. It SHALL use `channel_id` from `GET /marketplace/listings` response as the route parameter.

#### Scenario: Advertiser opens stats by tapping channel title
- **WHEN** an advertiser taps the channel name/title on a marketplace listing card
- **THEN** the app navigates to `/advertiser/channels/:channelId/stats` for that listing's `channel_id`

### Requirement: Advertiser stats page partial-data rendering
The advertiser stats page SHALL render partial data without blocking the page. For metrics and charts with `availability = ready`, it SHALL render the value/chart. For chart sections with `availability = missing`, `async_pending`, or `error`, the default behavior SHALL be hidden sections. For scalar/value metrics with unavailable states, the page SHALL render a non-blocking placeholder.

#### Scenario: Missing and async metrics do not break page
- **WHEN** the stats response contains a mix of `ready`, `missing`, and `async_pending` metrics
- **THEN** the page renders available metrics, hides unavailable chart sections by default, and keeps unavailable scalar metrics non-blocking

### Requirement: Shared stats routes by role
The UI SHALL expose stats pages for both roles using role-scoped routes (`/advertiser/channels/:channelId/stats` and `/owner/channels/:channelId/stats`). Advertiser role SHALL access the advertiser route, owner role SHALL access the owner route, and route guards SHALL redirect cross-role deep links to the caller's role default route.

#### Scenario: Owner opens owner stats route
- **WHEN** a user with owner role opens `/owner/channels/:channelId/stats`
- **THEN** the page is accessible in read-only mode

#### Scenario: Owner opens advertiser stats deep link
- **WHEN** a user with owner role opens `/advertiser/channels/:channelId/stats`
- **THEN** the app redirects to `/owner`
