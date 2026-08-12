# Publish aicheck-scan to GitHub Marketplace

Listing is a GitHub UI step. `gh release create` cannot check the Marketplace
box. Listing URL: https://github.com/marketplace/actions/aicheck-scan

v2: the root Action is `aicheck agents` (coding-agent credential files, no
network). Live-probe is `uses: unauthdev/aicheck-scan/scan@v2`.
`@v1` is frozen leftover live-probe. Do not move the `v1` tag.

## Each Marketplace version

1. Tag `v2.x.y` (must match `src/aicheck/__init__.py`).
2. Open the release → check **Publish this Action to the GitHub Marketplace**.
3. Primary category: **Security**.
4. Publish.

Consumers:

```yaml
- uses: actions/checkout@v4
- uses: unauthdev/aicheck-scan@v2
```

Alias: `uses: unauthdev/aicheck-scan/agents@v2` (same gate).
Live-probe leftover: `uses: unauthdev/aicheck-scan/scan@v2` with `target:`.
