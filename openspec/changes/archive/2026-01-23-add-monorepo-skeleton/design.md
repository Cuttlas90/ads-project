## Context
This change creates the initial monorepo scaffold and developer tooling for a greenfield codebase.

## Goals / Non-Goals
- Goals:
  - Provide a minimal, clean directory layout for backend, frontend, and bot services
  - Establish baseline developer commands and configuration files
  - Keep scaffolds installable and ready for later feature work
- Non-Goals:
  - No application logic, endpoints, or business workflows
  - No Docker or infrastructure orchestration in this change

## Decisions
- Use Poetry for Python package management in backend and bot, each with its own pyproject.toml
- Use Vue 3 + Vite with TypeScript for the frontend scaffold
- Use npm for frontend scripts and dependency management
- Make Makefile commands tolerant of missing tooling by printing guidance and exiting successfully

## Risks / Trade-offs
- Placeholder lint/test commands can mask missing tooling; mitigate with clear README guidance and follow-up setup work.

## Migration Plan
No migration; this is the initial repository scaffold.

## Open Questions
None.
