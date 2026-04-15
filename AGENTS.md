# AGENTS.md

## RUFLO_BMAD_MODE

- enabled: true
- track: bmad-method
- modules: BMad Core, BMad Method, BMad Builder, Creative Intelligence Suite
- preferred_roles: analyst, pm, architect, dev, tea, tech-writer, bmad-master
- artifact_flow: overview, brief, prd, architecture, tech_spec, stories, implementation_proof, validation, release_notes

## RUFLO_BMAD_V6

- enabled: true
- overlay_mode: ruflo-managed
- migration_required_on_detect: true
- compatibility_mode: false
- project_mode: upstream-bmad-v6
- enabled_modules: core, bmm, bmb, cis
- optional_modules: game-dev
- install_config: `RUFLO_HOME/.bmad/install-config.json`
- install_entrypoints: install, upgrade, force-upgrade
- workflow_surface: workflow-init, brief, prd, architecture, tech-spec, dev-story, validation, party-mode, bmad-builder, bmad-cis
- project_modes: legacy-ruflo-bmad, upstream-bmad-v6, hybrid-bmad, non-bmad

Required BMAD v6 behavior when enabled:

- Always restore BMAD project state before substantial work.
- Always check BMAD migration status before normal BMAD execution.
- If BMAD is detected and migration status is `required`, run BMAD v6 migration preflight first.
- Use the Ruflo-managed BMAD v6 overlay, not the raw upstream installer/runtime model.
- Use only the installed and enabled BMAD modules as the active capability surface.
- Persist BMAD v6 state in the ledger:
  - `bmadVersion`
  - `bmadProjectMode`
  - `migrationStatus`
  - `migrationSource`
  - `enabledModules`
  - `migrationPreflight`
  - `migrationHistory`
  - `compatibilityMode`
  - `canonicalArtifacts`
  - `upstreamMarkers`
- Preserve legacy artifact paths behind compatibility mode unless a later explicit normalization step changes them.
- Do not assume full upstream BMAD v6 workflow parity unless the synced pack actually includes those workflows.
- Surface BMAD v6 migration and module state in dashboard, ledger, and summaries when relevant.

## ARGUS_LIFECYCLE

- ARGUS is the repo-attached verification kernel for this workspace and any repo that opts into the same contract.
- Treat `.argus/` as generated, optional, and regenerable decision metadata, not as source of truth.
- On repo hydration, bootstrap, upgrade, or when repo structure changes materially, regenerate ARGUS metadata instead of leaving stale files in place.
- Keep ARGUS subordinate to Ruflo orchestration and BMAD workflow authority.
- Use ARGUS outputs to enrich validation, graph retrieval, ownership awareness, and risk scoring, but do not let ARGUS own phase control or acceptance authority.
- When a repo grows, ARGUS should grow with it by refreshing graph, checks, docs maps, scripts maps, workspace maps, and contracts maps.
- For new repos, ensure the bootstrap/template path seeds this contract so ARGUS starts active instead of requiring a manual add-on.
- When coding, ARGUS should be used as the safety layer:
  - inspect graph and ownership signals first
  - make the smallest safe edit
  - run ARGUS validation on the candidate
  - repair failed checks before handoff
  - use it especially for public interfaces, schemas, migrations, shared modules, generated artifacts, and CI changes

## BMAD_EXECUTION_CONTRACT

For this project, BMAD is the mandatory workflow layer on top of Ruflo.

Required behavior:

- Always restore BMAD project state before any substantial work.
- Always begin by reporting:
  - current phase
  - current role
  - next role
  - active workflow
  - blockers
  - open decisions
  - required next artifact
- If `RUFLO_BMAD_V6.enabled: true`, also report:
  - `bmadVersion`
  - `bmadProjectMode`
  - `migrationStatus`
  - enabled modules
  - whether compatibility mode is active
- Work spec-first, not code-first.
- Prefer this order every time:
  - understand the goal
  - confirm the active BMAD phase
  - if BMAD v6 is enabled, confirm migration state and enabled module surface
  - produce or update the required artifact
  - write a checkpoint
  - hand off to the next role
- After every substantial step, write a BMAD checkpoint.
- Each checkpoint must record:
  - role
  - phase
  - workflow
  - artifact created or updated
  - blockers
  - decisions
  - handoff target
  - completion state
- Write a checkpoint whenever:
  - a new artifact is created
  - an artifact changes meaningfully
  - the active phase changes
  - the active role changes
  - a blocker is discovered or cleared
  - a key decision is made
  - work is handed off
  - a milestone is completed
- Do not claim completion from filenames alone.
- Do not skip to implementation because code feels obvious.
- Do not move forward if the current BMAD gate is not satisfied.
- Do not treat BMAD as role flavor text only; use it as the real operating model.
- Always verify and validate each completed epic or story before marking it complete or handing it off.

Phase gates:

- analysis -> planning requires brief or overview
- planning -> solutioning requires prd
- solutioning -> implementation requires architecture or tech_spec
- implementation -> done requires validation

Definition of done:

- validation exists
- final checkpoint exists
- next role is `complete`

## BMAD_SUPREME_MODE

For important projects, maximize BMAD usage:

- Always use the full BMAD track unless there is a clear reason to use a quick flow.
- Prefer explicit role handoffs instead of one role doing everything implicitly.
- Keep artifact provenance accurate so every important artifact shows who created it and when.
- Treat blockers and open decisions as first-class project state.
- Use Builder capabilities for custom modules, workflows, or reusable packs.
- Use CIS capabilities for brainstorming, design thinking, storytelling, innovation strategy, and structured problem solving when they improve the result.
- Treat the dashboard and checkpoints as proof of the work, not decoration added afterward.

If `RUFLO_BMAD_V6.enabled: true`:

- Prefer the BMAD v6 overlay workflow surface before inventing ad hoc flow names.
- Respect enabled-module boundaries when choosing roles, workflows, and artifacts.
- Prefer migration-aware compatibility mappings over forced file renames.
- Keep BMAD v6 status visible in summaries for medium and large tasks.

## RUFLO_MANDATORY_POLICY

- Use Ruflo MCP for task routing/orchestration first whenever `mcp__ruflo__*` tools are available.
- Keep Ruflo as the default orchestration path for code, analysis, and planning.
- If Ruflo MCP is unavailable in a session, report it explicitly and continue with local tools.

## RUFLO_LSRA_POLICY

- For medium/large tasks, execute `learn -> store -> recall -> apply`.
- Store learned items in Ruflo memory namespaces: `knowledge`, `learnings`, `skills` as applicable.
- Recall from those namespaces before implementation and apply recalled signal in the work.
- Mark task incomplete if LSRA evidence is missing.

If `RUFLO_BMAD_V6.enabled: true`:

- Store BMAD v6 migration, module, workflow, and artifact learnings in Ruflo memory.
- Recall BMAD v6 capability and migration context before changing workflow behavior or artifact expectations.
- Reference the applied BMAD v6 signal in the task summary.

## RUFLO_USAGE_MAXIMIZER

- Route every non-trivial task with a Ruflo routing/hook call first.
- Prefer parallel Ruflo/tool operations where safe to reduce latency.
- Use skills deliberately: detect relevant skills, invoke them, and cite usage in output.
- Persist meaningful findings in Ruflo memory and recall them before implementation.
- Include explicit Ruflo evidence in task summaries:
  - route
  - store
  - recall
  - applied file path

If `RUFLO_BMAD_V6.enabled: true`:

- Maximize use of the Ruflo-managed BMAD v6 overlay before falling back to legacy BMAD behavior.
- Prefer module-aware execution:
  - `core` for baseline BMAD coordination
  - `bmm` for delivery workflow and phase progression
  - `bmb` for builder-style reusable packs and workflow extension
  - `cis` for ideation, structured problem solving, and narrative work
  - `game-dev` only when enabled
- Prefer dashboard-visible, ledger-backed BMAD state over implicit workflow assumptions.
- When evaluating capabilities, distinguish clearly between:
  - installed BMAD v6 overlay behavior
  - legacy BMAD compatibility behavior
  - not-yet-implemented upstream BMAD v6 parity
