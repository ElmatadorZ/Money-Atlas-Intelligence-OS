"""The Claude Code plugin package.

`claude plugin marketplace add ElmatadorZ/Money-Atlas-Intelligence-OS` reads
.claude-plugin/marketplace.json; `claude plugin install
money-atlas-intelligence-os@elmatadorz-money-atlas` then loads
skills/money-atlas-intelligence-os/SKILL.md and the files it references.
The root files stay canonical, so the copy must never drift.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "SKILL.md"
PLUGIN = ROOT / ".claude-plugin" / "plugin.json"
MARKET = ROOT / ".claude-plugin" / "marketplace.json"
SYNC = "run: python tools/sync_plugin_skill.py"

_spec = importlib.util.spec_from_file_location("sync", ROOT / "tools" / "sync_plugin_skill.py")
sync = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync)


def _load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def _files(base):
    return {p.relative_to(base).as_posix(): p.read_bytes()
            for p in base.rglob("*") if p.is_file() and "__pycache__" not in p.parts}


def test_plugin_skill_copy_is_identical():
    copy = ROOT / "skills" / sync.skill_name()
    assert (copy / "SKILL.md").exists(), f"plugin skill copy missing; {SYNC}"
    expected = {f: (ROOT / f).read_bytes() for f in sync.FILES}
    for d in sync.DIRS:
        expected.update({f"{d}/{k}": v for k, v in _files(ROOT / d).items()})
    assert _files(copy) == expected, f"plugin copy differs from the root files; {SYNC}"


def test_plugin_copy_carries_every_file_skill_md_references():
    refs = set(re.findall(r"`([\w./-]+\.(?:txt|md)|examples/[\w/-]+/?)`", SKILL.read_text(encoding="utf-8")))
    refs.discard("SKILL.md")
    copy = ROOT / "skills" / sync.skill_name()
    missing = [r for r in sorted(refs) if not (copy / r.rstrip("/")).exists()]
    assert not missing, f"plugin copy lacks {missing}; add them to tools/sync_plugin_skill.py"


def test_plugin_name_matches_skill_name():
    assert _load(PLUGIN)["name"] == sync.skill_name()


def test_marketplace_points_at_the_plugin():
    market, plugin = _load(MARKET), _load(PLUGIN)
    assert market["name"] and market["owner"]["name"]
    entries = {p["name"]: p for p in market["plugins"]}
    assert plugin["name"] in entries
    src = entries[plugin["name"]]["source"]
    assert ".." not in src and (ROOT / src / ".claude-plugin" / "plugin.json").exists()


def test_version_is_set_in_one_place_and_matches_skill():
    market, plugin = _load(MARKET), _load(PLUGIN)
    assert re.fullmatch(r"\d+\.\d+\.\d+", plugin["version"])
    assert all("version" not in p for p in market["plugins"])
    skill_v = re.search(r'^version:\s*"?([^"\n]+)"?', SKILL.read_text(encoding="utf-8"), re.M).group(1)
    assert plugin["version"].startswith(skill_v.strip() + ".")


def test_plugin_license_matches_repository():
    assert _load(PLUGIN)["license"] == "Apache-2.0"
    assert "Apache License" in (ROOT / "LICENSE").read_text(encoding="utf-8")
