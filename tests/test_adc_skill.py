"""Structure tests for skills/adc/ (no LLM)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "adc"
SKILL_MD = SKILL_DIR / "SKILL.md"
REFS = SKILL_DIR / "references"

REQUIRED_REFS = (
    "schema.md",
    "writer.md",
    "generator.md",
    "auditor.md",
    "refiner.md",
)

MODES = ("write", "generate", "audit", "refine")


def _frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert m, "SKILL.md missing YAML frontmatter"
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip('"')
    return out


def test_skill_directory_exists() -> None:
    assert SKILL_DIR.is_dir(), f"missing {SKILL_DIR}"


def test_skill_frontmatter() -> None:
    text = SKILL_MD.read_text(encoding="utf-8")
    fm = _frontmatter(text)
    assert fm.get("name") == "adc"
    desc = fm.get("description", "").lower()
    for mode in MODES:
        assert mode in desc, f"description must mention {mode}"


def test_skill_body_names_all_modes() -> None:
    body = SKILL_MD.read_text(encoding="utf-8").split("---", 2)[-1].lower()
    for mode in MODES:
        assert mode in body, f"SKILL.md body must mention {mode}"


def test_reference_files_exist_and_nonempty() -> None:
    assert REFS.is_dir(), f"missing {REFS}"
    for name in REQUIRED_REFS:
        path = REFS / name
        assert path.exists(), f"missing {path}"
        assert path.stat().st_size > 0, f"empty {path}"


def test_schema_is_symlink_to_adc_schema() -> None:
    schema = REFS / "schema.md"
    assert schema.is_symlink(), "schema.md must symlink to adc-schema.qmd"
    target = (schema.parent / schema.readlink()).resolve()
    assert target == (ROOT / "adc-schema.qmd").resolve()
