"""Local inventory of coding-agent credential files.

Relative paths are the coding-agent families from unauth.dev loot list v1
(observed 2026-08-10). This module only reads the local filesystem. It never
issues HTTP. The hosted scanner must not fetch these paths on a remote target.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path

CITE = "unauth.dev loot list v1, observed 2026-08-10, CC-BY 4.0"
LOOT_URL = "https://unauth.dev/loot"
CANARY_URL = "https://unauth.dev/canary?flavor=loot"

AGENT_CRED_FILES = (
    ".claude/.credentials.json",
    ".claude.json",
    ".claude/settings.json",
    ".codex/auth.json",
    ".qwen/oauth_creds.json",
    ".qwen/settings.json",
    ".qwen/.env",
    ".kimi-code/credentials/kimi-code.json",
    ".kimi-code/config.toml",
    ".grok/auth.json",
    ".hermes/auth.json",
    ".config/opencode/opencode.json",
    ".local/share/opencode/auth.json",
)

SKIP_DIR_NAMES = frozenset({
    ".git", "node_modules", ".venv", "venv", "__pycache__",
    ".tox", "dist", "build", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".nox",
})


def match_cred(rel: str) -> str | None:
    rel = rel.replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    rel = rel.lstrip("/")
    for cred in AGENT_CRED_FILES:
        if rel == cred or rel.endswith("/" + cred):
            return cred
    return None


def _empty_row(rel: str, path: Path) -> dict:
    return {"file": rel, "path": str(path), "present": False,
            "world_readable": False, "mode": None, "symlink": False}


def _stat_row(path: Path, rel: str, cred: str) -> dict:
    row = _empty_row(cred, path)
    row["path"] = str(path)
    try:
        st = path.lstat()
    except OSError:
        return row
    row["present"] = True
    row["symlink"] = stat.S_ISLNK(st.st_mode)
    row["mode"] = oct(st.st_mode & 0o777)
    row["world_readable"] = bool(st.st_mode & 0o004)
    return row


def inspect_home(home: Path) -> list[dict]:
    rows = []
    for rel in AGENT_CRED_FILES:
        path = home / rel
        row = _empty_row(rel, path)
        try:
            st = path.stat()
        except OSError:
            rows.append(row)
            continue
        if not stat.S_ISREG(st.st_mode):
            rows.append(row)
            continue
        row["present"] = True
        row["mode"] = oct(st.st_mode & 0o777)
        row["world_readable"] = bool(st.st_mode & 0o004)
        rows.append(row)
    return rows


def inspect_tree(root: Path) -> list[dict]:
    """Walk a checkout or build context. Hits only. Does not follow symlinks."""
    hits: list[dict] = []
    root = root.expanduser()
    if not root.is_dir():
        raise FileNotFoundError(str(root))
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        keep = []
        for d in dirnames:
            p = Path(dirpath) / d
            rel = str(p.relative_to(root)).replace("\\", "/")
            if d in SKIP_DIR_NAMES:
                continue
            if p.is_symlink():
                for cred in AGENT_CRED_FILES:
                    if cred == rel or cred.startswith(rel + "/"):
                        row = _stat_row(p, rel, cred)
                        hits.append(row)
                        break
                continue
            keep.append(d)
        dirnames[:] = keep
        for name in filenames:
            p = Path(dirpath) / name
            rel = str(p.relative_to(root)).replace("\\", "/")
            cred = match_cred(rel)
            if cred is None:
                continue
            hits.append(_stat_row(p, rel, cred))
    return hits


def present(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["present"]]


def _surface_fails(surface: dict) -> list[dict]:
    policy = surface["policy"]
    out = []
    for row in surface["files"]:
        if not row["present"]:
            continue
        if policy == "present" or row["world_readable"] or row.get("symlink"):
            out.append(row)
    return out


def _print_text(surfaces: list[dict], failing: list[tuple[dict, dict]]) -> None:
    print(f"agent-cred gate · cite: {CITE}")
    for surface in surfaces:
        kind = surface["kind"]
        root = surface["root"]
        policy = surface["policy"]
        hits = [r for r in surface["files"] if r["present"]]
        print(f"{kind} {root}  (fail on {policy})")
        if not hits:
            print("  clean")
            continue
        fail_set = {r["path"] for r, s in failing if s["root"] == surface["root"]
                    and s["kind"] == surface["kind"]}
        for r in hits:
            mark = "FAIL" if r["path"] in fail_set else "ok  "
            wr = " world-readable" if r["world_readable"] else ""
            sl = " symlink" if r.get("symlink") else ""
            mode = r["mode"] or "????"
            print(f"  {mark}  {mode}{wr}{sl}  {r['path']}")
    print(f"plant a decoy: {CANARY_URL}")
    print(f"the wordlist:  {LOOT_URL}")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    p = argparse.ArgumentParser(
        prog="aicheck agents",
        description=(
            "Find coding-agent credential files on disk. Read-only. No network. "
            "Cite: " + CITE
        ),
    )
    p.add_argument("--home", default=None,
                   help="home directory (default: your home, or with --ci the runner home)")
    p.add_argument("--tree", default=None,
                   help="git checkout / worktree to walk")
    p.add_argument("--context", action="append", default=[],
                   help="Docker build context directory (repeatable)")
    p.add_argument("--artifacts", action="append", default=[],
                   help="artifact directory to walk (repeatable)")
    p.add_argument("--ci", action="store_true",
                   help="CI gate: checkout + home. Home presence is ok if not world-readable")
    p.add_argument("--fail-home", action="store_true",
                   help="also fail if any agent-cred file exists in --home")
    p.add_argument("--format", choices=("text", "json"), default="text")
    args = p.parse_args(argv)

    ci = args.ci
    explicit = args.tree or args.context or args.artifacts
    home_path: Path | None
    tree_path: Path | None
    if ci:
        home_path = Path(args.home).expanduser() if args.home else Path.home()
        tree_path = Path(args.tree).expanduser() if args.tree else Path(
            os.environ.get("GITHUB_WORKSPACE") or ".")
    elif explicit:
        home_path = Path(args.home).expanduser() if args.home else None
        tree_path = Path(args.tree).expanduser() if args.tree else None
    else:
        home_path = Path(args.home).expanduser() if args.home else Path.home()
        tree_path = Path(args.tree).expanduser() if args.tree else None

    home_policy = "present" if (not ci or args.fail_home) else "world-readable"
    surfaces: list[dict] = []
    home_rows: list[dict] | None = None

    if home_path is not None:
        home_rows = inspect_home(home_path)
        surfaces.append({
            "kind": "home", "root": str(home_path), "policy": home_policy,
            "files": home_rows,
        })
    if tree_path is not None:
        try:
            rows = inspect_tree(tree_path)
        except FileNotFoundError as exc:
            print(f"aicheck agents: checkout not found: {exc}", file=sys.stderr)
            return 2
        surfaces.append({
            "kind": "checkout", "root": str(tree_path.resolve()),
            "policy": "present", "files": rows,
        })
    for kind, paths in (("context", args.context), ("artifacts", args.artifacts)):
        for raw in paths:
            path = Path(raw).expanduser()
            try:
                rows = inspect_tree(path)
            except FileNotFoundError as exc:
                print(f"aicheck agents: {kind} not found: {exc}", file=sys.stderr)
                return 2
            surfaces.append({
                "kind": kind, "root": str(path.resolve()),
                "policy": "present", "files": rows,
            })

    failing: list[tuple[dict, dict]] = []
    for surface in surfaces:
        for row in _surface_fails(surface):
            failing.append((row, surface))

    if args.format == "json":
        body: dict = {"cite": CITE, "loot": LOOT_URL, "surfaces": surfaces,
                      "failed": bool(failing)}
        if home_rows is not None:
            body["home"] = str(home_path)
            body["files"] = home_rows
        json.dump(body, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        _print_text(surfaces, failing)
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
