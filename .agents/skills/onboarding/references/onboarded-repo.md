# An already onboarded repo

The repo has all of `repo-map.json`, `test-map.json` and `.agents/skills/`. This file is the whole procedure for it: it replaces the loop phases in the main skill, and it never re-captures conventions the repo already holds. It brings the two maps and the convention skills up to the current templates. Do not decide that nothing needs to change before the plan below has run: the plan says what is missing.

`test-map.json` has two sections with different readers. `modules` is the repo's own test wiring (folders to its own test commands), and CI never reads it. `ci` is the CI engine's rules over `repo-map.json` roles, which decide the checks a pull request runs; the template's copy is the engine's default. Onboarding writes both and never replaces one with the other.

Installing or repairing CI is not part of this path, and neither is the CODEOWNERS block, which `install-ci` writes. If the repo's CI looks missing or partial, say so in the final report and recommend running `install-ci` as its own request; do not run it here.

## Plan, then ask

1. Run the plan from the repository root. It writes nothing:

   ```bash
   SKILL_DIR="<this skill's directory>" \
     && python3 "$SKILL_DIR/scripts/merge_maps.py" plan --repo . --platform <platform>
   ```

   Substitute this skill's directory for `$SKILL_DIR` and the Domain's platform kind for `<platform>`. Exit 3 means the platform has no CI roles: say so and stop.

2. List `.agents/skills/` against [templates/skills/](../templates/skills/): each convention skill the repo has (kept as it is) and each it lacks (added from the template).
3. Only once the plan and the skill list are in hand, ask the user, before changing anything, in one question or two: that the repo is already onboarded and whether to proceed, and, per artifact, what onboarding keeps and what it would overwrite or add:
   - `repo-map.json`: the CI roles it adds (`add`), every existing entry it keeps, and each role whose path differs from the template (`differs_from_template`), which stays the repo's own.
   - `test-map.json`: `modules` and every other entry it keeps; the `ci` section it adds when there is none. When the repo has its own `ci` section that differs from the default, the plan's `decisions` carries a `ci` entry: ask it as its own question, with its options and the rules `only_in_repo` and `only_in_default`. A general yes to proceed never authorises an overwrite.
   - `.agents/skills/`: the skills it keeps and the skills it adds.
4. Ask every entry in `decisions` before running `apply`, in the same call as the confirmation or after it. Follow the user's answers. Never overwrite an existing entry without that confirmation. A decline at any point stops the run with nothing changed and nothing committed.

## Apply

Keep is the default: only what is missing is added, and every existing entry stays byte-identical. Run the same command with `apply` in place of `plan`, adding `--overwrite-ci` only when the user chose to overwrite the `ci` section. The script inserts the new entries into the existing text and fails when any existing entry would change, so do not edit either map by hand. Add the missing convention skills as [base-setup.md](base-setup.md) says.

Then run the map tests the repo's `test-map.json` names (`tests/test_maps.py`), and commit and push the change as one concern. The final report lists what was kept, added and overwritten per artifact, and, when the repo kept its own `ci` section, says so. When the plan found nothing to add and the user kept everything, there is nothing to commit: say so.
