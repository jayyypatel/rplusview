<p align="center">

```text
██████╗ ██████╗ ██╗     ██╗   ██╗███████╗██╗   ██╗██╗███████╗██╗    ██╗
██╔══██╗██╔══██╗██║     ██║   ██║██╔════╝██║   ██║██║██╔════╝██║    ██║
██████╔╝██████╔╝██║     ██║   ██║███████╗██║   ██║██║█████╗  ██║ █╗ ██║
██╔══██╗██╔═══╝ ██║     ██║   ██║╚════██║╚██╗ ██╔╝██║██╔══╝  ██║███╗██║
██║  ██║██║     ███████╗╚██████╔╝███████║ ╚████╔╝ ██║███████╗╚███╔███╔╝
╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝ ╚══════╝  ╚═══╝  ╚═╝╚══════╝ ╚══╝╚══╝
```
![Dashboard](https://raw.githubusercontent.com/jayp-odoo/RPlusview_plugin/refs/heads/main/photos/screenshot_app.png?token=GHSAT0AAAAAADOCBULCO57FAM22R56WRUSM2SR7PNQ)
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

```bash
pip install rplusview
```

---

## 🚀 Quick start

```bash
# 1) Install
pip install .

# 2) Token (required for GitHub API)
export GITHUB_TOKEN=ghp_your_token_here
# or copy .env.example → .env and fill GITHUB_TOKEN

# 3) Launch
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

`Open` · `Details` · `Inbox` · `Closed` · `Stats` · `Repos` · `Search` · `Sort` · `Refresh` · `User` · `Help`

### Keyboard

| Key | Action |
|:---:|--------|
| `j` `k` / `↑` `↓` | Navigate rows (vim-style) |
| `gg` / `G` | First row / last row |
| `ctrl+d` / `ctrl+u` | Half page down / up |
| `ctrl+f` / `ctrl+b` | Full page down / up |
| `n` / `N` | Next / previous search match |
| `Enter` / `d` | PR details |
| `o` | Open in browser |
| `i` | Inbox (drafts · needs action · review requests) |
| `c` | Toggle open ↔ closed/merged PRs |
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

<p align="center">
  <img alt="made with textual" src="https://img.shields.io/badge/made%20with-Textual-0ea5e9?style=flat-square"/>
  <img alt="github" src="https://img.shields.io/badge/powered%20by-GitHub%20GraphQL-181717?style=flat-square&logo=github"/>
</p>
