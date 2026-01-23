# Change: Monorepo skeleton + tooling

## Why
Establish a clean, minimal monorepo foundation so future PRs can add product logic on a stable structure.

## What Changes
- Create the root directory layout: backend/, frontend/, bot/, infra/, docs/
- Add root documentation and baseline config files (README.md, LICENSE, .gitignore, .editorconfig, .env.example)
- Add a root Makefile with help/dev/lint/test commands that work without Docker
- Scaffold minimal backend and bot Python packages using Poetry
- Scaffold a minimal Vue 3 + Vite + TypeScript frontend

## Impact
- Affected specs: repo-structure, dev-tooling, backend-skeleton, bot-skeleton, frontend-skeleton
- Affected code: root files plus backend/, frontend/, bot/, infra/, docs/
