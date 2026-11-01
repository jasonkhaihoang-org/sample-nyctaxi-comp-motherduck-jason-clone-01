# Existing documents

| Found | Do |
| --- | --- |
| ADRs or design documents in another format or place | Leave them where they are. Put their paths and numbering in `repo-map.json` `artifact_paths`, so new ones continue the series. File format differences as `style` findings. |
| Per-piece-of-work and design documents in other places | Move each to the location `repo-map.json` `artifact_paths` declares for its class, keeping the content; update every citation in the same PR and list the moves in its description. Per-intent files are named `<date>-<normalized-title>.md` (the slug suffix only when the work had a Studio intent slug). Template differences are `style` findings, not rewrites. |

| Customer document | Class | Moves to |
| --- | --- | --- |
| Specs or tickets for a piece of work, an `intents/` folder | Requirement | `docs/requirement/` |
| Implementation plans | Plan | `docs/plans/` |
| Sign-offs or QA reports for a piece of work | Verification | `docs/verify/` |
| Profiling or sample-selection notes for a piece of work | Verification | `docs/verify/` |
| Per-pipeline docs or runbooks | Pipeline design | `docs/design/pipelines/` |
| Cross-model or subject-area design docs | Area design | `docs/design/<area>/` |
| Incident write-ups and root-cause analyses | Case record | `docs/cases/` |

| Found | What onboarding does |
| --- | --- |
| `CLAUDE.md`, `.cursor/rules`, `.github/copilot-instructions.md` or similar | Mine their conventions into the inventory. Once the convention skills hold them, reduce the file to one line pointing at `AGENTS.md`. |
| An existing `AGENTS.md` | Rewrite it as the index. Every convention it held lands in a convention skill; the PR description lists where each went. |
| dbt YAML descriptions and doc blocks | Leave them. Take `CONTEXT.md` terms from them. |
| README, CONTRIBUTING and other human documents | Leave them unchanged, including broken links. Add `notes_for_agents` in `repo-map.json` saying agents do not read them for build tasks. Broken links or stale content are `gap` findings. |
| Code comments citing decisions that have no document (`ADR 0004`) | Write the ADR only if the user confirms the decision; otherwise a `gap` finding. |
