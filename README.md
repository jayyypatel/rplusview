<p align="center">

```text
██████╗ ██████╗ ██╗     ██╗   ██╗███████╗██╗   ██╗██╗███████╗██╗    ██╗
██╔══██╗██╔══██╗██║     ██║   ██║██╔════╝██║   ██║██║██╔════╝██║    ██║
██████╔╝██████╔╝██║     ██║   ██║███████╗██║   ██║██║█████╗  ██║ █╗ ██║
██╔══██╗██╔═══╝ ██║     ██║   ██║╚════██║╚██╗ ██╔╝██║██╔══╝  ██║███╗██║
██║  ██║██║     ███████╗╚██████╔╝███████║ ╚████╔╝ ██║███████╗╚███╔███╔╝
╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝ ╚══════╝  ╚═══╝  ╚═╝╚══════╝ ╚══╝╚══╝
```

</p>

<p align="center">
  <b>A colorful terminal dashboard for your GitHub pull requests</b><br/>
  Search · Sort · Inbox · Stats · Repos · Odoo tasks · Open in browser
</p>

<p align="center">
  <a href="https://pypi.org/project/rplusview/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/rplusview.svg?style=for-the-badge&logo=pypi&logoColor=white&label=PyPI"></a>
  <a href="https://pypi.org/project/rplusview/"><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/rplusview.svg?style=for-the-badge&logo=python&logoColor=white"></a>
  <a href="https://github.com/jayyypatel/rplusview/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/pypi/l/rplusview.svg?style=for-the-badge&color=22c55e"></a>
  <a href="https://github.com/jayyypatel/rplusview/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/jayyypatel/rplusview/ci.yml?branch=main&style=for-the-badge&label=CI"></a>
</p>

<p align="center">
  <img alt="Textual" src="https://img.shields.io/badge/TUI-Textual-0ea5e9?style=flat-square"/>
  <img alt="GitHub GraphQL" src="https://img.shields.io/badge/API-GitHub%20GraphQL-181717?style=flat-square&logo=github"/>
  <a href="https://github.com/jayyypatel/rplusview/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/jayyypatel/rplusview?style=flat-square"/></a>
</p>

<p align="center">
  <strong>Open source under the <a href="LICENSE">MIT License</a></strong> — fork it, improve it, ship PRs.
</p>

---

## Why RPlusView?

GitHub’s web PR list is fine. Your terminal can be faster.

RPlusView is a **Textual TUI** that loads your pull requests over the GitHub GraphQL API, then lets you search, sort, triage an inbox, inspect details, jump to the browser, and open linked Odoo tasks — without leaving the keyboard.

| | Capability |
|---|---|
| Dashboard | Open PRs first (fast); toggle closed/merged when you need history |
| Inbox | Drafts, needs action, review requests — Pulls-style panels |
| Navigation | Vim `j`/`k`, `gg`/`G`, page keys, live `/` search |
| Insights | Stats and per-repo breakdowns (LOC, open/merged/closed) |
| Odoo tasks | Detects `task-XXXX` in title/branch/body; open on odoo.com with `p` |
| Setup | First-run welcome; change user or token anytime (`u`) |

---

## Install & quick start

**Requirements:** Python **3.10+** and a GitHub personal access token.

```bash
pip install rplusview

# Token (pick one)
export GITHUB_TOKEN=ghp_your_token_here
# or: copy .env.example → .env
# or: paste the token in the first-run / User (u) screen

rplusview
```

From source instead of PyPI:

```bash
git clone https://github.com/jayyypatel/rplusview.git
cd rplusview
pip install .
rplusview
```

On first launch, enter the **GitHub username** whose PRs you want to track.  
That username (and optionally the token) is saved under:

```text
~/.config/rplusview/config.json
```

```text
┌──────────────────────────────────────────────┐
│           ◆  Welcome to RPlusView            │
│   Enter a GitHub username to load their PRs  │
│                                              │
│  GitHub username                             │
│  ┌────────────────────────────────────────┐  │
│  │ octocat                                │  │
│  └────────────────────────────────────────┘  │
│                                              │
│                         [ Continue → ]       │
└──────────────────────────────────────────────┘
```

---

## Authentication

| Source | Notes |
|--------|--------|
| UI (`u` / setup screen) | Saved to config; **preferred** over env |
| `GITHUB_TOKEN` or `GH_TOKEN` | Environment variable |
| `.env` | Local only — never commit (see `.gitignore`) |

Create a token at [github.com/settings/tokens](https://github.com/settings/tokens).

| Token type | Minimum |
|------------|---------|
| Classic PAT | `repo` (private) or `public_repo` (public-only) |
| Fine-grained | Repository access + pull requests read |

---

## Controls

### Toolbar

`Open` · `Task` · `Details` · `Inbox` · `Closed` · `Stats` · `Repos` · `Search` · `Sort` · `Refresh` · `User` · `Help`

### Keyboard

| Key | Action |
|:---:|--------|
| `j` `k` / `↑` `↓` | Navigate rows |
| `gg` / `G` | First / last row |
| `ctrl+d` / `ctrl+u` | Half page down / up |
| `ctrl+f` / `ctrl+b` | Full page down / up |
| `n` / `N` | Next / previous search match |
| `Enter` / `d` | PR details |
| `o` | Open PR in browser |
| `p` | Open Odoo task (`task-XXXX` → odoo.com) |
| `i` | Inbox |
| `c` | Toggle open ↔ closed/merged |
| `/` | Live search |
| `s` | Cycle sort (LOC → Date → Title → Repo → Files → # → Task) |
| `t` | Statistics |
| `e` | Repositories |
| `u` | Change user and/or token |
| `r` | Refresh |
| `?` | Help |
| `Esc` | Clear search / go back |
| `q` | Quit / back |

---

## Configuration

| What | Where |
|------|--------|
| GitHub token | Setup / `u` → `~/.config/rplusview/config.json`, or `GITHUB_TOKEN` / `.env` |
| Tracked username | Setup / `u` → `~/.config/rplusview/config.json` |

Config directory is `0700` and the file is `0600`. The token is stored **plaintext** in that file (readable only by your user).

---

## Project layout

```text
rplusview/
├── pyproject.toml
├── README.md · LICENSE · CONTRIBUTING.md · SECURITY.md
├── .github/                    # CI, CodeQL, Gitleaks, release
├── docs/PUBLISHING.md
├── tests/
└── rplusview/
    ├── app.py                  # main TUI
    ├── github_client.py        # GraphQL API
    ├── config.py · safe.py · odoo_task.py
    ├── rplusview.tcss
    ├── screens/ · widget/
```

---

## Development

```bash
git clone https://github.com/jayyypatel/rplusview.git
cd rplusview
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
ruff check .
ruff format .
```

Optional local hooks:

```bash
pre-commit install
```

CI runs on every pull request: **ruff**, **pytest** (Python 3.10–3.13), **pip-audit**, **Gitleaks**, and **CodeQL**.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the fork → PR workflow and DCO sign-off.  
Security reports: [SECURITY.md](SECURITY.md) (private only).  
Community standards: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

**PyPI publishing is maintainer-only.** Details: [docs/PUBLISHING.md](docs/PUBLISHING.md).

---

## License

[MIT](LICENSE) © RPlusView contributors.
