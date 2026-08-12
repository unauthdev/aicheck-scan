"""Local inventory of coding-agent credential files.

Relative paths are the coding-agent families from unauth.dev loot list v1
(observed 2026-08-10). This module only reads the local filesystem. It never
issues HTTP. The hosted scanner must not fetch these paths on a remote target.
"""

from __future__ import annotations

import argparse
import json
import stat
import sys
from pathlib import Path

CITE = "unauth.dev loot list v1 — observed 2026-08-10 · CC-BY 4.0"
LOOT_URL = "https://unauth.dev/loot"
CANARY_URL = "https://unauth.dev/canary?flavor=loot"

# Distinct coding-agent files from loot list v1 (not the classic git/aws/ssh tail).
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


def inspect_home(home: Path) -> list[dict]:
    rows = []
    for rel in AGENT_CRED_FILES:
        path = home / rel
        row = {"file": rel, "path": str(path), "present": False,
               "world_readable": False, "mode": None}
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


def present(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["present"]]


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    p = argparse.ArgumentParser(
        prog="aicheck agents",
        description=(
            "Inventory coding-agent credential files in a local home directory. "
            "Read-only. No network. Cite: " + CITE
        ),
    )
    p.add_argument("--home", default=str(Path.home()),
                   help="directory to inspect (default: your home)")
    p.add_argument("--format", choices=("text", "json"), default="text")
    args = p.parse_args(argv)
    home = Path(args.home).expanduser()
    rows = inspect_home(home)
    hits = present(rows)
    if args.format == "json":
        json.dump({"home": str(home), "cite": CITE, "loot": LOOT_URL,
                   "files": rows}, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(f"agent-cred inventory · {home}")
        print(f"cite: {CITE}")
        if not hits:
            print("none of the loot-list coding-agent files are present here.")
        else:
            print(f"{len(hits)} file(s) present:")
            for r in hits:
                wr = " world-readable" if r["world_readable"] else ""
                print(f"  {r['mode']}{wr}  {r['path']}")
        print(f"plant a decoy: {CANARY_URL}")
        print(f"the wordlist:  {LOOT_URL}")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
