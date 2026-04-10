#!/usr/bin/env python3
"""
reef.py — Deterministic operations engine for the Reef Claude Code plugin.

Invocation: python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py <command> [options]

All output is structured JSON to stdout. Errors go to stderr.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pyyaml is required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    ".reef", ".env", "dist", "build", ".next", ".nuxt",
    "target", "vendor",
}

REQUIRED_FRONTMATTER_FIELDS = {
    "id", "type", "title", "domain", "status", "last_verified",
    "freshness_note", "tags", "relates_to", "sources",
}

VALID_STATUSES = {"draft", "active", "deprecated"}

ARTIFACT_SUBDIRS = [
    "systems", "schemas", "apis", "processes",
    "decisions", "glossary", "contracts", "risks",
]

# Map type prefix to section name for index generation
TYPE_SECTIONS = {
    "SYS": "Systems",
    "SCH": "Schemas",
    "API": "APIs",
    "PRC": "Processes",
    "DEC": "Decisions",
    "GLO": "Glossary",
    "CON": "Contracts",
    "RSK": "Risks",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def emit(result: dict) -> None:
    """Print structured JSON to stdout and exit 0."""
    print(json.dumps(result, indent=2))
    sys.exit(0)


def fail(message: str) -> None:
    """Print error to stderr and structured JSON to stdout, exit 1."""
    print(message, file=sys.stderr)
    print(json.dumps({"status": "error", "message": message}, indent=2))
    sys.exit(1)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def find_reef_root(override: str | None = None) -> Path:
    """Walk up from cwd (or override) to find directory containing .reef/."""
    if override:
        p = Path(override).resolve()
        if (p / ".reef").is_dir():
            return p
        fail(f"No .reef/ directory found at {p}")

    current = Path.cwd().resolve()
    while True:
        if (current / ".reef").is_dir():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    fail("Not inside a reef — no .reef/ directory found in any parent. Use --reef <path>.")
    return Path()  # unreachable, satisfies type checker


def read_json(path: Path) -> dict | list:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        fail(f"Cannot read {path}: {e}")
        return {}


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def is_binary(filepath: Path) -> bool:
    """Check first 8192 bytes for null bytes."""
    try:
        chunk = filepath.read_bytes()[:8192]
        return b"\x00" in chunk
    except (OSError, PermissionError):
        return True


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def parse_frontmatter(filepath: Path) -> dict | None:
    """Parse YAML frontmatter between --- delimiters. Returns None if not found."""
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception:
        return None

    if not text.startswith("---"):
        return None

    end = text.find("---", 3)
    if end == -1:
        return None

    raw = text[3:end].strip()
    try:
        return yaml.safe_load(raw) or {}
    except yaml.YAMLError:
        return None


def get_artifact_body(filepath: Path) -> str:
    """Return the markdown body after frontmatter."""
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception:
        return ""

    if not text.startswith("---"):
        return text

    end = text.find("---", 3)
    if end == -1:
        return text
    return text[end + 3:].strip()


def collect_artifacts(reef: Path) -> list[tuple[Path, dict]]:
    """Collect all artifact files with valid frontmatter from artifacts/ subdirs."""
    results = []
    artifacts_dir = reef / "artifacts"
    if not artifacts_dir.is_dir():
        return results

    for subdir in ARTIFACT_SUBDIRS:
        sd = artifacts_dir / subdir
        if not sd.is_dir():
            continue
        for f in sd.iterdir():
            if f.suffix == ".md" and f.is_file():
                fm = parse_frontmatter(f)
                if fm:
                    results.append((f, fm))
    return results


# ---------------------------------------------------------------------------
# Subcommand: init
# ---------------------------------------------------------------------------


def cmd_init(args) -> None:
    root = Path(args.path).resolve()

    if (root / ".reef").exists():
        fail(f"Reef already exists at {root}")

    # Create directory tree
    root.mkdir(parents=True, exist_ok=True)

    for subdir in ARTIFACT_SUBDIRS:
        (root / "artifacts" / subdir).mkdir(parents=True, exist_ok=True)

    (root / "sources" / "registries").mkdir(parents=True, exist_ok=True)
    (root / "sources" / "raw").mkdir(parents=True, exist_ok=True)

    dot_reef = root / ".reef"
    dot_reef.mkdir(parents=True, exist_ok=True)
    (dot_reef / "artifact-state").mkdir(parents=True, exist_ok=True)
    (dot_reef / "sessions").mkdir(parents=True, exist_ok=True)

    # index.md
    (root / "index.md").write_text(
        "---\ngenerated: true\n---\n"
        f"# Reef Index — {root.name}\n\n"
        "> Auto-generated catalog. Do not edit manually.\n\n"
        + "".join(f"## {name}\n\n" for name in TYPE_SECTIONS.values()),
        encoding="utf-8",
    )

    # log.md
    (root / "log.md").write_text(
        "# Reef Evolution Log\n\n",
        encoding="utf-8",
    )

    # project.json
    write_json(dot_reef / "project.json", {
        "name": root.name,
        "sources": [],
        "created": now_iso(),
        "version": "1.0.0",
    })

    # source-index.json
    write_json(dot_reef / "source-index.json", {})

    # source-artifact-map.json
    write_json(dot_reef / "source-artifact-map.json", {})

    # questions.json
    write_json(dot_reef / "questions.json", [])

    # .gitignore
    (dot_reef / ".gitignore").write_text(
        "sessions/\n",
        encoding="utf-8",
    )

    emit({"status": "ok", "path": str(root), "name": root.name})


# ---------------------------------------------------------------------------
# Subcommand: index
# ---------------------------------------------------------------------------


def cmd_index(args) -> None:
    reef = find_reef_root(args.reef)
    project = read_json(reef / ".reef" / "project.json")

    sources_cfg = project.get("sources", [])
    if not sources_cfg:
        emit({"status": "ok", "sources": {}})

    result_sources = {}
    index_data = {"indexed_at": now_iso(), "sources": {}}

    for src in sources_cfg:
        # Each source can be a string path or a dict with name/path
        if isinstance(src, dict):
            src_name = src.get("name", Path(src["path"]).name)
            src_path = Path(src["path"]).resolve()
        else:
            src_path = Path(src).resolve()
            src_name = src_path.name

        if not src_path.is_dir():
            result_sources[src_name] = {"files_indexed": 0, "skipped": 0}
            index_data["sources"][src_name] = {"path": str(src_path), "files": {}}
            continue

        files_indexed = 0
        skipped = 0
        files_map = {}

        for dirpath, dirnames, filenames in os.walk(src_path):
            # Prune skip dirs in-place
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

            for fname in filenames:
                fpath = Path(dirpath) / fname

                if is_binary(fpath):
                    skipped += 1
                    continue

                try:
                    rel = fpath.relative_to(src_path)
                    stat = fpath.stat()
                    files_map[str(rel)] = {
                        "hash": sha256_file(fpath),
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(
                            stat.st_mtime, tz=timezone.utc
                        ).isoformat(),
                    }
                    files_indexed += 1
                except Exception:
                    skipped += 1

        index_data["sources"][src_name] = {
            "path": str(src_path),
            "files": files_map,
        }
        result_sources[src_name] = {
            "files_indexed": files_indexed,
            "skipped": skipped,
        }

    write_json(reef / ".reef" / "source-index.json", index_data)
    emit({"status": "ok", "sources": result_sources})


# ---------------------------------------------------------------------------
# Subcommand: snapshot
# ---------------------------------------------------------------------------


def cmd_snapshot(args) -> None:
    reef = find_reef_root(args.reef)
    artifact_id = args.artifact_id

    # Find the artifact file
    artifact_file = None
    for subdir in ARTIFACT_SUBDIRS:
        candidate = reef / "artifacts" / subdir / f"{artifact_id}.md"
        if candidate.is_file():
            artifact_file = candidate
            break

    if artifact_file is None:
        fail(f"Artifact not found: {artifact_id}")

    fm = parse_frontmatter(artifact_file)
    if fm is None:
        fail(f"Cannot parse frontmatter for {artifact_id}")

    raw_sources = fm.get("sources", []) or []
    # sources can be strings or dicts with a "ref" field
    source_refs = []
    for s in raw_sources:
        if isinstance(s, dict):
            r = s.get("ref")
            if r:
                source_refs.append(r)
        elif isinstance(s, str):
            source_refs.append(s)
    source_index = read_json(reef / ".reef" / "source-index.json")

    snapshot_sources = {}
    for ref in source_refs:
        # ref can be "source-name:relative/path" or just "relative/path"
        if ":" in ref:
            src_name, rel_path = ref.split(":", 1)
        else:
            # Try to find in any source
            src_name = None
            rel_path = ref
            for sn, sdata in source_index.get("sources", {}).items():
                if rel_path in sdata.get("files", {}):
                    src_name = sn
                    break
            if src_name is None:
                snapshot_sources[ref] = {"hash": None, "modified": None}
                continue

        sources_data = source_index.get("sources", {})
        src_data = sources_data.get(src_name, {})
        file_entry = src_data.get("files", {}).get(rel_path)

        if file_entry:
            snapshot_sources[ref] = {
                "hash": file_entry["hash"],
                "modified": file_entry["modified"],
            }
        else:
            snapshot_sources[ref] = {"hash": None, "modified": None}

    snap = {
        "artifact_id": artifact_id,
        "snapshot_at": now_iso(),
        "sources": snapshot_sources,
    }

    write_json(reef / ".reef" / "artifact-state" / f"{artifact_id}.json", snap)
    emit({
        "status": "ok",
        "artifact_id": artifact_id,
        "sources_captured": len([s for s in snapshot_sources.values() if s["hash"]]),
    })


# ---------------------------------------------------------------------------
# Subcommand: diff
# ---------------------------------------------------------------------------


def cmd_diff(args) -> None:
    reef = find_reef_root(args.reef)
    source_index = read_json(reef / ".reef" / "source-index.json")
    state_dir = reef / ".reef" / "artifact-state"

    # Load all artifact snapshots
    snapshots = {}
    if state_dir.is_dir():
        for f in state_dir.iterdir():
            if f.suffix == ".json":
                snap = read_json(f)
                snapshots[snap["artifact_id"]] = snap

    # Build current file lookup: ref -> {hash, modified}
    current_files = {}  # "source:relpath" -> file entry
    for src_name, src_data in source_index.get("sources", {}).items():
        for rel_path, fentry in src_data.get("files", {}).items():
            current_files[f"{src_name}:{rel_path}"] = fentry

    # Compare each artifact snapshot against current index
    source_stats = {}  # source_name -> {new, updated, deleted, unchanged}
    affected_artifacts = set()
    details = []

    for art_id, snap in snapshots.items():
        for ref, old_entry in snap.get("sources", {}).items():
            # Determine source name
            if ":" in ref:
                src_name = ref.split(":", 1)[0]
            else:
                src_name = "_unknown"

            if src_name not in source_stats:
                source_stats[src_name] = {"new": 0, "updated": 0, "deleted": 0, "unchanged": 0}

            current = current_files.get(ref)
            old_hash = old_entry.get("hash")

            if old_hash is None and current is not None:
                classification = "new"
            elif current is None:
                classification = "deleted"
            elif current["hash"] != old_hash:
                classification = "updated"
            else:
                classification = "unchanged"

            source_stats[src_name][classification] += 1

            if classification != "unchanged":
                affected_artifacts.add(art_id)
                detail = {
                    "file": ref.split(":", 1)[-1] if ":" in ref else ref,
                    "source": src_name,
                    "classification": classification,
                    "artifacts": [art_id],
                }
                if old_hash:
                    detail["old_hash"] = old_hash
                if current:
                    detail["new_hash"] = current["hash"]
                details.append(detail)

    # Check for new files in index not in any snapshot
    all_snapped_refs = set()
    for snap in snapshots.values():
        all_snapped_refs.update(snap.get("sources", {}).keys())

    for ref in current_files:
        if ref not in all_snapped_refs:
            src_name = ref.split(":", 1)[0] if ":" in ref else "_unknown"
            if src_name not in source_stats:
                source_stats[src_name] = {"new": 0, "updated": 0, "deleted": 0, "unchanged": 0}
            source_stats[src_name]["new"] += 1

    emit({
        "status": "ok",
        "sources": source_stats,
        "affected_artifacts": sorted(affected_artifacts),
        "details": details,
    })


# ---------------------------------------------------------------------------
# Subcommand: lint
# ---------------------------------------------------------------------------


def cmd_lint(args) -> None:
    reef = find_reef_root(args.reef)
    artifacts = collect_artifacts(reef)
    source_index = read_json(reef / ".reef" / "source-index.json")

    errors = []
    warnings = []
    infos = []

    # Build lookup: artifact_id -> (path, frontmatter)
    art_map = {}
    for path, fm in artifacts:
        aid = fm.get("id", path.stem)
        art_map[aid] = (path, fm)

    # Build set of all relates_to targets pointing at each artifact
    incoming = {}  # artifact_id -> set of source artifact ids
    for aid, (_, fm) in art_map.items():
        for target in (fm.get("relates_to") or []):
            incoming.setdefault(target, set()).add(aid)

    # Build current file set for source existence check
    existing_source_files = set()
    for src_name, src_data in source_index.get("sources", {}).items():
        for rel_path in src_data.get("files", {}):
            existing_source_files.add(f"{src_name}:{rel_path}")
            existing_source_files.add(rel_path)

    # Load snapshots for freshness check
    state_dir = reef / ".reef" / "artifact-state"
    snapshots = {}
    if state_dir.is_dir():
        for f in state_dir.iterdir():
            if f.suffix == ".json":
                snap = read_json(f)
                snapshots[snap["artifact_id"]] = snap

    # Build current files index
    current_files = {}
    for src_name, src_data in source_index.get("sources", {}).items():
        for rel_path, fentry in src_data.get("files", {}).items():
            current_files[f"{src_name}:{rel_path}"] = fentry

    for aid, (apath, fm) in art_map.items():
        # Check 4: Frontmatter schema
        missing = REQUIRED_FRONTMATTER_FIELDS - set(fm.keys())
        for field in sorted(missing):
            errors.append({
                "artifact": aid,
                "check": "schema",
                "severity": "error",
                "message": f"Missing required field: {field}",
            })

        status_val = fm.get("status")
        if status_val and status_val not in VALID_STATUSES:
            errors.append({
                "artifact": aid,
                "check": "schema",
                "severity": "error",
                "message": f"Invalid status '{status_val}', must be one of: {', '.join(sorted(VALID_STATUSES))}",
            })

        # id matches filename
        if fm.get("id") and fm["id"] != apath.stem:
            errors.append({
                "artifact": aid,
                "check": "schema",
                "severity": "error",
                "message": f"Frontmatter id '{fm['id']}' does not match filename '{apath.stem}'",
            })

        # Check 1: Orphan detection (no incoming relates_to, except SYS- roots)
        if aid not in incoming and not aid.startswith("SYS-"):
            warnings.append({
                "artifact": aid,
                "check": "orphan",
                "severity": "warning",
                "message": "No other artifact references this one via relates_to",
            })

        # Check 2: Dangling references
        for target in (fm.get("relates_to") or []):
            if target not in art_map:
                errors.append({
                    "artifact": aid,
                    "check": "dangling_reference",
                    "severity": "error",
                    "message": f"relates_to target '{target}' does not resolve to an existing artifact",
                })

        # Check 3: Source file existence
        for src_entry in (fm.get("sources") or []):
            src_ref = src_entry.get("ref", "") if isinstance(src_entry, dict) else str(src_entry)
            if not src_ref:
                continue
            if src_ref not in existing_source_files:
                errors.append({
                    "artifact": aid,
                    "check": "source_existence",
                    "severity": "error",
                    "message": f"Source ref '{src_ref}' not found in source index",
                })

        # Check 5: Key Facts without source links
        body = get_artifact_body(apath)
        if "## Key Facts" in body:
            # Extract lines in Key Facts section
            kf_start = body.index("## Key Facts")
            kf_section = body[kf_start:]
            # Find next ## heading
            next_heading = kf_section.find("\n## ", 1)
            if next_heading != -1:
                kf_section = kf_section[:next_heading]

            # Check for facts (lines starting with -) that lack source citations (→ syntax)
            for line in kf_section.split("\n"):
                stripped = line.strip()
                if stripped.startswith("- ") and "→" not in stripped:
                    warnings.append({
                        "artifact": aid,
                        "check": "key_facts_sources",
                        "severity": "warning",
                        "message": f"Key fact without source citation: {stripped[:80]}",
                    })

        # Check 6: Wikilink/frontmatter sync
        relates_to_set = set(fm.get("relates_to") or [])
        wikilinks = set()
        if "## Related" in body:
            rel_start = body.index("## Related")
            rel_section = body[rel_start:]
            next_heading = rel_section.find("\n## ", 1)
            if next_heading != -1:
                rel_section = rel_section[:next_heading]

            wikilinks = set(re.findall(r"\[\[([^\]]+)\]\]", rel_section))

        # Wikilinks in Related that aren't in relates_to
        for wl in wikilinks:
            if wl not in relates_to_set:
                warnings.append({
                    "artifact": aid,
                    "check": "wikilink_sync",
                    "severity": "warning",
                    "message": f"Wikilink [[{wl}]] in ## Related not in relates_to frontmatter",
                })

        # relates_to entries not in Related wikilinks
        for rt in relates_to_set:
            if wikilinks and rt not in wikilinks:
                warnings.append({
                    "artifact": aid,
                    "check": "wikilink_sync",
                    "severity": "warning",
                    "message": f"relates_to '{rt}' not found as wikilink in ## Related section",
                })

        # Check 7: Freshness — sources changed since last snapshot
        if aid in snapshots:
            snap = snapshots[aid]
            changed_count = 0
            for ref, old_entry in snap.get("sources", {}).items():
                current = current_files.get(ref)
                old_hash = old_entry.get("hash")
                if current is None and old_hash is not None:
                    changed_count += 1
                elif current and old_hash and current["hash"] != old_hash:
                    changed_count += 1
            if changed_count > 0:
                warnings.append({
                    "artifact": aid,
                    "check": "freshness",
                    "severity": "warning",
                    "message": f"{changed_count} source file(s) changed since last snapshot",
                })

    emit({
        "status": "ok",
        "artifacts_checked": len(artifacts),
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "errors": len(errors),
            "warnings": len(warnings),
            "info": len(infos),
        },
    })


# ---------------------------------------------------------------------------
# Subcommand: rebuild-map
# ---------------------------------------------------------------------------


def cmd_rebuild_map(args) -> None:
    reef = find_reef_root(args.reef)
    artifacts = collect_artifacts(reef)

    mapping = {}  # source_ref -> [artifact_ids]
    for _, fm in artifacts:
        aid = fm.get("id", "")
        for src_entry in (fm.get("sources") or []):
            # sources can be strings or dicts with a "ref" field
            if isinstance(src_entry, dict):
                src_ref = src_entry.get("ref", "")
            else:
                src_ref = str(src_entry)
            if not src_ref:
                continue
            mapping.setdefault(src_ref, [])
            if aid not in mapping[src_ref]:
                mapping[src_ref].append(aid)

    write_json(reef / ".reef" / "source-artifact-map.json", mapping)
    emit({"status": "ok", "mappings": len(mapping)})


# ---------------------------------------------------------------------------
# Subcommand: rebuild-index
# ---------------------------------------------------------------------------


def cmd_rebuild_index(args) -> None:
    reef = find_reef_root(args.reef)
    project = read_json(reef / ".reef" / "project.json")
    artifacts = collect_artifacts(reef)

    # Group by type prefix
    grouped = {}
    for _, fm in artifacts:
        aid = fm.get("id", "")
        prefix = aid.split("-")[0] if "-" in aid else aid
        grouped.setdefault(prefix, []).append(fm)

    # Sort each group by id
    for prefix in grouped:
        grouped[prefix].sort(key=lambda f: f.get("id", ""))

    lines = [
        "---",
        "generated: true",
        "---",
        f"# Reef Index — {project.get('name', 'unknown')}",
        "",
        "> Auto-generated catalog. Do not edit manually.",
        "",
    ]

    total = 0
    for prefix, section_name in TYPE_SECTIONS.items():
        lines.append(f"## {section_name}")
        arts = grouped.get(prefix, [])
        if arts:
            for fm in arts:
                aid = fm.get("id", "")
                title = fm.get("title", "")
                status = fm.get("status", "")
                lines.append(f"- [[{aid}]] — {title} ({status})")
                total += 1
        lines.append("")

    (reef / "index.md").write_text("\n".join(lines), encoding="utf-8")
    emit({"status": "ok", "artifacts_indexed": total})


# ---------------------------------------------------------------------------
# Subcommand: log
# ---------------------------------------------------------------------------


def cmd_log(args) -> None:
    reef = find_reef_root(args.reef)
    log_path = reef / "log.md"

    timestamp = now_iso()
    entry = f"**{timestamp}** — {args.message}\n\n"

    if log_path.is_file():
        content = log_path.read_text(encoding="utf-8")
        content += entry
    else:
        content = "# Reef Evolution Log\n\n" + entry

    log_path.write_text(content, encoding="utf-8")
    emit({"status": "ok"})


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="reef",
        description="Deterministic operations engine for the Reef Claude Code plugin.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Initialize a new reef")
    p_init.add_argument("path", help="Path to create the reef at")
    p_init.set_defaults(func=cmd_init)

    # index
    p_index = sub.add_parser("index", help="Index all source files")
    p_index.add_argument("--reef", default=None, help="Path to reef root")
    p_index.set_defaults(func=cmd_index)

    # snapshot
    p_snap = sub.add_parser("snapshot", help="Snapshot source state for an artifact")
    p_snap.add_argument("artifact_id", help="Artifact ID to snapshot")
    p_snap.add_argument("--reef", default=None, help="Path to reef root")
    p_snap.set_defaults(func=cmd_snapshot)

    # diff
    p_diff = sub.add_parser("diff", help="Diff current sources against artifact snapshots")
    p_diff.add_argument("--reef", default=None, help="Path to reef root")
    p_diff.set_defaults(func=cmd_diff)

    # lint
    p_lint = sub.add_parser("lint", help="Run mechanical checks on all artifacts")
    p_lint.add_argument("--reef", default=None, help="Path to reef root")
    p_lint.set_defaults(func=cmd_lint)

    # rebuild-map
    p_rmap = sub.add_parser("rebuild-map", help="Rebuild source-artifact map")
    p_rmap.add_argument("--reef", default=None, help="Path to reef root")
    p_rmap.set_defaults(func=cmd_rebuild_map)

    # rebuild-index
    p_ridx = sub.add_parser("rebuild-index", help="Rebuild index.md catalog")
    p_ridx.add_argument("--reef", default=None, help="Path to reef root")
    p_ridx.set_defaults(func=cmd_rebuild_index)

    # log
    p_log = sub.add_parser("log", help="Append entry to evolution log")
    p_log.add_argument("message", help="Log message")
    p_log.add_argument("--reef", default=None, help="Path to reef root")
    p_log.set_defaults(func=cmd_log)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
