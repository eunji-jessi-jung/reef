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
    "decisions", "glossary", "contracts", "risks", "patterns",
]

# Map type prefix to section name for index generation
TYPE_SECTIONS = {
    "SYS": "Systems",
    "SCH": "Schemas",
    "API": "APIs",
    "PROC": "Processes",
    "DEC": "Decisions",
    "GLOSSARY": "Glossary",
    "CON": "Contracts",
    "RISK": "Risks",
    "PAT": "Patterns",
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


def collect_artifacts_from_dir(artifacts_dir: Path) -> list[tuple[Path, dict]]:
    """Collect artifacts from a bare artifacts/ directory (no .reef/ required)."""
    results = []
    if not artifacts_dir.is_dir():
        return results
    # Check all known subdirs plus any extra ones
    for sd in artifacts_dir.iterdir():
        if not sd.is_dir() or sd.name.startswith("."):
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

    for src_subdir in ["raw", "context/requirements", "context/decisions", "context/processes", "context/meetings", "context/roadmaps"]:
        (root / "sources" / src_subdir).mkdir(parents=True, exist_ok=True)

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

    # Find the artifact file (try exact, then lowercase, then uppercase)
    artifact_file = None
    for aid_variant in [artifact_id, artifact_id.lower(), artifact_id.upper()]:
        for subdir in ARTIFACT_SUBDIRS:
            candidate = reef / "artifacts" / subdir / f"{aid_variant}.md"
            if candidate.is_file():
                artifact_file = candidate
                break
        if artifact_file:
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

    # Build lookup: artifact_id (uppercase) -> (path, frontmatter)
    art_map = {}
    for path, fm in artifacts:
        aid = fm.get("id", path.stem).upper()
        art_map[aid] = (path, fm)

    # Build set of all relates_to targets pointing at each artifact
    incoming = {}  # artifact_id -> set of source artifact ids
    for aid, (_, fm) in art_map.items():
        for entry in (fm.get("relates_to") or []):
            target = entry.get("target", entry) if isinstance(entry, dict) else entry
            target = str(target).strip("[]").upper()
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

        # id matches filename (id is uppercase, filename is lowercase of id)
        if fm.get("id") and fm["id"].lower() != apath.stem.lower():
            errors.append({
                "artifact": aid,
                "check": "schema",
                "severity": "error",
                "message": f"Frontmatter id '{fm['id']}' does not match filename '{apath.stem}'",
            })
        # id should be uppercase
        if fm.get("id") and fm["id"] != fm["id"].upper():
            warnings.append({
                "artifact": aid,
                "check": "id_case",
                "severity": "warning",
                "message": f"Frontmatter id '{fm['id']}' should be uppercase: '{fm['id'].upper()}'",
            })
        # filename should be lowercase
        if apath.stem != apath.stem.lower():
            warnings.append({
                "artifact": aid,
                "check": "filename_case",
                "severity": "warning",
                "message": f"Filename '{apath.name}' should be lowercase: '{apath.stem.lower()}.md'",
            })

        # title must be Title Case
        title_val = fm.get("title", "")
        if title_val:
            minor_words = {"a", "an", "the", "and", "but", "or", "for", "in", "of", "on", "to", "with", "vs", "via"}
            words = title_val.split()
            bad_title = False
            for i, w in enumerate(words):
                # Skip special tokens (arrows, symbols, acronyms that are all-caps)
                if w in {"↔", "→", "←", "--", "-", "/"} or w.isupper():
                    continue
                if i == 0:
                    # First word must be capitalized
                    if w[0].islower():
                        bad_title = True
                        break
                elif w.lower() in minor_words:
                    # Minor words should be lowercase (unless first)
                    if w[0].isupper() and w.lower() in minor_words:
                        continue  # allow capitalized minor words (not an error, just not ideal)
                else:
                    # Major words must be capitalized
                    if w[0].islower():
                        bad_title = True
                        break
            if bad_title:
                warnings.append({
                    "artifact": aid,
                    "check": "title_case",
                    "severity": "warning",
                    "message": f"Title '{title_val}' is not in Title Case",
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
        for entry in (fm.get("relates_to") or []):
            target = entry.get("target", entry) if isinstance(entry, dict) else entry
            target = str(target).strip("[]").upper()
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

        # Check 6: Wikilink/frontmatter sync (case-insensitive comparison)
        relates_to_targets = set()
        for entry in (fm.get("relates_to") or []):
            t = entry.get("target", entry) if isinstance(entry, dict) else entry
            relates_to_targets.add(str(t).strip("[]").upper())
        wikilinks = set()
        if "## Related" in body:
            rel_start = body.index("## Related")
            rel_section = body[rel_start:]
            next_heading = rel_section.find("\n## ", 1)
            if next_heading != -1:
                rel_section = rel_section[:next_heading]

            wikilinks = {wl.upper() for wl in re.findall(r"\[\[([^\]]+)\]\]", rel_section)}

        # Wikilinks in Related that aren't in relates_to
        for wl in wikilinks:
            if wl not in relates_to_targets:
                warnings.append({
                    "artifact": aid,
                    "check": "wikilink_sync",
                    "severity": "warning",
                    "message": f"Wikilink [[{wl}]] in ## Related not in relates_to frontmatter",
                })

        # relates_to entries not in Related wikilinks
        for rt in relates_to_targets:
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
        prefix = (aid.split("-")[0] if "-" in aid else aid).upper()
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


def cmd_inventory(args) -> None:
    """Emit a structured inventory of all artifacts, grouped by type."""
    if args.artifacts_dir:
        # Direct artifacts directory mode (for non-reef repos like knowledge bases)
        artifacts = collect_artifacts_from_dir(Path(args.artifacts_dir))
        reef_path = args.artifacts_dir
    else:
        reef = find_reef_root(args.reef)
        artifacts = collect_artifacts(reef)
        reef_path = str(reef)

    by_type: dict[str, list[dict]] = {}
    for path, fm in artifacts:
        aid = fm.get("id", path.stem)
        atype = fm.get("type", "unknown")
        entry = {
            "id": aid,
            "title": fm.get("title", ""),
            "status": fm.get("status", ""),
            "domain": fm.get("domain", ""),
        }
        by_type.setdefault(atype, []).append(entry)

    # Sort each group by id
    for t in by_type:
        by_type[t].sort(key=lambda x: x["id"])

    total = sum(len(v) for v in by_type.values())
    summary = {t: len(v) for t, v in sorted(by_type.items())}

    emit({
        "reef": reef_path,
        "total": total,
        "summary": summary,
        "artifacts": {t: v for t, v in sorted(by_type.items())},
    })


def cmd_gap(args) -> None:
    """Compare two artifact sets and emit the delta."""
    # Collect from reef (automated)
    reef = find_reef_root(args.reef)
    reef_artifacts = collect_artifacts(reef)

    # Collect from baseline
    baseline_dir = Path(args.baseline)
    if (baseline_dir / ".reef").is_dir():
        baseline_artifacts = collect_artifacts(baseline_dir)
    elif baseline_dir.is_dir():
        baseline_artifacts = collect_artifacts_from_dir(baseline_dir)
    else:
        emit({"status": "error", "message": f"Baseline not found: {baseline_dir}"})
        return

    # Build id sets grouped by type
    def group_by_type(artifacts):
        by_type = {}
        for path, fm in artifacts:
            aid = fm.get("id", path.stem)
            atype = fm.get("type", "unknown")
            by_type.setdefault(atype, {})[aid] = {
                "title": fm.get("title", ""),
                "status": fm.get("status", ""),
                "domain": fm.get("domain", ""),
            }
        return by_type

    reef_by_type = group_by_type(reef_artifacts)
    base_by_type = group_by_type(baseline_artifacts)

    all_types = sorted(set(list(reef_by_type.keys()) + list(base_by_type.keys())))

    per_type = {}
    total_reef = 0
    total_base = 0
    total_missing = 0
    total_extra = 0
    total_matched = 0

    for t in all_types:
        reef_ids = set(reef_by_type.get(t, {}).keys())
        base_ids = set(base_by_type.get(t, {}).keys())

        missing = sorted(base_ids - reef_ids)
        extra = sorted(reef_ids - base_ids)
        matched = sorted(reef_ids & base_ids)

        per_type[t] = {
            "reef_count": len(reef_ids),
            "baseline_count": len(base_ids),
            "matched": len(matched),
            "missing": [{"id": mid, **base_by_type[t][mid]} for mid in missing],
            "extra": [{"id": eid, **reef_by_type[t][eid]} for eid in extra],
        }

        total_reef += len(reef_ids)
        total_base += len(base_ids)
        total_missing += len(missing)
        total_extra += len(extra)
        total_matched += len(matched)

    coverage_pct = round(total_reef / total_base * 100, 1) if total_base else 0

    emit({
        "reef": str(reef),
        "baseline": str(baseline_dir),
        "total_reef": total_reef,
        "total_baseline": total_base,
        "coverage_pct": coverage_pct,
        "matched": total_matched,
        "missing_from_reef": total_missing,
        "extra_in_reef": total_extra,
        "per_type": per_type,
    })


# ---------------------------------------------------------------------------
# Subcommand: audit
# ---------------------------------------------------------------------------


def cmd_audit(args) -> None:
    """Check snorkel output against mandatory minimum artifact requirements."""
    reef = find_reef_root(args.reef)
    project = read_json(reef / ".reef" / "project.json")
    artifacts = collect_artifacts(reef)

    services = project.get("services", [])
    if not services:
        fail("No services configured in project.json. Run /reef:init first.")

    # Build artifact lookup: uppercase ID -> frontmatter
    existing = {}
    for _, fm in artifacts:
        aid = fm.get("id", "").upper()
        existing[aid] = fm

    # Also build prefix -> list of IDs for pattern matching
    by_prefix_service = {}  # (prefix, service_name) -> [ids]
    for aid in existing:
        parts = aid.split("-", 2)
        if len(parts) >= 2:
            prefix = parts[0]
            svc = parts[1]
            by_prefix_service.setdefault((prefix, svc), []).append(aid)

    service_names = [s["name"].upper() for s in services]
    missing = []
    present = []

    # 1. Mandatory per-service: SYS, SCH, API, PROC-auth, GLOSSARY, RISK
    for svc in services:
        svc_upper = svc["name"].upper()

        # SYS-
        sys_id = f"SYS-{svc_upper}"
        if sys_id in existing:
            present.append({"id": sys_id, "type": "system", "status": "present"})
        else:
            missing.append({"id": sys_id, "type": "system", "service": svc["name"],
                            "reason": "Every service must have a SYS- artifact"})

        # SCH- (at least 1)
        sch_ids = by_prefix_service.get(("SCH", svc_upper), [])
        if sch_ids:
            for sid in sch_ids:
                present.append({"id": sid, "type": "schema", "status": "present"})
        else:
            missing.append({"id": f"SCH-{svc_upper}-*", "type": "schema", "service": svc["name"],
                            "reason": "Every service must have at least one SCH- artifact"})

        # API- (at least 1)
        api_ids = by_prefix_service.get(("API", svc_upper), [])
        if api_ids:
            for aid_item in api_ids:
                present.append({"id": aid_item, "type": "api", "status": "present"})
        else:
            missing.append({"id": f"API-{svc_upper}-*", "type": "api", "service": svc["name"],
                            "reason": "Every service must have at least one API- artifact"})

        # PROC-*-AUTH (any PROC containing AUTH for this service)
        proc_ids = by_prefix_service.get(("PROC", svc_upper), [])
        has_auth = any("AUTH" in pid for pid in proc_ids)
        if has_auth:
            auth_ids = [pid for pid in proc_ids if "AUTH" in pid]
            for aid_item in auth_ids:
                present.append({"id": aid_item, "type": "process-auth", "status": "present"})
        else:
            missing.append({"id": f"PROC-{svc_upper}-AUTH", "type": "process-auth", "service": svc["name"],
                            "reason": "Every service must have a PROC- auth artifact"})

        # GLOSSARY- per service
        glossary_id = f"GLOSSARY-{svc_upper}"
        if glossary_id in existing:
            present.append({"id": glossary_id, "type": "glossary", "status": "present"})
        else:
            missing.append({"id": glossary_id, "type": "glossary", "service": svc["name"],
                            "reason": "Every service must have a GLOSSARY- artifact"})

        # RISK- per service
        risk_ids = by_prefix_service.get(("RISK", svc_upper), [])
        if risk_ids:
            for rid in risk_ids:
                present.append({"id": rid, "type": "risk", "status": "present"})
        else:
            missing.append({"id": f"RISK-{svc_upper}-KNOWN-GAPS", "type": "risk", "service": svc["name"],
                            "reason": "Every service must have a RISK- artifact"})

    # 2. Cross-service: CON- for all pairs
    n = len(services)
    expected_pairs = n * (n - 1) // 2
    con_ids = [aid for aid in existing if aid.startswith("CON-")]
    # Count service-pair CONs (exclude entity comparison CONs)
    service_pair_cons = []
    entity_cons = []
    for cid in con_ids:
        # Entity comparisons typically have "ENTITY" in the name
        if "ENTITY" in cid:
            entity_cons.append(cid)
        else:
            service_pair_cons.append(cid)

    if len(service_pair_cons) >= expected_pairs:
        for cid in service_pair_cons:
            present.append({"id": cid, "type": "contract", "status": "present"})
    else:
        # Find which pairs are missing
        existing_pairs = set()
        for cid in service_pair_cons:
            parts = cid.replace("CON-", "").split("-")
            if len(parts) >= 2:
                existing_pairs.add(tuple(sorted(parts[:2])))

        for i in range(n):
            for j in range(i + 1, n):
                pair = tuple(sorted([services[i]["name"].upper(), services[j]["name"].upper()]))
                if pair not in existing_pairs:
                    missing.append({
                        "id": f"CON-{pair[0]}-{pair[1]}",
                        "type": "contract",
                        "service": f"{pair[0]} × {pair[1]}",
                        "reason": f"Service pair contract missing ({expected_pairs} pairs expected for {n} services)",
                    })
                else:
                    present.append({"id": f"CON-{pair[0]}-{pair[1]}", "type": "contract", "status": "present"})

    # 3. Unified glossary
    unified_glossaries = [aid for aid in existing if aid.startswith("GLOSSARY-") and
                          aid.replace("GLOSSARY-", "").split("-")[0] not in
                          [s["name"].upper() for s in services]]
    if unified_glossaries:
        for gid in unified_glossaries:
            present.append({"id": gid, "type": "glossary-unified", "status": "present"})
    else:
        missing.append({"id": "GLOSSARY-*-UNIFIED", "type": "glossary-unified",
                        "reason": "Reef needs a unified cross-service glossary"})

    # Summary
    summary = {
        "total_present": len(present),
        "total_missing": len(missing),
        "pass": len(missing) == 0,
    }

    # Group missing by type for readability
    missing_by_type = {}
    for m in missing:
        missing_by_type.setdefault(m["type"], []).append(m)

    emit({
        "status": "ok",
        "summary": summary,
        "missing": missing,
        "missing_by_type": {t: len(v) for t, v in missing_by_type.items()},
        "present_count": len(present),
    })


# ---------------------------------------------------------------------------
# Subcommand: manifest
# ---------------------------------------------------------------------------


def _extract_entities_from_schema(schema_path: Path) -> list[dict]:
    """Extract entities from a schema.md file by parsing Mermaid ERDs and ## Tables/Collections.

    Returns list of dicts with keys:
      name, tier (1/2/3), fields_count, fk_count, has_status, reason
    """
    try:
        text = schema_path.read_text(encoding="utf-8")
    except Exception:
        return []

    # --- Parse Mermaid erDiagram blocks ---
    raw_entities: dict[str, dict] = {}  # name -> {fields: [], fks: [], has_status: bool}
    in_mermaid = False
    current_entity = None

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```mermaid"):
            in_mermaid = True
            continue
        if stripped.startswith("```") and in_mermaid:
            in_mermaid = False
            current_entity = None
            continue
        if not in_mermaid:
            continue
        if stripped.startswith("erDiagram"):
            continue

        # Relationship lines (e.g., "contract_data ||--o{ contract : has")
        if any(op in stripped for op in ("||", "}o", "}|", "o{", "|{", "--")):
            continue

        # Entity opening: "entity_name {"
        m = re.match(r"^(\w+)\s*\{", stripped)
        if m:
            current_entity = m.group(1)
            if current_entity not in raw_entities:
                raw_entities[current_entity] = {"fields": [], "fks": [], "has_status": False}
            continue

        # Closing brace
        if stripped == "}":
            current_entity = None
            continue

        # Field line inside entity: "TYPE name [PK|FK] [comment]"
        if current_entity and stripped:
            parts = stripped.split()
            if len(parts) >= 2:
                field_type = parts[0]
                field_name = parts[1]
                rest = " ".join(parts[2:]).upper()
                is_fk = "FK" in rest
                is_pk = "PK" in rest

                raw_entities[current_entity]["fields"].append(field_name)
                if is_fk:
                    raw_entities[current_entity]["fks"].append(field_name)
                if field_name.lower() in ("status", "state", "current_run_state",
                                          "current_state", "workflow_state"):
                    raw_entities[current_entity]["has_status"] = True

    # --- Also try ## Tables / ## Collections heading format (fallback) ---
    # Parses markdown tables under ### headings to extract fields, FKs, and status.
    in_tables = False
    current_entity_name = None
    in_column_table = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## Tables") or stripped.startswith("## Collections"):
            in_tables = True
            current_entity_name = None
            in_column_table = False
            continue
        if stripped.startswith("## ") and in_tables:
            in_tables = False
            current_entity_name = None
            in_column_table = False
            continue
        if not in_tables:
            continue
        if stripped.startswith("### "):
            raw_name = stripped[4:].strip().split("(")[0].strip().split(" / ")[0].strip()
            name_lower = raw_name.lower().replace(" ", "_")
            current_entity_name = None
            in_column_table = False
            # Only add if not already parsed from Mermaid
            if name_lower not in {k.lower() for k in raw_entities}:
                raw_entities[raw_name] = {"fields": [], "fks": [], "has_status": False}
                current_entity_name = raw_name
            continue
        if current_entity_name is None:
            continue
        # Detect markdown table header row: | Column | Type | Constraints |
        if stripped.startswith("|") and not in_column_table:
            headers = [h.strip().lower() for h in stripped.split("|")]
            if any(h in ("column", "field", "name") for h in headers):
                in_column_table = True
            continue
        # Skip separator row: |--------|------|-------------|
        if in_column_table and stripped.startswith("|") and set(stripped.replace("|", "").strip()) <= {"-", " "}:
            continue
        # Parse data rows: | column_name | TYPE | constraints |
        if in_column_table and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")]
            # Remove empty first/last from leading/trailing |
            cells = [c for c in cells if c]
            if len(cells) >= 2:
                field_name = cells[0]
                constraints_str = " ".join(cells[2:]).upper() if len(cells) >= 3 else ""
                ent = raw_entities[current_entity_name]
                # Skip system fields for counting later, but still record them
                ent["fields"].append(field_name)
                if "FK" in constraints_str or field_name.endswith("_id"):
                    ent["fks"].append(field_name)
                if field_name.lower() in ("status", "state", "current_run_state",
                                          "current_state", "workflow_state"):
                    ent["has_status"] = True
            continue
        # Non-table line after table started means table ended
        if in_column_table and not stripped.startswith("|"):
            in_column_table = False

    # --- Classify into tiers ---
    SYSTEM_FIELDS = {"id", "_id", "created_at", "updated_at", "deleted_at"}
    JUNCTION_PATTERN = re.compile(r"__")
    LOOKUP_NAMES = {"ethnicity", "race", "gender", "country", "language",
                    "timezone", "currency", "tag"}
    EVENT_LOG_SUFFIXES = ("_logs", "_log", "_events", "_event", "_states",
                          "_history", "_audit")
    MV_SUFFIXES = ("_mv", "_flat_mv")

    # Count incoming FKs per entity (how many other entities reference this one)
    incoming_fk_count: dict[str, int] = {}
    for name, info in raw_entities.items():
        for fk_field in info["fks"]:
            # FK fields typically reference another entity: {entity}_id or {entity}_fk
            ref_name = fk_field.lower().replace("_id", "").replace("_fk", "").replace(" ", "_")
            for other_name in raw_entities:
                if other_name.lower().replace(" ", "_") == ref_name:
                    incoming_fk_count[other_name] = incoming_fk_count.get(other_name, 0) + 1
                    break
    # Also count junction table references (entity__entity patterns)
    for name in raw_entities:
        if JUNCTION_PATTERN.search(name):
            parts = name.lower().split("__")
            for part in parts:
                for other_name in raw_entities:
                    if other_name.lower().replace(" ", "_") == part:
                        incoming_fk_count[other_name] = incoming_fk_count.get(other_name, 0) + 1

    entities = []
    for name, info in raw_entities.items():
        name_lower = name.lower()
        business_fields = [f for f in info["fields"]
                           if f.lower() not in SYSTEM_FIELDS]
        fk_count = len(info["fks"])
        has_status = info["has_status"]
        field_count = len(business_fields)
        inbound_fks = incoming_fk_count.get(name, 0)

        # Tier 3: join tables, lookups, materialized views
        if JUNCTION_PATTERN.search(name):
            tier, reason = 3, "junction table"
        elif any(name_lower.endswith(s) for s in MV_SUFFIXES):
            tier, reason = 3, "materialized view"
        elif name_lower in LOOKUP_NAMES and field_count <= 3:
            tier, reason = 3, "lookup table"
        elif any(name_lower.endswith(s) for s in EVENT_LOG_SUFFIXES):
            tier, reason = 2, "event log/audit table — document in parent lifecycle"
        elif field_count <= 2 and fk_count == 0 and not has_status and inbound_fks < 3:
            tier, reason = 3, "trivial entity"
        # Data-companion entities: Tier 2 unless very complex
        elif name_lower.endswith("_data") and field_count <= 10:
            tier, reason = 2, "data companion — document in parent lifecycle"
        # Tier 1: entities with real lifecycles
        elif has_status:
            tier, reason = 1, "has status/state field"
        elif field_count > 5 and fk_count >= 1:
            tier, reason = 1, f"complex ({field_count} fields, {fk_count} FKs)"
        elif fk_count >= 3:
            tier, reason = 1, f"highly connected ({fk_count} outgoing FKs)"
        elif inbound_fks >= 3:
            tier, reason = 1, f"highly referenced ({inbound_fks} incoming FKs)"
        # Tier 2: connected but no independent lifecycle
        else:
            tier, reason = 2, "connected but no independent lifecycle"

        entities.append({
            "name": name,
            "tier": tier,
            "fields_count": field_count,
            "fk_count": fk_count,
            "inbound_fk_count": inbound_fks,
            "has_status": has_status,
            "reason": reason,
        })

    return entities


def cmd_manifest(args) -> None:
    """Generate scuba manifest skeleton from project.json + extracted sources."""
    reef = find_reef_root(args.reef)
    project = read_json(reef / ".reef" / "project.json")
    artifacts = collect_artifacts(reef)

    services = project.get("services", [])
    if not services:
        fail("No services configured in project.json.")

    existing_ids = set()
    for _, fm in artifacts:
        existing_ids.add(fm.get("id", "").upper())

    planned = []

    def plan(artifact_id: str, atype: str, **extra):
        aid_upper = artifact_id.upper()
        status = "update" if aid_upper in existing_ids else "new"
        entry = {"id": artifact_id, "type": atype, "status": status}
        entry.update(extra)
        planned.append(entry)

    # 1. API- from extracted specs
    apis_dir = reef / "sources" / "apis"
    if apis_dir.is_dir():
        for spec_path in sorted(apis_dir.rglob("openapi.json")):
            rel = spec_path.relative_to(apis_dir)
            parts = list(rel.parts[:-1])  # e.g., ["payments", "gateway"]
            if len(parts) >= 2:
                svc, sub = parts[0].upper(), parts[1].upper()
                aid = f"API-{svc}-{sub}"
            elif len(parts) == 1:
                aid = f"API-{parts[0].upper()}"
            else:
                continue
            plan(aid, "api", source=str(spec_path.relative_to(reef)))

    # 2. SCH- from extracted schemas
    schemas_dir = reef / "sources" / "schemas"
    all_entities_by_service = {}  # service_upper -> [(entity_name, schema_source)]
    if schemas_dir.is_dir():
        for schema_path in sorted(schemas_dir.rglob("schema.md")):
            rel = schema_path.relative_to(schemas_dir)
            parts = list(rel.parts[:-1])
            if len(parts) >= 2:
                svc, sub = parts[0].upper(), parts[1].upper()
                aid = f"SCH-{svc}-{sub}"
            elif len(parts) == 1:
                aid = f"SCH-{parts[0].upper()}"
            else:
                continue
            plan(aid, "schema", source=str(schema_path.relative_to(reef)))

            # Extract entities for PROC- planning (with tiering)
            entities = _extract_entities_from_schema(schema_path)
            svc_key = parts[0].upper()
            if svc_key not in all_entities_by_service:
                all_entities_by_service[svc_key] = []
            for ent in entities:
                ent["schema_source"] = str(schema_path.relative_to(reef))
                all_entities_by_service[svc_key].append(ent)

    # 3. PROC-entity lifecycles (Tier 1 only, with multi-app dedup)
    #
    # Multi-app dedup: when a service has multiple sub-schemas (e.g., a service
    # with regional or product-line variants) and the same entity name appears
    # in multiple sub-schemas, plan ONE lifecycle at the SERVICE level
    # (e.g., PROC-PAYMENTS-ORDER-LIFECYCLE), not one per sub-app.
    #
    # Entity tiering summary is emitted in the output for Claude to report.
    tiering_report = {}
    all_tier1_count = 0

    for svc in services:
        svc_upper = svc["name"].upper()
        svc_sources = [s.upper() for s in svc.get("sources", [])]

        # Collect entities across all sub-schemas for this service
        svc_entities: dict[str, dict] = {}  # entity_name_lower -> best entity info
        for schema_key, entities in all_entities_by_service.items():
            # Match schema_key to service (schema keys are uppercase service names)
            if schema_key != svc_upper:
                continue
            for ent in entities:
                name_lower = ent["name"].lower().replace(" ", "_")
                existing = svc_entities.get(name_lower)
                if existing is None:
                    svc_entities[name_lower] = ent
                else:
                    # Keep the one with more fields (better for tiering)
                    if ent.get("fields_count", 0) > existing.get("fields_count", 0):
                        svc_entities[name_lower] = ent

        tier_counts = {1: 0, 2: 0, 3: 0}
        tier1_names = []
        for name_lower, ent in svc_entities.items():
            tier = ent.get("tier", 2)
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            if tier == 1:
                tier1_names.append(ent["name"])
                ent_slug = ent["name"].upper().replace("_", "-").replace(" ", "-")
                aid = f"PROC-{svc_upper}-{ent_slug}-LIFECYCLE"
                plan(aid, "process", entity=ent["name"],
                     source=ent.get("schema_source", ""),
                     tier=1)

        all_tier1_count += tier_counts[1]
        tiering_report[svc_upper] = {
            "tier1": tier_counts[1],
            "tier2": tier_counts[2],
            "tier3": tier_counts[3],
            "tier1_entities": tier1_names,
        }

    # 4. CON- service pairs (combinatorial)
    n = len(services)
    for i in range(n):
        for j in range(i + 1, n):
            a = services[i]["name"].upper()
            b = services[j]["name"].upper()
            pair = tuple(sorted([a, b]))
            aid = f"CON-{pair[0]}-{pair[1]}"
            plan(aid, "contract", source="cross-service")

    # 5. RISK- per service
    for svc in services:
        aid = f"RISK-{svc['name'].upper()}-KNOWN-GAPS"
        plan(aid, "risk", source="code-scan")

    # 6. DEC- per service (placeholder — Claude fills in specifics)
    for svc in services:
        # Check if any DEC- exists for this service already
        svc_upper = svc["name"].upper()
        has_dec = any(eid.startswith(f"DEC-{svc_upper}") for eid in existing_ids)
        if not has_dec:
            aid = f"DEC-{svc_upper}-OBSERVABLE"
            plan(aid, "decision", source="code-scan",
                 note="Placeholder — Claude should replace with specific decisions found during analysis")

    # 7. GLOSSARY- per service + source index
    for svc in services:
        aid = f"GLOSSARY-{svc['name'].upper()}"
        plan(aid, "glossary", source="cross-artifact")
    plan("GLOSSARY-SOURCE-INDEX", "glossary", source="cross-artifact")

    # 8. PROC- flow catalogs (for services with pipeline/orchestration)
    # Heuristic: check service descriptions for pipeline/orchestration keywords
    pipeline_keywords = {"pipeline", "prefect", "celery", "airflow", "orchestrat", "worker", "job", "queue"}
    for svc in services:
        desc = (svc.get("description", "") or "").lower()
        sources_str = " ".join(svc.get("sources", [])).lower()
        if any(kw in desc or kw in sources_str for kw in pipeline_keywords):
            aid = f"PROC-{svc['name'].upper()}-FLOW-CATALOG"
            plan(aid, "process", source="code-scan",
                 note="Flow catalog for pipeline/orchestration service")

    # 9. SCH- per-collection (for document store services with 3+ collections)
    for svc_upper, entities in all_entities_by_service.items():
        doc_store_entities = []
        for ent in entities:
            schema_text = ""
            try:
                schema_text = (reef / ent["schema_source"]).read_text(encoding="utf-8")
            except Exception:
                pass
            if "## Collections" in schema_text and ent.get("tier", 2) <= 2:
                doc_store_entities.append(ent)

        if len(doc_store_entities) >= 3:
            for ent in doc_store_entities:
                ent_slug = ent["name"].upper().replace("_", "-").replace(" ", "-")
                aid = f"SCH-{svc_upper}-COLLECTION-{ent_slug}"
                plan(aid, "schema", entity=ent["name"],
                     source=ent["schema_source"],
                     note="Per-collection schema for document store")

    # --- Checklist A: SYS- updates (one per service) ---
    for svc in services:
        aid = f"SYS-{svc['name'].upper()}"
        if aid in existing_ids:
            plan(aid, "system", source="checklist-A",
                 note="SYS- deepening: add dependencies, Does NOT Own, behavior highlights, runtime components")

    # --- Checklist B2: PAT- from cross-service divergence signals ---
    # Detect entities/concepts that appear in 2+ services with different structures.
    # These are high-confidence pattern candidates that can be auto-generated.
    if len(services) >= 2:
        # Collect entity names per service (normalized to tokens for fuzzy matching)
        entities_per_service: dict[str, set[str]] = {}
        # Also keep raw names for reporting
        entities_raw_per_service: dict[str, dict[str, str]] = {}  # svc -> {normalized: raw}
        for svc_upper, ents in all_entities_by_service.items():
            entities_per_service[svc_upper] = set()
            entities_raw_per_service[svc_upper] = {}
            for e in ents:
                if e.get("tier", 3) <= 2:
                    raw = e["name"].lower().replace("_", " ")
                    entities_per_service[svc_upper].add(raw)
                    entities_raw_per_service[svc_upper][raw] = e["name"]

        # --- Method 1: Exact match (original) ---
        from collections import Counter
        entity_service_count: dict[str, list[str]] = {}
        for svc_upper, names in entities_per_service.items():
            for name in names:
                entity_service_count.setdefault(name, []).append(svc_upper)
        shared_entities = {name: svcs for name, svcs in entity_service_count.items()
                          if len(svcs) >= 2}

        # --- Method 2: Token-overlap matching ---
        # "acquisition project" and "project" share the token "project"
        # Match when a shorter name is a substring of a longer name,
        # or when names share a significant token (>= 4 chars, not generic)
        GENERIC_TOKENS = {"data", "type", "base", "info", "item", "list",
                          "model", "record", "entry", "result", "event"}
        all_svc_names = list(entities_per_service.keys())
        for i, svc_a in enumerate(all_svc_names):
            for svc_b in all_svc_names[i + 1:]:
                for name_a in entities_per_service[svc_a]:
                    for name_b in entities_per_service[svc_b]:
                        if name_a == name_b:
                            continue  # Already caught by exact match
                        # Check substring: "project" in "acquisition project"
                        is_substring = (name_a in name_b) or (name_b in name_a)
                        # Check significant token overlap
                        tokens_a = set(name_a.split())
                        tokens_b = set(name_b.split())
                        shared_tokens = (tokens_a & tokens_b) - GENERIC_TOKENS
                        has_shared_token = any(len(t) >= 4 for t in shared_tokens)
                        if is_substring or has_shared_token:
                            # Use the shorter name as the concept name
                            concept = name_a if len(name_a) <= len(name_b) else name_b
                            key = f"{concept}|fuzzy"
                            if key not in shared_entities:
                                shared_entities[key] = []
                            svcs_in = shared_entities[key]
                            if svc_a not in svcs_in:
                                svcs_in.append(svc_a)
                            if svc_b not in svcs_in:
                                svcs_in.append(svc_b)

        # --- Method 3: Glossary-based divergence detection ---
        # Read GLOSSARY-UNIFIED for cross-service disambiguation table
        glossary_path = reef / "artifacts" / "glossary" / "glossary-unified.md"
        if glossary_path.is_file():
            try:
                glossary_text = glossary_path.read_text(encoding="utf-8")
                # Parse the disambiguation table: | Term | DAIP | CDM | CTL | RDP |
                in_disambig = False
                svc_columns: list[str] = []
                for gline in glossary_text.split("\n"):
                    stripped = gline.strip()
                    if "ambiguous" in stripped.lower() or "disambiguation" in stripped.lower():
                        in_disambig = True
                        continue
                    if in_disambig and stripped.startswith("## "):
                        in_disambig = False
                        continue
                    if not in_disambig:
                        continue
                    if stripped.startswith("|"):
                        cells = [c.strip() for c in stripped.split("|")]
                        cells = [c for c in cells if c]
                        if not cells:
                            continue
                        # Header row: detect service column names
                        if any(c.lower() in ("term", "concept") for c in cells):
                            svc_columns = [c.upper() for c in cells[1:]]
                            continue
                        # Separator row
                        if set(cells[0].replace("-", "").strip()) <= {" ", ""}:
                            continue
                        # Data row: term is first cell, services with non-empty definitions
                        term = cells[0].lower().strip()
                        if not term or len(cells) < 2:
                            continue
                        active_svcs = []
                        for idx, cell in enumerate(cells[1:]):
                            if idx < len(svc_columns) and cell.strip() not in ("", "--", "-", "n/a"):
                                active_svcs.append(svc_columns[idx])
                        if len(active_svcs) >= 2:
                            key = f"{term}|glossary"
                            if key not in shared_entities:
                                shared_entities[key] = active_svcs
            except Exception:
                pass

        # Deduplicate and plan PAT- artifacts
        planned_pat_concepts: set[str] = set()
        for raw_key, svcs in shared_entities.items():
            if len(svcs) < 2:
                continue
            # Normalize: strip |fuzzy or |glossary suffix for the concept name
            concept = raw_key.split("|")[0].strip()
            if concept in planned_pat_concepts:
                continue
            planned_pat_concepts.add(concept)
            slug = concept.upper().replace(" ", "-")
            svc_pair = "-".join(sorted(svcs[:2]))
            aid = f"PAT-{svc_pair}-{slug}-COMPARISON"
            source_type = "glossary" if "|glossary" in raw_key else (
                "fuzzy-match" if "|fuzzy" in raw_key else "exact-match")
            plan(aid, "pattern", source=f"cross-service-divergence ({source_type})",
                 note=f"Concept '{concept}' appears in {', '.join(svcs)} with different structures/meanings")

        # Detect repeated architectural patterns across services (error handling, auth, etc.)
        # Check both existing artifacts AND manifest-planned operational PROC-
        operational_patterns: dict[str, list[str]] = {}
        # From existing artifacts
        for _, fm in artifacts:
            aid = fm.get("id", "").upper()
            if aid.startswith("PROC-") and any(
                aid.endswith(suffix) for suffix in ("-ERROR-HANDLING", "-AUTH", "-BACKGROUND-TASKS")
            ):
                for suffix in ("-ERROR-HANDLING", "-AUTH", "-BACKGROUND-TASKS"):
                    if aid.endswith(suffix):
                        pat_type = suffix.lstrip("-")
                        operational_patterns.setdefault(pat_type, []).append(aid)
                        break
        # From manifest-planned items (Checklist D planned above but not yet on disk)
        for entry in planned:
            aid = entry["id"].upper()
            if entry["type"] == "process" and entry.get("source") == "checklist-D":
                for suffix in ("-ERROR-HANDLING", "-AUTH", "-BACKGROUND-TASKS"):
                    if aid.endswith(suffix):
                        pat_type = suffix.lstrip("-")
                        if aid not in operational_patterns.get(pat_type, []):
                            operational_patterns.setdefault(pat_type, []).append(aid)
                        break
        for pat_type, proc_ids in operational_patterns.items():
            if len(proc_ids) >= 2:
                slug = pat_type.replace("-", "-")
                aid = f"PAT-CROSS-SERVICE-{slug}"
                if aid not in existing_ids:
                    plan(aid, "pattern", source="cross-service-pattern",
                         note=f"Same pattern ({pat_type}) found in {len(proc_ids)} services: {', '.join(proc_ids)}")

    # --- Checklist E: FE/BE contracts (sub-step 3.5) ---
    # For services with both frontend and backend repos, plan CON- artifacts
    frontend_signals = {"frontend", "office", "admin", "ui", "web", "app"}
    backend_signals = {"backend", "server", "api", "authenticator", "gateway", "pipeline"}
    for svc in services:
        svc_upper = svc["name"].upper()
        svc_sources = svc.get("sources", [])
        fe_repos = [s for s in svc_sources
                    if any(sig in s.lower() for sig in frontend_signals)]
        be_repos = [s for s in svc_sources
                    if any(sig in s.lower() for sig in backend_signals)]
        if fe_repos and be_repos:
            for fe in fe_repos:
                fe_slug = fe.upper().replace("-", "-")
                aid = f"CON-{svc_upper}-FE-BE-{fe_slug}"
                plan(aid, "contract", source="checklist-E",
                     note=f"Frontend-backend contract: {fe} -> backend")

    # --- Checklist F: Intra-service data contracts (sub-step 3.7b) ---
    # Scan source index for signal files indicating internal contracts
    intra_contract_signals = {
        "hash": "Identifier/hash conventions",
        "identifier": "Identifier conventions",
        "id_gen": "ID generation",
        "checksum": "Checksum conventions",
        "export": "Export/serialization formats",
        "serializer": "Export/serialization formats",
        "path_builder": "Path construction conventions",
        "storage_path": "Path construction conventions",
    }
    source_index_path = reef / ".reef" / "source-index.json"
    if source_index_path.is_file():
        try:
            source_index_raw = json.loads(source_index_path.read_text(encoding="utf-8"))
            source_index = source_index_raw.get("sources", source_index_raw)
            for svc in services:
                svc_upper = svc["name"].upper()
                svc_source_names = set(svc.get("sources", []))
                found_signals: dict[str, list[str]] = {}  # signal_type -> [file_paths]
                for src_name, src_data in source_index.items():
                    if src_name not in svc_source_names:
                        continue
                    files = src_data.get("files", [])
                    if isinstance(files, dict):
                        file_list = list(files.keys())
                    elif isinstance(files, list):
                        file_list = files
                    else:
                        continue
                    for fpath in file_list:
                        fpath_lower = fpath.lower()
                        fname = fpath_lower.rsplit("/", 1)[-1] if "/" in fpath_lower else fpath_lower
                        for signal_key, signal_desc in intra_contract_signals.items():
                            if signal_key in fname:
                                found_signals.setdefault(signal_desc, []).append(fpath)
                                break
                for signal_desc, files in found_signals.items():
                    if len(files) >= 1:
                        slug = signal_desc.upper().replace(" ", "-").replace("/", "-")
                        aid = f"CON-{svc_upper}-{slug}"
                        plan(aid, "contract", source="checklist-F-intra",
                             note=f"Intra-service contract: {signal_desc} ({len(files)} signal files)")
        except Exception:
            pass

    # --- Checklist F2: Multi-app comparison PROC- (sub-step 3.14) ---
    # For services with multiple sub-apps sharing entities, plan comparison artifacts
    for svc in services:
        svc_upper = svc["name"].upper()
        sub_apps = svc.get("sub_apps", [])
        # Also detect multi-app from schemas: if service has 2+ sub-schema dirs
        schema_svc_dir = reef / "sources" / "schemas" / svc["name"].lower()
        schema_subs = []
        if schema_svc_dir.is_dir():
            schema_subs = [d.name for d in schema_svc_dir.iterdir()
                           if d.is_dir() and (d / "schema.md").is_file()]
        app_list = sub_apps if sub_apps else schema_subs
        # Filter to application-level sub-apps (not libraries)
        app_level = [a for a in app_list
                     if a.lower() not in ("auth", "backend-core", "cc-export",
                                          "cc-primitive", "cc-schema",
                                          "cc-test-data-generator", "rpc")]
        if len(app_level) >= 2:
            # Plan one comparison artifact for the whole service
            aid = f"PROC-{svc_upper}-MULTI-APP-COMPARISON"
            plan(aid, "process", source="checklist-F2",
                 note=f"Multi-app comparison: {', '.join(app_level)}")
            # Also plan pairwise comparisons for apps with shared schemas
            if len(schema_subs) >= 2:
                compared = set()
                for ia, app_a in enumerate(schema_subs):
                    for app_b in schema_subs[ia + 1:]:
                        pair_key = f"{app_a}-{app_b}"
                        if pair_key in compared:
                            continue
                        compared.add(pair_key)
                        a_slug = app_a.upper().replace("-", "-")
                        b_slug = app_b.upper().replace("-", "-")
                        aid = f"PROC-{svc_upper}-{a_slug}-VS-{b_slug}"
                        plan(aid, "process", source="checklist-F2",
                             note=f"Schema comparison: {app_a} vs {app_b}")

    # --- Checklist G: SCH- field lineage (sub-step 3.16) ---
    # For services with ingestion/ETL/transform logic, plan field lineage artifacts
    lineage_signal_keywords = {"ingestion", "ingest", "etl", "transform", "pipeline",
                               "import", "sync", "migration", "loader"}
    for svc in services:
        svc_upper = svc["name"].upper()
        svc_desc = svc.get("description", "").lower()
        svc_source_names = set(svc.get("sources", []))
        has_lineage_signal = any(kw in svc_desc for kw in lineage_signal_keywords)
        # Also check source names
        if not has_lineage_signal:
            has_lineage_signal = any(
                any(kw in src.lower() for kw in lineage_signal_keywords)
                for src in svc_source_names
            )
        if has_lineage_signal:
            # Plan one field lineage artifact per service with ETL signals
            aid = f"SCH-{svc_upper}-FIELD-LINEAGE"
            plan(aid, "schema", source="checklist-G",
                 note="Field lineage tracing for ingestion/ETL entities")

    # --- Checklist C: Individual PROC- from catalog/inventory artifacts ---
    # Generalised: works for flow catalogs, event catalogs, job catalogs, etc.
    # Parses both wikilinks AND markdown table rows to discover items.
    catalog_dir = reef / "artifacts" / "processes"
    CATALOG_SUFFIXES = ("flow-catalog", "event-catalog", "job-catalog",
                        "task-catalog", "catalog", "inventory")
    if catalog_dir.is_dir():
        for fpath in catalog_dir.iterdir():
            if fpath.suffix != ".md":
                continue
            fname_lower = fpath.stem.lower()
            matched_suffix = None
            for suffix in CATALOG_SUFFIXES:
                if fname_lower.endswith(suffix):
                    matched_suffix = suffix
                    break
            if matched_suffix is None:
                continue
            try:
                catalog_text = fpath.read_text(encoding="utf-8")
            except Exception:
                continue
            # Extract service prefix: proc-pipeline-flow-catalog -> PIPELINE
            prefix_part = fname_lower.replace("proc-", "").replace(f"-{matched_suffix}", "")
            svc_prefix = prefix_part.upper()
            # Determine item type slug from catalog suffix (flow-catalog -> FLOW)
            item_slug = matched_suffix.replace("-catalog", "").replace("-inventory", "").upper()
            if item_slug in ("", "CATALOG", "INVENTORY"):
                item_slug = "ITEM"

            found_items = set()
            for line in catalog_text.split("\n"):
                # Method 1: wikilinks [[PROC-SVC-FLOW-NAME]]
                for m in re.finditer(r"\[\[PROC-" + svc_prefix + r"-" + item_slug + r"-([A-Z0-9-]+)\]\]", line, re.IGNORECASE):
                    found_items.add(m.group(1).upper())
                # Method 2: first column of markdown table rows (skip headers/separators)
                if line.strip().startswith("|") and not set(line.strip().replace("|", "").strip()) <= {"-", " "}:
                    cells = [c.strip() for c in line.split("|")]
                    cells = [c for c in cells if c]
                    if len(cells) >= 2:
                        first_cell = cells[0]
                        # Skip header rows (heuristic: header words)
                        if first_cell.lower() in ("name", "flow", "event", "job", "task",
                                                   "category", "type", "id", "#", ""):
                            continue
                        # Extract a slug from the first cell — could be a name or code identifier
                        slug = re.sub(r"[^a-zA-Z0-9_-]", "-", first_cell).strip("-").upper()
                        slug = re.sub(r"-+", "-", slug)
                        if slug and len(slug) >= 3 and len(slug) <= 60:
                            found_items.add(slug)

            for item_name in sorted(found_items):
                aid = f"PROC-{svc_prefix}-{item_slug}-{item_name}"
                plan(aid, "process", source="checklist-C",
                     note=f"Individual {item_slug.lower()} from {matched_suffix}")

    # --- Checklist D: Operational PROC- per service ---
    operational_types = [
        ("AUTH", "Authentication and authorization patterns"),
        ("ERROR-HANDLING", "Error handling patterns"),
    ]
    for svc in services:
        svc_upper = svc["name"].upper()
        for op_suffix, op_note in operational_types:
            aid = f"PROC-{svc_upper}-{op_suffix}"
            plan(aid, "process", source="checklist-D", note=op_note)

    # --- PROC count floor check ---
    # Count both planned PROC- and existing PROC- artifacts not in the manifest
    proc_planned = sum(1 for e in planned if e["type"] == "process")
    proc_existing = sum(1 for eid in existing_ids if eid.startswith("PROC-"))
    proc_in_manifest = sum(1 for e in planned
                           if e["type"] == "process" and e["id"].upper() in existing_ids)
    # Total = new planned + existing (avoid double-counting updates)
    proc_total = proc_planned + proc_existing - proc_in_manifest
    proc_floor = all_tier1_count + len(services) * 3
    floor_met = proc_total >= proc_floor

    # Deduplicate (same ID planned multiple times)
    seen = set()
    deduped = []
    for entry in planned:
        key = entry["id"].upper()
        if key not in seen:
            seen.add(key)
            deduped.append(entry)

    # Summary by type
    by_type = {}
    new_count = 0
    update_count = 0
    for entry in deduped:
        by_type.setdefault(entry["type"], {"new": 0, "update": 0})
        if entry["status"] == "new":
            by_type[entry["type"]]["new"] += 1
            new_count += 1
        else:
            by_type[entry["type"]]["update"] += 1
            update_count += 1

    manifest = {
        "generated_at": now_iso(),
        "planned": deduped,
        "completed": [],
        "skipped": [],
    }

    # Write manifest
    write_json(reef / ".reef" / "scuba-manifest.json", manifest)

    emit({
        "status": "ok",
        "total_planned": len(deduped),
        "new": new_count,
        "updates": update_count,
        "by_type": by_type,
        "entity_tiering": tiering_report,
        "proc_floor": {
            "tier1_entities": all_tier1_count,
            "services": len(services),
            "floor": proc_floor,
            "proc_in_manifest": proc_planned,
            "proc_existing_not_in_manifest": proc_existing - proc_in_manifest,
            "proc_total": proc_total,
            "floor_met": floor_met,
        },
        "manifest_path": str(reef / ".reef" / "scuba-manifest.json"),
    })


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

    # gap
    p_gap = sub.add_parser("gap", help="Compare reef artifacts against a baseline")
    p_gap.add_argument("--reef", default=None, help="Path to reef root")
    p_gap.add_argument("--baseline", required=True, help="Path to baseline (reef root or artifacts/ directory)")
    p_gap.set_defaults(func=cmd_gap)

    # inventory
    p_inv = sub.add_parser("inventory", help="Emit structured artifact inventory as JSON")
    p_inv.add_argument("--reef", default=None, help="Path to reef root")
    p_inv.add_argument("--artifacts-dir", default=None, help="Direct path to artifacts/ directory (for non-reef repos)")
    p_inv.set_defaults(func=cmd_inventory)

    # audit
    p_audit = sub.add_parser("audit", help="Check snorkel output against mandatory minimums")
    p_audit.add_argument("--reef", default=None, help="Path to reef root")
    p_audit.set_defaults(func=cmd_audit)

    # manifest
    p_manifest = sub.add_parser("manifest", help="Generate scuba manifest from project.json + extracted sources")
    p_manifest.add_argument("--reef", default=None, help="Path to reef root")
    p_manifest.set_defaults(func=cmd_manifest)

    # log
    p_log = sub.add_parser("log", help="Append entry to evolution log")
    p_log.add_argument("message", help="Log message")
    p_log.add_argument("--reef", default=None, help="Path to reef root")
    p_log.set_defaults(func=cmd_log)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
