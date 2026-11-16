"""Copy the canonical skill into the Claude Code plugin layout.

Run after editing SKILL.md or any file it loads:  python tools/sync_plugin_skill.py

The plugin loads skills/<name>/SKILL.md, and SKILL.md loads its reference files
(full_mode.txt, light_mode.txt, architecture.md, system_prompt.txt,
examples/worked/) relative to its own folder, so those are copied too.
tests/test_plugin_package.py fails until the copy matches byte for byte.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = ["SKILL.md", "full_mode.txt", "light_mode.txt", "architecture.md", "system_prompt.txt"]
DIRS = ["examples/worked"]


def skill_name() -> str:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    return re.search(r'^name:\s*"?([^"\n]+)"?', text, re.M).group(1).strip()


def main() -> None:
    dest = ROOT / "skills" / skill_name()
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for f in FILES:
        shutil.copyfile(ROOT / f, dest / f)
    for d in DIRS:
        shutil.copytree(ROOT / d, dest / d)
    print(f"synced {len(FILES)} files + {', '.join(DIRS)} -> {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
