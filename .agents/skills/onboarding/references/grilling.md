# Confirming the inventory

Use the `grilling` skill in grill-with-docs mode: whatever the code and documents settle, settle from them.

The inventory is grilled by file and section, the same way as greenfield: each `##` section of the `AGENTS.md` and convention skill templates is one unit, its recommendation taken from what the inventory found (or the template's recommendation where the code shows nothing). See the `<!-- onboarding -->` blocks in [templates/](../templates/).

1. Show the inventory as one table and ask the user to confirm or correct it in one pass.
2. Then ask one question at a time, only for these rows:
   - **Inconsistent**: the code does it two ways. Is one a convention and the other a mistake? A mistake becomes a `convention` finding in the review.
   - **No reason in the code**: an ADR or design decision needs a why. Offer your best reading of the evidence as the recommended answer. If the user does not know, keep it and mark the source `inferred from code`.
   - **No clear destination**: for example, a business default that could be a convention skill or an ADR.
3. Confirm the domain-skill candidates the same way.

Never ask about scope the requirement already fixed, where a file lives, which target is production when `profiles.yml` says so, or anything else a file answers.
