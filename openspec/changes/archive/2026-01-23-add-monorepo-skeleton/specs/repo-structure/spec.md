## ADDED Requirements
### Requirement: Base repository layout
The repository SHALL include top-level directories: backend/, frontend/, bot/, infra/, docs/.

#### Scenario: Fresh checkout layout
- **WHEN** a developer lists the repository root
- **THEN** all required top-level directories are present

### Requirement: Root documentation and config files
The repository SHALL include README.md, LICENSE (MIT), .gitignore, .editorconfig, and .env.example at the root.

#### Scenario: Root files present
- **WHEN** a developer checks the repository root
- **THEN** each required file exists

### Requirement: README onboarding guidance
The README SHALL describe the purpose of each top-level directory and include basic setup commands for frontend and Python environments.

#### Scenario: Developer onboarding
- **WHEN** a developer opens README.md
- **THEN** they can identify each directory's purpose and the minimal setup steps
