---
artifact: checkpoints
project: Lockr
date: 2026-04-15
---

# BMAD Checkpoints

## Checkpoint 001

- role: analyst
- phase: analysis
- workflow: brief
- artifact created or updated: overview
- blockers: none
- decisions: product is local-first; v1 excludes hosted sync and enterprise scope
- handoff target: pm
- completion state: complete

## Checkpoint 002

- role: pm
- phase: planning
- workflow: prd
- artifact created or updated: prd
- blockers: none
- decisions: MVP includes CLI vault, `.env` import, runtime injection, encrypted git backup, and minimal TUI
- handoff target: architect
- completion state: complete

## Checkpoint 003

- role: architect
- phase: solutioning
- workflow: architecture
- artifact created or updated: architecture
- blockers: none
- decisions: Python + Typer + Textual stack, single encrypted vault file for MVP, git backup isolated as optional integration
- handoff target: pm-dev
- completion state: complete

## Checkpoint 004

- role: pm-dev
- phase: solutioning
- workflow: stories
- artifact created or updated: stories
- blockers: choose final TUI framework and unlock-session behavior before implementation tech spec
- decisions: Epic sequence starts with vault core; backup auto-commit remains opt-in; shell support starts with PowerShell and POSIX
- handoff target: dev
- completion state: complete

## Checkpoint 005

- role: architect-dev
- phase: solutioning
- workflow: tech-spec
- artifact created or updated: tech_spec_epic1
- blockers: none
- decisions: Epic 1 will use a single encrypted vault file, local session cache, scrypt KDF, AES-GCM encryption, and Typer CLI
- handoff target: dev
- completion state: complete

## Checkpoint 006

- role: dev
- phase: implementation
- workflow: dev-story
- artifact created or updated: Epic 1 codebase and tests
- blockers: none
- decisions: session cache stores the derived vault key while unlocked; CLI slice limited to init, unlock, lock, set, get, and list
- handoff target: tea
- completion state: complete

## Checkpoint 007

- role: tea
- phase: validation
- workflow: validation
- artifact created or updated: validation_epic1
- blockers: none
- decisions: Epic 1 validation passed via automated tests and direct service verification; Epic 2 should begin with a new tech spec
- handoff target: architect-dev
- completion state: complete

## Checkpoint 008

- role: architect-dev
- phase: solutioning
- workflow: tech-spec
- artifact created or updated: tech_spec_epic2
- blockers: none
- decisions: Epic 2 includes scoped `.env` import/export, explicit preview/apply behavior, and explicit plaintext export warnings
- handoff target: dev
- completion state: complete

## Checkpoint 009

- role: dev
- phase: implementation
- workflow: dev-story
- artifact created or updated: Epic 2 code and tests
- blockers: none
- decisions: `.env` support is limited to a conservative parser; import is split into preview/apply; export requires explicit stdout or file destination
- handoff target: tea
- completion state: complete

## Checkpoint 010

- role: tea
- phase: validation
- workflow: validation
- artifact created or updated: validation_epic2
- blockers: none
- decisions: Epic 2 validation passed via automated tests and direct service verification; next work should start from Epic 3 tech spec
- handoff target: architect-dev
- completion state: complete
