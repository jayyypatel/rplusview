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
  <b>⚡ A colorful terminal dashboard for your GitHub pull requests</b><br/>
  Search · Sort · Inbox · Stats · Repos · Open in browser · First-run setup
</p>

<p align="center">
  <img alt="PyPI" src="https://img.shields.io/badge/pypi-v3.0.0-3776AB?style=for-the-badge&logo=pypi&logoColor=white"/>
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img alt="Textual" src="https://img.shields.io/badge/TUI-Textual-0ea5e9?style=for-the-badge"/>
  <img alt="License" src="https://img.shields.io/badge/license-MIT-22c55e?style=for-the-badge"/>
</p>

---

## ✨ Features

| | |
|---|---|
<<<<<<< Updated upstream
| 🎨 | **Polished dark TUI** with GitHub-inspired greens, blues & purples |
| 👋 | **First-run welcome popup** — enter any GitHub username dynamically |
| 🔍 | **Live search** across title, repo, PR number & status |
| 📊 | **Stats & repos views** with LOC, open/merged/closed breakdowns |
| 🌐 | **Open in browser** for PRs and repositories |
| ⌨️ | **Toolbar buttons + shortcuts** — vim `j`/`k` nav, everything is one key away |
| 🔄 | **Switch user / token anytime** with the User button (`u`) |
| 📥 | **Inbox panels** — drafts, needs action, review requests (like GitHub Pulls) |
| ⚡ | **Open PRs first** — faster load; toggle Closed when you need history |

---

## 📦 Install as a package
=======
| Dashboard | Open PRs first (fast); toggle closed/merged when you need history |
| Inbox | Drafts, needs action, review requests — Pulls-style panels |
| Navigation | Vim `j`/`k`, `gg`/`G`, page keys, live `/` search |
| Insights | Stats and per-repo breakdowns (LOC, open/merged/closed) |
| Odoo tasks | Detects `task-XXXX` in title/branch/body; open on odoo.com with `p` |
| Setup | First-run welcome; change user or token anytime (`u`) |

---

## Install & quick start

**Requirements:** Python **3.10+** and a GitHub personal access token.
>>>>>>> Stashed changes

```bash
pip install rplusview

# Token (pick one)
export GITHUB_TOKEN=ghp_your_token_here
# or: copy .env.example → .env
# or: paste the token in the first-run / User (u) screen

rplusview
```

<<<<<<< Updated upstream
---

## 🚀 Quick start

```bash
# 1) Install
pip install .

# 2) Token (required for GitHub API)
export GITHUB_TOKEN=ghp_your_token_here
# or copy .env.example → .env and fill GITHUB_TOKEN

# 3) Launch
=======
From source instead of PyPI:

```bash
git clone https://github.com/jayyypatel/rplusview.git
cd rplusview
pip install .
>>>>>>> Stashed changes
rplusview
```

On **first launch**, a welcome popup asks for the GitHub username to track.  
That username is saved in `~/.config/rplusview/config.json`.

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

## 🎮 Controls

### Toolbar

`Open` · `Task` · `Details` · `Inbox` · `Closed` · `Stats` · `Repos` · `Search` · `Sort` · `Refresh` · `User` · `Help`

### Keyboard

| Key | Action |
|:---:|--------|
| `j` `k` / `↑` `↓` | Navigate rows (vim-style) |
| `gg` / `G` | First row / last row |
| `ctrl+d` / `ctrl+u` | Half page down / up |
| `ctrl+f` / `ctrl+b` | Full page down / up |
| `n` / `N` | Next / previous search match |
| `Enter` / `d` | PR details |
<<<<<<< Updated upstream
| `o` | Open in browser |
| `i` | Inbox (drafts · needs action · review requests) |
| `c` | Toggle open ↔ closed/merged PRs |
=======
| `o` | Open PR in browser |
| `p` | Open Odoo task (`task-XXXX` → odoo.com) |
| `i` | Inbox |
| `c` | Toggle open ↔ closed/merged |
>>>>>>> Stashed changes
| `/` | Live search |
| `s` | Cycle sort (LOC → Date → Title → Repo → Files → #) |
| `t` | Statistics |
| `e` | Repositories |
| `u` | Change user and/or API token |
| `r` | Refresh |
| `?` | Help |
| `Esc` | Clear search / go back |
| `q` | Quit / back |

---

## 🗂️ Project layout

```text
<<<<<<< Updated upstream
github_plugin/
├── pyproject.toml          # package metadata + CLI entrypoint
├── README.md
├── .env.example
├── app.py                  # thin launcher
└── rplusview/              # installable Python package
    ├── app.py              # main TUI
    ├── github_client.py    # GraphQL API
    ├── config.py           # saved username / token
    ├── rplusview.tcss      # theme
    ├── screens/            # details · stats · repos
    └── widget/             # title · actions · setup · help
=======
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
>>>>>>> Stashed changes
```

---

## 🔐 Config

| What | Where |
|------|--------|
| GitHub token | User button (`u`) · or `~/.config/rplusview/config.json` · or `GITHUB_TOKEN` / `.env` |
| Tracked username | User button (`u`) → `~/.config/rplusview/config.json` |

Token saved via the UI is preferred over env/`.env`, so you can fix a wrong token without reinstalling.

Create a classic PAT at [github.com/settings/tokens](https://github.com/settings/tokens)  
with at least **`repo`** (or public_repo) access for searching PRs.

---


## 💜 Why RPlusView?

Because your PRs deserve a dashboard that feels as sharp as your code 
fast, colorful, and living right inside the terminal.

<<<<<<< Updated upstream
<p align="center">
  <img alt="made with textual" src="https://img.shields.io/badge/made%20with-Textual-0ea5e9?style=flat-square"/>
  <img alt="github" src="https://img.shields.io/badge/powered%20by-GitHub%20GraphQL-181717?style=flat-square&logo=github"/>
</p>
=======
[MIT](LICENSE) © RPlusView contributors.
>>>>>>> Stashed changes
