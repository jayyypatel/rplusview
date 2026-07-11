#!/usr/bin/env python3
"""Capture SVG screenshots of RPlusView for the README.

Usage:
    python3 scripts/capture_screenshots.py
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from rplusview.app import RPlusView

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images"


async def _wait_table(app: RPlusView, pilot, timeout: float = 40.0) -> bool:
    steps = int(timeout / 0.25)
    for _ in range(steps):
        await pilot.pause(0.25)
        table = app.query_one("#pr-table")
        if table.display and table.row_count > 0:
            return True
    return False


async def capture() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    app = RPlusView()
    async with app.run_test(size=(120, 36)) as pilot:
        # First-run / user setup overlay
        if type(app.screen).__name__ != "SetupScreen":
            await pilot.press("u")
            await pilot.pause(0.4)
        (OUT / "setup.svg").write_text(app.export_screenshot(), encoding="utf-8")
        print("wrote setup.svg")
        await pilot.press("escape")
        await pilot.pause(0.3)

        if type(app.screen).__name__ == "SetupScreen":
            print("still on setup — cannot capture dashboard without a username")
            return

        ok = await _wait_table(app, pilot)
        if not ok:
            print("timed out waiting for PR table")
            return

        (OUT / "dashboard.svg").write_text(app.export_screenshot(), encoding="utf-8")
        print("wrote dashboard.svg")

        await pilot.press("d")
        await pilot.pause(0.5)
        for _ in range(40):
            await pilot.pause(0.25)
            screen = app.screen
            if type(screen).__name__ == "PRDetailScreen":
                try:
                    if screen.query_one("#detail-scroll").display:
                        break
                except Exception:
                    pass
        (OUT / "details.svg").write_text(app.export_screenshot(), encoding="utf-8")
        print("wrote details.svg")
        await pilot.press("escape")
        await pilot.pause(0.3)

        await pilot.press("t")
        await pilot.pause(0.5)
        (OUT / "stats.svg").write_text(app.export_screenshot(), encoding="utf-8")
        print("wrote stats.svg")
        await pilot.press("escape")
        await pilot.pause(0.3)

        await pilot.press("e")
        await pilot.pause(0.5)
        (OUT / "repos.svg").write_text(app.export_screenshot(), encoding="utf-8")
        print("wrote repos.svg")
        await pilot.press("escape")
        await pilot.pause(0.2)
        await pilot.press("q")


if __name__ == "__main__":
    asyncio.run(capture())
    for path in sorted(OUT.glob("*.svg")):
        print(f"  {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")
