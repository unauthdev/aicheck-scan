# trust

why you can run aicheck in your CI without taking our word for anything.

## what the engine does

the product Action (`uses: unauthdev/aicheck-scan@v2`) is `aicheck agents`.
it walks the checkout on the runner. it dials nothing.

the leftover live-probe (`uses: unauthdev/aicheck-scan/scan@v2`, or the CLI
`aicheck scan`) sends read-only GETs to the target you give it, on the
well-known AI-service ports. it asks for version, tags, and settings
endpoints — the same metadata the unauth.dev scanner reads — and grades
what answers.

live-probe dials nothing else. no telemetry, no phone-home, no analytics, no
beacon to unauth.dev. no logins, no POSTs to your services, no exploit
verification. it needs no credentials and accepts none.

there is one optional extra — a weekly, opt-in PyPI version check, off
unless you enable it — in its own section below. `aicheck agents` never
runs it.

## verify it yourself

don't trust this page. check:

- `aicheck agents --ci` — no sockets. `aicheck agents --format json` shows
  every path it looked at.
- `aicheck example.com --dry-run` prints every request the live-probe would
  send — no sockets, no DNS. the plan you see is the whole plan.
- `aicheck example.com --verbose` logs each connection actually dialed
  (with the pinned IP) to stderr, 1:1 against the transport.
- run the live-probe behind a logging proxy and watch every byte.
- or read the source. the engine is dependency-light python (httpx +
  pyyaml); the core is an afternoon's audit.

## supply chain

- every release is built and published by
  [.github/workflows/publish-pypi.yml](https://github.com/unauthdev/aicheck-scan/blob/main/.github/workflows/publish-pypi.yml)
  with SLSA provenance attestations on the `dist/*` artifacts (via
  `actions/attest-build-provenance`). verify an artifact with
  `gh attestation verify`.
- publishing uses OIDC trusted publishing — there is no PyPI API token
  anywhere, so there is no token to leak. Maintainer checklist:
  [`docs/pypi.md`](pypi.md).
- the build is reproducible: `pip install build && python -m build` on a
  clean checkout.

## verifying the container image

the `ghcr.io/unauthdev/aicheck` image gets the same treatment as the PyPI
dists, via
[.github/workflows/publish-image.yml](https://github.com/unauthdev/aicheck-scan/blob/main/.github/workflows/publish-image.yml):

- the base image (`python:3.11-slim`) is pinned by digest in
  `packaging/Dockerfile` — no floating base.
- every tag build emits a build-provenance attestation for the image digest.
  verify what you pulled:

  ```bash
  gh attestation verify oci://ghcr.io/unauthdev/aicheck:v2 \
    --owner unauthdev
  ```

- an SBOM (SPDX-JSON, via `anchore/sbom-action`) is generated for every
  image and attached to the release as `sbom.spdx.json` — that file is the
  container, not the pip wheel. for pip, pin the SHA256 in the release notes.
- tag pushes assert the tag equals `__version__` before anything is built,
  so `v2.0.0` the tag is always `2.0.0` the code. the floating `v2` git tag
  is convenience; pin a SHA or `v2.0.0` if you need immutability.

## per-release hashes

the release notes for each version carry the sha256 of the sdist and wheel
(appended by the publish workflow itself, straight from the built `dist/`).
that's the number to pin against in `--require-hashes` installs — not a
hash you computed from whatever the index handed you, and not one we typed
into the notes by hand.

## the optional network call beyond your target

off by default. if you enable it with `--version-check` or
`AICHECK_VERSION_CHECK=1`, then once per week, if online, the CLI checks
PyPI's JSON API for a newer version (3s timeout, cannot raise, PyPI-only).
the old opt-out switches — `--no-version-check` and
`AICHECK_NO_VERSION_CHECK=1` — are still honored and silence it. it never
goes anywhere else. `aicheck agents` does not make this call.

## Action pin posture

`uses: unauthdev/aicheck-scan@v2` is a **mutable** floating major tag
(convenience). `@v1` is frozen leftover live-probe; do not use it for new
installs. Third-party Actions in this repo are pinned to full SHAs
(Dependabot keeps them fresh). For a SHA-locked consumer install:

```yaml
- uses: unauthdev/aicheck-scan@<full-commit-sha>  # pin a v2.x release commit
```

`--allow-private` is intentional inside CI runners for the live-probe
(you already control that network). The Action is not a sandbox — a
malicious workflow can still reach metadata IPs the same way `curl` could.
`aicheck agents` does not open sockets.

## hash-pinned install

for the paranoid path, pin by hash instead of trusting the index:

```bash
pip download aicheck-scan --no-deps -d /tmp/aicheck
pip install --require-hashes aicheck-scan \
  --hash sha256:<hash from the release notes>
```

the sha256 hashes of the sdist and wheel are published in the release
notes for each version. combine with `gh attestation verify` for the full
chain: source → build → artifact.

## disclosure

found something? see [SECURITY.md](../SECURITY.md).
