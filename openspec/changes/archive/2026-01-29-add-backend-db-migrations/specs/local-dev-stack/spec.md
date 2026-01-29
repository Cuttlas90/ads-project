## ADDED Requirements
### Requirement: Shared module available in dev containers
The local Docker Compose stack SHALL mount the root `shared/` directory into backend, worker, and bot containers and set `PYTHONPATH` so those services can import the shared module.

#### Scenario: Shared imports in dev stack
- **WHEN** a developer starts the local dev stack
- **THEN** backend, worker, and bot can import the shared database module without manual path tweaks
