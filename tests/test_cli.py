"""Parity tests for adc CLI commands (adc-tool-adc-001)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from adc_cli.__main__ import (
    ADCConfig,
    main,
    parse_and_write_files,
    save_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"


def test_generate_command(tmp_path: Path) -> None:
    fake_md = (
        "### File tree\n\n- `pkg/hello.py`\n\n"
        "### `pkg/hello.py`\n"
        "```python\nprint('hi')\n```\n"
    )
    with patch("adc_cli.__main__.run_ai_task", return_value=fake_md) as run:
        rc = main(
            [
                "generate",
                "--contracts",
                str(CONTRACTS),
                "--output",
                str(tmp_path),
            ]
        )
    assert rc == 0
    run.assert_called_once()
    assert (tmp_path / "pkg" / "hello.py").read_text() == "print('hi')\n"


def test_audit_command(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("adc_cli.__main__.run_ai_task", return_value="## 1. Parity Check\nOK") as run:
        rc = main(
            [
                "audit",
                "--contracts",
                str(CONTRACTS),
                "--code",
                str(ROOT / "src"),
            ]
        )
    assert rc == 0
    run.assert_called_once()
    assert "Parity Check" in capsys.readouterr().out


def test_refine_command(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("adc_cli.__main__.run_ai_task", return_value="Refine suggestion") as run:
        rc = main(["refine", "--contracts", str(CONTRACTS)])
    assert rc == 0
    run.assert_called_once()
    assert "Refine suggestion" in capsys.readouterr().out


def test_config_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg_path = tmp_path / ".adcconfig.json"
    monkeypatch.setattr("adc_cli.__main__.CONFIG_PATH", cfg_path)
    save_config(ADCConfig(), cfg_path)

    rc = main(["config", "--set-default", "anthropic", "--set-generate", "gemini"])
    assert rc == 0
    data = json.loads(cfg_path.read_text())
    assert data["default_agent"] == "anthropic"
    assert data["task_agents"]["generate"] == "gemini"

    rc = main(["config", "--list"])
    assert rc == 0


def test_setup_vscode_command(tmp_path: Path) -> None:
    rc = main(["setup-vscode", "--target-dir", str(tmp_path)])
    assert rc == 0
    tasks = json.loads((tmp_path / ".vscode" / "tasks.json").read_text())
    labels = {t["label"] for t in tasks["tasks"]}
    assert labels == {"ADC: Generate", "ADC: Audit", "ADC: Refine"}


def test_parse_and_write_files_path_in_fence(tmp_path: Path) -> None:
    md = "```python:src/foo.py\nx = 1\n```\n"
    written = parse_and_write_files(md, tmp_path)
    assert written == [tmp_path / "src" / "foo.py"]
    assert (tmp_path / "src" / "foo.py").read_text() == "x = 1\n"


def test_load_config_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("adc_cli.__main__.CONFIG_PATH", tmp_path / "missing.json")
    from adc_cli.__main__ import load_config

    cfg = load_config()
    assert cfg.default_agent == "openai"
    assert "generate" in cfg.task_agents


def test_provider_initialize_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from adc_cli.__main__ import OpenAIAgent

    assert OpenAIAgent().initialize() is False


if __name__ == "__main__":
    # ponytail: one runnable check without requiring pytest install for smoke
    sys.path.insert(0, str(ROOT / "src"))
    fake = MagicMock()
    print("smoke: parse_and_write_files")
    d = Path("/tmp/adc_cli_smoke")
    d.mkdir(exist_ok=True)
    outs = parse_and_write_files("### `a.py`\n```python\n1\n```\n", d)
    assert outs and outs[0].read_text() == "1\n"
    print("ok")
