# Dry run

Checks first: the map tests and the ADR link test pass, CI is green, and every `ADR NNNN` citation resolves.

Then pick three tasks a user of this repo would ask for:

1. Add a source like an existing one.
2. Add or change a mart model.
3. The most used domain skill, or a change to the most connected intermediate model.

For each, using only `AGENTS.md`, `repo-map.json` and `.agents/skills/`, write down:

| Task | Files read | Files changed or created | Commands |
| --- | --- | --- | --- |

Then check every entry against the repo: the paths exist, the command runs in the sandbox, and nothing the task needs is missing from the context. Do not run a build.

Each miss is a context fix before shipping, or a finding in the review. Record the table and its result in this intent's Verification, not under `docs/review/`.
