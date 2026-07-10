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
  Search · Sort · Stats · Repos · Open in browser · First-run setup
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img alt="Textual" src="https://img.shields.io/badge/TUI-Textual-0ea5e9?style=for-the-badge"/>
  <img alt="License" src="https://img.shields.io/badge/license-MIT-22c55e?style=for-the-badge"/>
  <img alt="Status" src="https://img.shields.io/badge/status-ready-a855f7?style=for-the-badge"/>
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
| ⌨️ | **Toolbar buttons + shortcuts** — everything is one key away |
| 🔄 | **Switch user anytime** with the User button (`u`) |

---

## 📦 Install as a package

### Option A — from this repo (recommended)

```bash
git clone https://github.com/YOUR_USER/github_plugin.git
cd github_plugin
pip install .
```

That installs the `rplusview` command globally (or into your active venv).

### Option B — editable (for development)

```bash
git clone https://github.com/YOUR_USER/github_plugin.git
cd github_plugin
pip install -e .
```

Code changes apply immediately — no reinstall needed.

### Option C — run without installing

```bash
cd github_plugin
pip install textual requests
python -m rplusview
# or
python app.py
```

### Option D — publish to PyPI (optional)

```bash
pip install build twine
python -m build
twine upload dist/*
```

Then anyone can install with:

```bash
pip install rplusview
```

> Replace `YOUR_USER` with your GitHub username/org, and update
> `[project.urls]` in `pyproject.toml` before publishing.

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

`Open` · `Details` · `Stats` · `Repos` · `Search` · `Sort` · `Refresh` · `User` · `Help`

### Keyboard

| Key | Action |
|:---:|--------|
| `↑` `↓` | Navigate rows |
| `Enter` / `d` | PR details |
| `o` | Open in browser |
| `/` | Live search |
| `s` | Cycle sort (LOC → Date → Title → Repo → Files → #) |
| `t` | Statistics |
| `e` | Repositories |
| `u` | Change user |
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
| GitHub token | `GITHUB_TOKEN` env var or `.env` |
| Tracked username | first-run UI → `~/.config/rplusview/config.json` |

Create a classic PAT at [github.com/settings/tokens](https://github.com/settings/tokens)  
with at least **`repo`** (or public_repo) access for searching PRs.

---

## 🛠️ Develop

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
rplusview
```

Build a distributable wheel locally:

```bash
pip install build
python -m build
ls dist/   # rplusview-1.0.0-py3-none-any.whl
```

---

## 💜 Why RPlusView?

Because your PRs deserve a dashboard that feels as sharp as your code —  
fast, colorful, and living right inside the terminal.

<p align="center">
  <img alt="made with textual" src="https://img.shields.io/badge/made%20with-Textual-0ea5e9?style=flat-square"/>
  <img alt="github" src="https://img.shields.io/badge/powered%20by-GitHub%20GraphQL-181717?style=flat-square&logo=github"/>
</p>
