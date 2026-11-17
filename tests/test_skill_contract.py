"""The SKILL.md contract.

A skill is installed and run by a model, so its guarantees live in the markdown,
not only in the Python. These tests assert the promises the skill makes about
itself hold in the file itself — the same properties tools/validate_skill.py
checks, kept here so a contributor running pytest sees them too.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "SKILL.md"


def _split():
    text = SKILL.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "frontmatter must be present and delimited"
    return yaml.safe_load(m.group(1)), text[m.end():]


def test_canonical_filename():
    # Strict skill-discovery tooling looks for uppercase SKILL.md.
    assert SKILL.exists(), "SKILL.md must exist at the repository root"


def test_frontmatter_required_and_recommended_fields():
    fm, _ = _split()
    for f in ("name", "description"):
        assert f in fm, f"frontmatter must declare '{f}'"
    for f in ("license", "version"):
        assert f in fm, f"frontmatter should declare '{f}'"
    assert str(fm["license"]).lower().replace(" ", "-") == "apache-2.0"


def test_name_is_slug_safe():
    fm, _ = _split()
    assert re.fullmatch(r"[a-z0-9][a-z0-9-]*", str(fm["name"]))


def test_metadata_declares_scope_and_compatibility():
    fm, _ = _split()
    meta = fm.get("metadata", {})
    assert meta.get("compatibility"), "metadata.compatibility must state where it runs"
    assert meta.get("not_for"), "metadata.not_for must bound the skill's scope"


def test_body_requires_scenarios_and_invalidation():
    _, body = _split()
    assert re.search(r"scenario", body, re.I)
    assert re.search(r"invalidation", body, re.I)
    assert re.search(r"uncertaint|confidence", body, re.I)


def test_body_degrades_honestly_without_data():
    _, body = _split()
    assert re.search(r"insufficient|no live data|abstain", body, re.I), \
        "the skill must declare what it does when data is missing"


def test_body_declines_personalized_advice():
    _, body = _split()
    assert re.search(r"not.{0,20}(financial|investment) advice|does not issue", body, re.I)


# ---------------------------------------------------------------- v2.1
# A blind A/B test of v2.0 (evals/2026-11-16/) found answers written with the
# skill scored below answers written without it (141.0 vs 152.0 of 160): the
# full framework around concept questions, an SMC map forced onto questions with
# no price structure, confidence percentages with no basis, and a refusal to
# build trade levels from the price the user gave. These tests pin the fixes.

def _section(body, title):
    return body.split(f"## {title}", 1)[1].split("\n## ", 1)[0]


def _exists_case_exact(rel):
    here = ROOT
    for part in Path(rel.rstrip("/")).parts:
        if not here.is_dir() or part not in {p.name for p in here.iterdir()}:
            return False
        here = here / part
    return True


def test_every_referenced_file_exists_case_exact():
    _, body = _split()
    refs = set(re.findall(r"`([\w./-]+\.(?:txt|md)|examples/[\w/-]+/?)`", body))
    refs.discard("SKILL.md")
    assert len(refs) >= 4
    missing = [r for r in sorted(refs) if not _exists_case_exact(r)]
    assert not missing, missing


def test_description_does_not_demand_always_trigger():
    fm, _ = _split()
    assert not re.search(r"\bALWAYS trigger\b|do not skip", fm["description"], re.I)


def test_direct_mode_for_concept_questions():
    _, body = _split()
    act = _section(body, "ACTIVATION")
    for mode in ("**DIRECT**", "**LIGHT MODE**", "**FULL MODE**"):
        assert mode in act
    assert re.search(r"No banners, no scenarios, no confidence field", act)
    assert "concept question in the market framework" in _section(body, "FAILURE SYSTEM")


def test_market_core_has_five_moves():
    _, body = _split()
    core = _section(body, "MARKET CORE")
    assert len(re.findall(r"^\d\. \*\*", core, re.M)) == 5


def test_smc_layer_is_not_forced_without_structure_data():
    _, body = _split()
    smc = _section(body, "SMC LAYER")
    assert "Do not force it" in smc
    assert re.search(r"Without it: say in one line", smc)


def test_data_rules_label_every_figure():
    _, body = _split()
    rules = _section(body, "DATA RULES")
    for kind in ("**Given**", "**Last known**", "**Assumed**", "`[ASSUMED]`", "`[UNVERIFIED]`"):
        assert kind in rules
    assert "Abstain from facts, not from method" in rules


def test_confidence_is_grounded_not_a_bare_percentage():
    _, body = _split()
    assert "[X%]" not in body
    conf = _section(body, "CONFIDENCE RULES")
    assert "HIGH / MEDIUM / LOW" in conf
    assert re.search(r"percentage only when it is computed", conf)
    assert "not assessable" in conf


def test_personal_decisions_refuse_all_in_and_leverage():
    _, body = _split()
    personal = _section(body, "PERSONAL MONEY DECISIONS")
    assert re.search(r'Never endorse going "all in"', personal)
    assert "leverage" in personal and "position" in personal.lower()


def test_mode_reference_files_agree_with_skill():
    # full_mode.txt and light_mode.txt are loaded as references; they must not
    # reintroduce the bare confidence percentage the skill dropped.
    for f in ("full_mode.txt", "light_mode.txt", "system_prompt.txt", "session_boot.txt"):
        assert "X%" not in (ROOT / f).read_text(encoding="utf-8"), f


# ---------------------------------------------------------------- v2.2
# Round 2 left two misses: a "gold always rises with inflation" question answered
# as a plain explanation (no known/inferred split, a wrong 2022 detail), and an
# expired Thai tax deduction presented as current. These tests pin the fixes.

def test_market_myths_are_tested_not_explained():
    _, body = _split()
    act = _section(body, "ACTIVATION")
    assert "no claim to test" in act
    assert re.search(r"claim about how markets behave", act)
    assert re.search(r'"always" or "every time" happens is not DIRECT', act)


def test_historical_figures_and_changing_rules_are_dated():
    _, body = _split()
    rules = _section(body, "DATA RULES")
    assert "**Historical figures**" in rules and "describe the move without the" in rules
    assert "**Rules and products change.**" in rules
    assert "official source" in rules
    assert "without its date" in _section(body, "FAILURE SYSTEM")


def test_market_myths_are_answered_as_prose():
    # Round 3: the myth question routed to LIGHT came out with trading-desk banners
    # and lost proportion points. The Market Core still applies, as prose.
    _, body = _split()
    assert "without the LIGHT banners" in _section(body, "ACTIVATION")


# ---------------------------------------------------------------- v2.3
# A harder test (10 professional-level questions) found v2.2 described calculations the
# data allowed instead of doing them, refused a point forecast without giving the honest
# best estimate, and asserted that a recent event "has never happened".

def test_quantify_what_the_data_allows():
    _, body = _split()
    q = _section(body, "QUANTIFY WHAT THE DATA ALLOWS")
    for item in ("**Sizing and leverage**", "**Plans and portfolios**", "**Choices**",
                 "**Pricing formulas**", "**Point forecasts on request**"):
        assert item in q
    assert "do not just refuse" in q
    assert "Check the arithmetic" in q


def test_absence_claims_about_recent_history_are_dated():
    _, body = _split()
    assert re.search(r'never say something "has never happened"', _section(body, "DATA RULES"))


# ---------------------------------------------------------------- v2.3.1
# Proof run (evals/2026-11-17-proof/): proportion was the one criterion where no skill
# still won — 📍 banners on answers that were not asset reads, and "Layer 5" / "this
# framework" leaking into a refusal.

def test_internal_machinery_is_never_named_to_the_user():
    _, body = _split()
    act = _section(body, "ACTIVATION")
    assert "Speak the user's language, not the skill's." in act
    for term in ('"Layer 5"', '"this framework"', '"Market Core"'):
        assert term in act


def test_banners_only_for_asset_reads():
    _, body = _split()
    light = _section(body, "OUTPUT — LIGHT MODE")
    assert "only for a read on an asset or market" in light


def test_refusals_are_short_and_redirect():
    _, body = _split()
    fs = _section(body, "FAILURE SYSTEM")
    assert "front-running" in fs and "No framework" in fs


# ---------------------------------------------------------------- v2.4 (data agent)

def test_data_tools_section_binds_the_mcp_server():
    _, body = _split()
    dt = _section(body, "DATA TOOLS")
    for tool in ("get_quote", "get_candles", "get_macro_series", "market_snapshot",
                 "position_size", "paper_propose_order", "paper_orders"):
        assert f"`{tool}`" in dt
    assert "Fetch before you reason" in dt and "Quote the source and `as_of`" in dt
    assert "Orders are paper only" in dt and "Never say an order" in dt
    assert "Never fill the gap with a guess" in dt


def test_every_tool_the_skill_names_exists_on_the_server():
    from money_atlas_mcp.server import TOOLS
    _, body = _split()
    named = set(re.findall(r"`((?:get|paper|market|position)_[a-z_]+)`", _section(body, "DATA TOOLS")))
    assert named <= {t["name"] for t in TOOLS}
