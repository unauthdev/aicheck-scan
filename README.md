# aicheck-scan

[![selftest](https://github.com/unauthdev/aicheck-scan/actions/workflows/selftest.yml/badge.svg)](https://github.com/unauthdev/aicheck-scan/actions/workflows/selftest.yml)
[![PyPI](https://img.shields.io/pypi/v/aicheck-scan)](https://pypi.org/project/aicheck-scan/)
[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-aicheck--scan-blue?logo=github)](https://github.com/marketplace/actions/aicheck-scan)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Fail the build if coding-agent credential files land in git.

`aicheck agents --ci` walks the checkout, an optional Docker context, and the
runner home. Checkout / context / artifacts fail on **presence**. Home fails
only if a file is **world-readable** (Claude Code on the runner is otherwise
ok). No network. The path list is
[unauth.dev/loot](https://unauth.dev/loot) (102 GET paths, one session,
10 August 2026).

The documented command is `aicheck-scan`; the package also installs `aicheck`
as a short alias.

## Add to CI (60 seconds)

Copy [`examples/agents-ci.yml`](examples/agents-ci.yml) to
`.github/workflows/agents.yml`, or:

```yaml
name: agent-creds
on:
  pull_request:
  push:
    branches: [main]
jobs:
  agents:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: unauthdev/aicheck-scan@v2
```

Pin `@v2` for the floating major, or `@v2.0.0` for an exact release.
Same gate also lives at `uses: unauthdev/aicheck-scan/agents@v2` (older
snippets). Optional inputs: `context` (Docker build context), `artifacts`,
`fail-home`. Maintainer notes: [`docs/marketplace.md`](docs/marketplace.md).

```bash
pip install aicheck-scan
aicheck agents --ci
aicheck agents --home "$HOME"          # laptop inventory; does not fail CI
aicheck agents --ci --context .        # also walk a Docker context
```

Exit 1 if a listed file is in the tree you asked it to fail on. JSON:
`aicheck agents --ci --format json`.

## What it looks for

Relative paths from loot list v1, coding-agent families only:

`.claude/.credentials.json`, `.claude.json`, `.claude/settings.json`,
`.codex/auth.json`, `.qwen/oauth_creds.json`, `.qwen/settings.json`,
`.qwen/.env`, `.kimi-code/credentials/kimi-code.json`,
`.kimi-code/config.toml`, `.grok/auth.json`, `.hermes/auth.json`,
`.config/opencode/opencode.json`, `.local/share/opencode/auth.json`.

A random `.env` is not a hit. `.qwen/.env` is. Cite:
`unauth.dev loot list v1 — observed 2026-08-10 · CC-BY 4.0`.

The hosted scanner at [unauth.dev](https://unauth.dev) names the door (open
n8n, Ollama, …). It never fetches these files on a host you submit.

## Live-probe leftover

v2 moved live-probe off the root Action. `@v1` is frozen (still live-probe,
stuck on 1.2.2). New installs that still want a host probe:

```yaml
- uses: unauthdev/aicheck-scan/scan@v2
  with:
    target: localhost
    fail-grade: F
```

CLI equivalent: `aicheck-scan example.com` / `aicheck scan localhost --allow-private`.
Probe contract: [`docs/PROBES.md`](docs/PROBES.md). Fix cards:
[unauth.dev/fixes](https://unauth.dev/fixes/).

## Inventory

Local continuous sweep of hosts you own. Nothing phones home.

```bash
aicheck inventory --targets targets.yaml --state-dir ./state --allow-private --i-own-these-targets
```

Target examples under [`examples/`](examples/). Schema:
[`docs/schemas/inventory-report-v1.md`](docs/schemas/inventory-report-v1.md).

Docker: `docker run ghcr.io/unauthdev/aicheck:v2 …` (1.3.0+ includes
`aicheck agents`).

## Trust

- `aicheck agents` dials nothing.
- Live-probe traffic is read-only GETs to the host you name. No logins, no
  POSTs, no exploit verification.
- Optional weekly PyPI version check is **opt-in** (`--version-check` /
  `AICHECK_VERSION_CHECK=1`).
- `--dry-run` prints every request and opens no sockets.

Full page: [`docs/trust.md`](docs/trust.md). Security reports: [SECURITY.md](SECURITY.md).

## License

MIT. Dataset on [unauth.dev/loot](https://unauth.dev/loot) is CC-BY 4.0.
Advisory catalog: [`advisories.yaml`](advisories.yaml) / [unauth.dev/advisories](https://unauth.dev/advisories).
