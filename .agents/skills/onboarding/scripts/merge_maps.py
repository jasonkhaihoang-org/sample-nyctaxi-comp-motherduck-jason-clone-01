"""Bring an onboarded repo's two maps up to the template: the CI roles and the `ci` section.

`plan` prints, per map, what is kept, added and (with --overwrite-ci) overwritten, and writes nothing.
`apply` makes exactly that change. It inserts text into the existing files rather than re-serialising
them, so every entry already there keeps its bytes; it then re-reads both maps and fails if any
pre-existing entry's value changed.

    python3 merge_maps.py plan  --repo . --platform <platform> [--overwrite-ci]
    python3 merge_maps.py apply --repo . --platform <platform> [--overwrite-ci]

The platform's own roles come from `## Repo-map roles` in `_shared/platforms/<platform>/ci.md`.
Exit 0 on success, 2 when a map is missing or not valid JSON, 3 when the platform has no ci.md.
"""

import argparse
import json
import re
import sys
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[1] / "templates" / "repo"
PLATFORMS = Path(__file__).resolve().parents[3] / "_shared" / "platforms"
CI_ROLES = ("dbt_project", "ingestion_root", "pipeline", "source_config", "orchestration", "test_map")
ROLE_ROW = re.compile(r"^\|\s*`([a-z_]+)`\s*\|\s*`([^`]+)`\s*\|\s*$")


def platform_roles(platform_file):
    """The `## Repo-map roles` table of the platform's ci.md: role -> path."""
    text = Path(platform_file).read_text(encoding="utf-8")
    section = text.split("## Repo-map roles", 1)
    if len(section) < 2:
        raise SystemExit(f"{platform_file} has no ## Repo-map roles section")
    body = section[1].split("\n## ", 1)[0]
    return dict(m.groups() for m in map(ROLE_ROW.match, body.splitlines()) if m)


def wanted_roles(platform_file):
    template = json.loads((TEMPLATES / "repo-map.json").read_text(encoding="utf-8"))["artifact_paths"]
    roles = {role: template[role] for role in CI_ROLES}
    roles.update(platform_roles(platform_file))
    return roles


def default_ci():
    return json.loads((TEMPLATES / "test-map.json").read_text(encoding="utf-8"))["ci"]


def _value_end(text, start):
    """Index just past the JSON value starting at `start` (an object, array, string or scalar)."""
    depth, i, in_string = 0, start, False
    while i < len(text):
        c = text[i]
        if in_string:
            if c == "\\":
                i += 1
            elif c == '"':
                in_string = False
                if depth == 0:
                    return i + 1
        elif c == '"':
            in_string = True
        elif c in "{[":
            depth += 1
        elif c in "}]":
            depth -= 1
            if depth == 0:
                return i + 1
            if depth < 0:
                return i
        elif depth == 0 and c in ",\n":
            return i
        i += 1
    return i


def _top_level_key(text, key):
    """(start, end) of the value of a top-level `key`, or None."""
    depth, i, in_string, token_start = 0, 0, False, None
    while i < len(text):
        c = text[i]
        if in_string:
            if c == "\\":
                i += 1
            elif c == '"':
                in_string = False
                after = text[i + 1:].lstrip()
                if depth == 1 and text[token_start + 1:i] == key and after.startswith(":"):
                    colon = text.index(":", i)
                    start = colon + 1
                    while text[start] in " \t\r\n":
                        start += 1
                    return start, _value_end(text, start)
        elif c == '"':
            in_string, token_start = True, i
        elif c in "{[":
            depth += 1
        elif c in "}]":
            depth -= 1
        i += 1
    return None


def _newline(text):
    return "\r\n" if "\r\n" in text else "\n"


def _insert_before_close(text, close, entries, indent):
    """Insert `"k": v` entries before the object brace at `close`, after its last entry."""
    body_end = close
    while text[body_end - 1] in " \t\r\n":
        body_end -= 1
    empty = text[body_end - 1] == "{"
    newline = _newline(text)
    added = ",".join(f"{newline}{indent}{json.dumps(k)}: {v}" for k, v in entries)
    return text[:body_end] + ("" if empty else ",") + added.lstrip(",") + text[body_end:]


def _indent_of_entries(text, start, end):
    match = re.search(r"\n([ \t]+)\"", text[start:end])
    return match.group(1) if match else "  "


def _render_ci(ci, indent, newline):
    return json.dumps(ci, indent=2).replace("\n", newline + indent)


def plan(repo, platform_file, overwrite_ci):
    repo = Path(repo)
    try:
        repo_map = json.loads((repo / "repo-map.json").read_text(encoding="utf-8"))
        test_map = json.loads((repo / "test-map.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"merge_maps: cannot read the maps: {error}", file=sys.stderr)
        raise SystemExit(2) from error
    if not isinstance(repo_map, dict) or not isinstance(repo_map.get("artifact_paths"), dict) or not isinstance(test_map, dict):
        print("merge_maps: repo-map.json needs an artifact_paths object and test-map.json must be an object", file=sys.stderr)
        raise SystemExit(2)
    roles = repo_map["artifact_paths"]
    wanted = wanted_roles(platform_file)
    ci, default = test_map.get("ci"), default_ci()
    ci_action = "add" if ci is None else ("overwrite" if overwrite_ci and ci != default else "keep")
    decisions = []
    if ci is not None and ci != default:
        show = json.dumps
        decisions.append({
            "id": "ci",
            "question": "test-map.json has its own ci section, which differs from the CI engine's default. "
                        "Keep the repo's own section (recommended), or overwrite it with the default?",
            "options": ["keep (recommended)", "overwrite with the default"],
            "only_in_repo": [show(rule) for rule in ci.get("rules", []) if rule not in default["rules"]],
            "only_in_default": [show(rule) for rule in default["rules"] if rule not in ci.get("rules", [])],
        })
    return {
        "decisions": decisions,
        "repo-map.json": {
            "keep": sorted(roles),
            "add": {r: p for r, p in wanted.items() if r not in roles},
            "differs_from_template": {r: {"repo": roles[r], "template": p} for r, p in wanted.items()
                                      if r in roles and roles[r] != p},
        },
        "test-map.json": {
            "keep": sorted(k for k in test_map if k != "ci" or ci_action == "keep"),
            "ci": ci_action,
            "ci_matches_default": ci == default,
        },
    }


def _read(path):
    """The file's exact text: no newline translation, so a CRLF map stays CRLF."""
    return path.read_bytes().decode("utf-8")


def _write(path, text):
    path.write_bytes(text.encode("utf-8"))


def apply(repo, platform_file, overwrite_ci):
    repo = Path(repo)
    result = plan(repo, platform_file, overwrite_ci)
    originals = {name: _read(repo / name) for name in ("repo-map.json", "test-map.json")}
    before = {name: json.loads(text) for name, text in originals.items()}

    additions = result["repo-map.json"]["add"]
    if additions:
        path = repo / "repo-map.json"
        text = _read(path)
        start, end = _top_level_key(text, "artifact_paths")
        indent = _indent_of_entries(text, start, end)
        _write(path, _insert_before_close(text, end - 1, [(k, json.dumps(v)) for k, v in additions.items()], indent))

    action = result["test-map.json"]["ci"]
    if action != "keep":
        path = repo / "test-map.json"
        text = _read(path)
        outer = _indent_of_entries(text, 0, len(text))
        rendered = _render_ci(default_ci(), outer, _newline(text))
        if action == "add":
            close = text.rstrip().rfind("}")
            text = _insert_before_close(text, close, [("ci", rendered)], outer)
        else:
            start, end = _top_level_key(text, "ci")
            text = text[:start] + rendered + text[end:]
        _write(path, text)

    for name, old in before.items():
        new = json.loads(_read(repo / name))
        changed = [k for k in old if new.get(k) != old[k] and not (name == "repo-map.json" and k == "artifact_paths")
                   and not (name == "test-map.json" and k == "ci" and action == "overwrite")]
        if name == "repo-map.json":
            changed += [f"artifact_paths.{r}" for r, p in old.get("artifact_paths", {}).items()
                        if new["artifact_paths"].get(r) != p]
        if changed:
            for restore, text in originals.items():
                _write(repo / restore, text)
            raise SystemExit(f"merge_maps: {name} would change existing entries {changed}; both maps are restored")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("plan", "apply"))
    parser.add_argument("--repo", default=".")
    parser.add_argument("--platform", required=True, help="the Domain's platform kind")
    parser.add_argument("--overwrite-ci", action="store_true", help="replace a ci section that differs from the default")
    args = parser.parse_args(argv)
    platform_file = PLATFORMS / args.platform / "ci.md"
    if not platform_file.is_file():
        print(f"merge_maps: platform {args.platform!r} has no CI roles ({platform_file} is missing)", file=sys.stderr)
        return 3
    run = plan if args.command == "plan" else apply
    print(json.dumps(run(args.repo, platform_file, args.overwrite_ci), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
