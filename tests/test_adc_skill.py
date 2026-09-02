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
    "iac.md",
    "writer.md",
    "generator.md",
    "auditor.md",
    "refiner.md",
)

MODES = ("write", "generate", "audit", "refine")
IAC_BLOCK_TYPES = ("Infrastructure", "Resource")
IAC_KEYWORDS = ("Provider / Tool", "Parent:", "ADC-IMPLEMENTS")
IAC_TOOLS = ("aws-cdk", "terraform", "cloudformation")
IAC_DETECTION_SIGNALS = ("cdk.json", "*.tf", "template.yaml")


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


def test_schema_is_standalone_file() -> None:
    schema = REFS / "schema.md"
    assert schema.is_file(), "schema.md must be a regular file (not symlink)"
    assert not schema.is_symlink(), "schema.md must not symlink to adc-schema.qmd"


def test_schema_documents_iac_block_types() -> None:
    text = (REFS / "schema.md").read_text(encoding="utf-8")
    for block_type in IAC_BLOCK_TYPES:
        assert f"[{block_type}:" in text, f"schema.md must document [{block_type}: ...]"
    for kw in IAC_KEYWORDS:
        assert kw in text, f"schema.md must mention {kw!r}"


def test_iac_reference_exists() -> None:
    path = REFS / "iac.md"
    assert path.is_file(), f"missing {path}"
    text = path.read_text(encoding="utf-8")
    assert len(text) > 500, "iac.md must be substantive"
    for tool in IAC_TOOLS:
        assert tool in text, f"iac.md must document {tool}"
    for signal in IAC_DETECTION_SIGNALS:
        assert signal in text, f"iac.md must mention detection signal {signal!r}"
    assert "ADC-IMPLEMENTS" in text


def test_skill_mentions_iac() -> None:
    text = SKILL_MD.read_text(encoding="utf-8").lower()
    assert "infrastructure" in text or "iac" in text
    assert "iac.md" in text
    body = SKILL_MD.read_text(encoding="utf-8")
    assert "[Infrastructure]" in body or "Infrastructure" in body


def test_writer_documents_iac_authoring() -> None:
    text = (REFS / "writer.md").read_text(encoding="utf-8")
    assert "Infrastructure" in text
    assert "Resource" in text
    assert "iac.md" in text
    assert "Parent" in text
    assert "Provider / Tool" in text


def test_generator_documents_iac_generation() -> None:
    text = (REFS / "generator.md").read_text(encoding="utf-8")
    assert "Infrastructure" in text
    assert "Resource" in text
    assert "iac.md" in text
    assert "ADC-IMPLEMENTS" in text


def test_auditor_documents_iac_checks() -> None:
    text = (REFS / "auditor.md").read_text(encoding="utf-8")
    assert "Infrastructure" in text
    assert "iac.md" in text
    assert "Infrastructure Parity" in text or "Infrastructure Drift" in text


def test_refiner_documents_iac_heuristics() -> None:
    text = (REFS / "refiner.md").read_text(encoding="utf-8")
    assert "Infrastructure" in text
    assert "iac.md" in text
    assert "Parent" in text


def test_all_mode_refs_link_to_iac() -> None:
    for name in ("writer.md", "generator.md", "auditor.md", "refiner.md"):
        text = (REFS / name).read_text(encoding="utf-8")
        assert "iac.md" in text, f"{name} must link to iac.md"


def test_schema_links_to_iac() -> None:
    text = (REFS / "schema.md").read_text(encoding="utf-8")
    assert "iac.md" in text
