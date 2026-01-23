## ADDED Requirements
### Requirement: Root Makefile commands
The repository SHALL provide a root Makefile with help, dev, lint, and test targets.

#### Scenario: Discoverable commands
- **WHEN** a developer runs `make help`
- **THEN** the available commands and descriptions are printed

### Requirement: Safe development commands
The dev, lint, and test targets SHALL run configured tooling when available, otherwise print guidance and exit successfully.

#### Scenario: Tooling not yet configured
- **WHEN** a developer runs `make lint` or `make test` before tools are configured
- **THEN** the command prints guidance and exits with status 0
