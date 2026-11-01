# Orchestration documentation — Fabric

Inspect `pipeline-content.json`, `.schedules` when present, and the `.platform` files of referenced pipeline and notebook items. The schedule is `on demand` when `.schedules` is absent.

Validate each documented item:

```bash
SKILL_DIR="<this skill's directory>" \
  && cd /workspace \
  && python3 "$SKILL_DIR/../../scripts/platforms/_family/fabric/validate-datapipeline.py" \
    orchestration/<Name>.DataPipeline --repo-root .
```
