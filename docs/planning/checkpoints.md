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
