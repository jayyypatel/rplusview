# Contributing to RPlusView

Thanks for helping improve RPlusView. This guide keeps contributions secure and easy to review.

## Quick start

```bash
git clone https://github.com/jayyypatel/rplusview.git
cd rplusview
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q
ruff check .
```

Optional: copy `.env.example` → `.env` for local API calls. **Never commit `.env` or real tokens.**

## Workflow (fork → PR)

1. Fork the repository and clone your fork.
2. Create a branch from latest `main`:
   ```bash
   git checkout main && git pull
   git checkout -b feat/short-description
   ```
3. Make a focused change (one concern per PR).
4. Run checks locally:
   ```bash
   ruff check .
   ruff format .
   pytest -q
   ```
5. Commit with a **DCO sign-off**:
   ```bash
   git commit -s -m "Explain why this change exists"
   ```
6. Push to your fork and open a Pull Request against `main` using the PR template.

External contributors **cannot push to `main`**. All changes land via reviewed PRs.

## Releases / PyPI

**Only the repository owner publishes to PyPI.** Contributors must not upload
packages, hold PyPI tokens, or push release tags on the upstream repo.

See [docs/PUBLISHING.md](docs/PUBLISHING.md) for the maintainer-only release process.

## Developer Certificate of Origin (DCO)

All commits must include:

```text
Signed-off-by: Your Name <you@example.com>
```

Use `git commit -s`. By signing off, you certify that you have the right to submit the contribution under the project’s MIT license (see [DCO 1.1](https://developercertificate.org/)).

## Code review

- Maintainers review via `CODEOWNERS`.
- CI must be green (lint, tests, gitleaks, CodeQL) before merge.
- Prefer squash-merge; keep history linear on `main`.

## Security

See [SECURITY.md](SECURITY.md). Never paste PATs or private keys into issues or PRs.

## Conduct

Be respectful. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
