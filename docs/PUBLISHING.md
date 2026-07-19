# Publishing to PyPI (maintainer only)

Only the repository owner publishes RPlusView to PyPI. Contributors and
collaborators **cannot** and **must not** upload releases.

## Who can publish

| Actor | Can open PRs | Can merge to `main` | Can push `v*` tags | Can upload to PyPI |
|-------|--------------|---------------------|--------------------|--------------------|
| External contributors (forks) | Yes | No | No | No |
| Collaborators (if any) | Yes | Only if you grant it | Only if you grant it | No |
| You (owner) | Yes | Yes | Yes | Yes |

Forks never get this workflow’s publish job: it is gated on
`github.repository == 'jayyypatel/rplusview'`.

## How you publish (recommended)

1. Merge the release PR to `main`.
2. Create and push a version tag (only you should have permission to do this):

   ```bash
   git checkout main && git pull
   git tag -a v3.0.1 -m "rplusview 3.0.1"
   git push origin v3.0.1
   ```

3. GitHub Actions runs `.github/workflows/release.yml`.
4. Approve the deployment for environment **`pypi`** if prompted.
5. The package uploads via **Trusted Publishing** (OIDC) — no API token in the repo.

## One-time PyPI + GitHub setup (you only)

### A. GitHub Environment `pypi`

Repo → **Settings** → **Environments** → **New environment** → name: `pypi`

- **Required reviewers**: add only your account
- **Deployment branches and tags**: limit to tags matching `v*` (or “Selected tags”)
- Do **not** grant other people access to this environment

### B. PyPI Trusted Publisher

On [pypi.org](https://pypi.org) → your project (or pending publisher) → **Publishing** → **Add a new pending publisher**:

| Field | Value |
|-------|--------|
| Owner | `jayyypatel` |
| Repository | `rplusview` |
| Workflow name | `release.yml` |
| Environment name | `pypi` |

Do **not** create a long-lived PyPI API token and put it in GitHub Secrets unless you have no other option. If you ever did, revoke it and switch to trusted publishing.

### C. Repo access

- Keep **Settings → Collaborators** empty (or triage-only with no admin).
- Protect `main` so only you can merge.
- Restrict who can create releases/tags (org/repo rulesets if available).

## What contributors should know

Contributors never need PyPI credentials. Version bumps in a PR do **not** publish anything until **you** tag and approve the `pypi` environment deployment.
