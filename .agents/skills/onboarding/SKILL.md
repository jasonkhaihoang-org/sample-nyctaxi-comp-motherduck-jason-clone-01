---
name: onboarding
description: "Use when the user asks to onboard this repository into a Vibedata domain, or to bring an onboarded repo's maps up to date for CI: an empty repo, an existing dbt and dlt repo, or an already onboarded repo (it has repo-map.json, test-map.json and .agents/skills/), which it changes only after the user confirms. Do not use for adding sources or models or for any other build task."
user-invocable: true
triggers: [onboard this repo, onboard into vibedata, onboard into a vibedata domain]
---

# Onboarding

Onboarding is an intent kind. It captures what the repo already does, so later intents can work in it, and files everything that should change for triage. It ships context, not code.

## When it applies

Decide at the requirement step, from the repo and the Domain database:

| Repo | Domain database | Path |
| --- | --- | --- |
| Empty | Empty | Greenfield: [greenfield.md](references/greenfield.md) |
| Has dbt or dlt code | Has data | Brownfield: the rest of this skill |
| Has dbt or dlt code | Empty | Brownfield, loading the Domain first: [base-setup.md](references/base-setup.md) (Empty Domain database) |
| Empty | Has data | Not supported yet: say so and stop. A migration assessment of an existing warehouse is future work |
| Already onboarded: has all of `repo-map.json`, `test-map.json` and `.agents/skills/` | Any | Follow [onboarded-repo.md](references/onboarded-repo.md) in place of the loop phases below. It first runs a read-only plan (`scripts/merge_maps.py`), then says the repo is already onboarded and asks the user to confirm, with the plan's per-artifact list and decisions, before changing anything; on a decline, stop and change nothing |

Check for an onboarded repo first, whoever triggered onboarding: the user or another skill.

## The two stages

1. **This intent**: capture conventions, write the context, file the onboarding review, ship one PR.
2. **Later intents**: each review finding an engineer picks up is a normal intent (requirement, design, build, verify, ship). An intent that changes code compares output before and after in its own session.

So during onboarding you change no model, pipeline or human document. A problem you find goes in the review, even when the fix is one line.

The general rule behind that list: **any change that needs code, configuration, a file edit or a data fix is a review finding, never an onboarding edit** — one line or many, in any file. Onboarding's deliverable is context (the maps, the skills, the documents) plus the review; a fix is a later intent with its own requirement, design and verification. If you catch yourself reaching for the editor to correct something you found, write `R-n` instead.

Two things are not edits under this rule: the base-setup changes `references/base-setup.md` lists (onboarding owns those, and applies only what is on that list), and build output under gitignored paths such as `transformation/target/` or `dbt_packages/`. Anything outside both is a finding. The only other changes are the base setup in [base-setup.md](references/base-setup.md): two `dbt_project.yml` lines the sandbox build needs, and files added where the repo has none.

## Loop phases

| Phase | Work |
| --- | --- |
| Requirement | Scope: which dbt projects and dlt pipelines. The deliverable is the context and the review. |
| Design | Discover the repo (dbt project, dlt pipelines, profiles, CI, existing documents). Before any load or build, perform the [inherited-view check](references/base-setup.md#inherited-views), then run the base commands on the sandbox `dev` target. The runtime provides that profile; the repo's own `profiles.yml` targets are for local and CI use, so do not ask which target the sandbox uses. Then build the inventory: [inventory.md](references/inventory.md) — including the rules hiding in code (thresholds, population filters, and comments that explain why), not only the structure. Confirm it: [grilling.md](references/grilling.md). Find domain-skill candidates: [domain-skills.md](references/domain-skills.md). |
| Build | Write `repo-map.json` (every CI role, with the platform's from `## Repo-map roles` in `../../_shared/platforms/<platform>/ci.md`), `test-map.json` (its `modules` and the template's `ci` section, the CI engine's default rules), the map tests, the `AGENTS.md` index and `.agents/skills/` from the confirmed inventory, starting from [templates/](templates/), plus the base setup files and base convention skills in base-setup.md. Write confirmed domain skills under `.agents/skills/`. `domain-modeling` writes `CONTEXT.md` and the ADRs for decisions already in the code. Write the ontology from that confirmed vocabulary with the `ontology` skill, always: declare `ontology/` in `repo-map.json` and its module in `test-map.json`, and write a mapping only for an Ossie document that exists (so a repo with no `gold` `marts` gets the ontology and no mapping, and says so). Write design records as the `designing` skill and `.agents/skills/design-records/SKILL.md` say, only where a model or pipeline makes a decision its code does not explain. A `D-NN` line is a choice plus its reason; a line that only says what the code does is not a decision. Handle existing documents: [existing-docs.md](references/existing-docs.md). Declare `docs/review/`, `docs/proposal/` and — when the repo has `gold` `marts` — `logical-model/` in `repo-map.json` and its module in `test-map.json`, and write the canonical semantic model with the `semantic-model` skill, reviewed by `validating-semantic-model`; base-setup.md says what those skills are and where they come from. Write the contracts with the `data-contract` skill: declare `contracts/` in `repo-map.json` as `artifact_paths.data_contract` and as a module, and that module in `test-map.json`, declare `data_platform` (the platform kind the Domain runs on) and, where an Ossie document exists, `gold_layers`, seed `data-contract` and `validating-data-contract` with their scripts and the vendored schema, rebuild the warehouse with `--full-refresh`, run `reverse` with no flag — it leaves a contract the repo already has alone, and `--force` is only for a deliberate rewrite — and write the review artifact of type `contracts` from its findings. The contracts are partial until those findings are triaged: say so in that artifact and the PR description. base-setup.md says where the two skills come from, how the loader-column boundary is derived, and the two questions onboarding may not answer. Run `install-ci`. Run `reviewing` with type `onboarding`, including the checks in base-setup.md. |
| Verify | Base commands, map tests in the sandbox, CI, ADR citations, then the dry run: [dry-run.md](references/dry-run.md). |
| Ship | One PR. The description lists where each existing convention went, and recommends a trial intent after merge: a standard prompt, with its trajectory reviewed. |

## Where things go

| Thing found | Destination |
| --- | --- |
| A location or identity a script can check | `repo-map.json` |
| A must or never for every change of a kind | A convention skill in `.agents/skills/` |
| A multi-step procedure only this repo has, confirmed by the user | A procedure (domain) skill in `.agents/skills/` |
| A decision with a reason (why this grain, this filter, this key) | ADR |
| A business term | `CONTEXT.md` |
| A concept the vocabulary names, with identity | The ontology, mapped to the Ossie documents that carry it; unmapped and reported where none does |
| A decision one model or pipeline makes that its code does not explain | That model's design record |
| Anything that should change | Onboarding review finding |

## Common mistakes

| Mistake | Instead |
| --- | --- |
| Design record lists inputs, tests, columns, SQL, or decisions that only describe the code ("vendor resolved the same way", "key is an md5 of the flags") | Grain, `D-NN` decisions with their source, rejected alternatives, consumers, history. Figures and check results go in a verification file, never the record. No record when there is nothing beyond the code. |
| Conventions written into `AGENTS.md` | `AGENTS.md` is an index; conventions go to convention skills. |
| Editing README or CONTRIBUTING, or linking agents to them | Leave human documents alone. Tell agents not to read them. |
| Fixing a tracked generated file, a broken config path or a lint setting now | A review finding. |
| Treating a successful sandbox rebuild as proof the uploaded database works | Preserve the inherited-view check before rebuilding; the Domain database remains unchanged and later Intents inherit its views. |
| Asking the user what the code already answers | Infer, show the inventory, ask only the three kinds of question in grilling.md. |
| An ADR rationale you made up | Write the decision, mark the reason `inferred from code`, and file it for confirmation. |
