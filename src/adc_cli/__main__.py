"""ADC CLI — orchestrates generate / audit / refine / config / setup-vscode."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

CONFIG_PATH = Path.home() / ".adcconfig.json"
DEFAULT_PROMPTS = {
    "generate": "code_generator.md",
    "audit": "auditor.md",
    "refine": "refiner.md",
}
ROLE_FILES = {
    "generate": "code_generator.md",
    "audit": "auditor.md",
    "refine": "refiner.md",
}


# ADC-IMPLEMENTS: <adc-cli-datamodel-02>
class ADCConfig(BaseModel):
    """Structure of ~/.adcconfig.json."""

    default_agent: str = "openai"
    task_agents: dict[str, str] = Field(
        default_factory=lambda: {
            "generate": "openai",
            "audit": "openai",
            "refine": "openai",
        }
    )
    models: dict[str, str] = Field(
        default_factory=lambda: {
            "openai": "gpt-4o",
            "anthropic": "claude-3-sonnet-20240229",
            "gemini": "gemini-1.5-pro-latest",
        }
    )


# ADC-IMPLEMENTS: <adc-cli-datamodel-01>
class AIProvider(ABC):
    """Interface every AI provider must satisfy."""

    name: str
    description: str

    @abstractmethod
    def initialize(self) -> bool:
        """Set up the client (typically load an API key)."""

    @abstractmethod
    def generate(self, system_prompt: str, user_content: str, model: str) -> str:
        """Generate content from system + user prompts."""


# ADC-IMPLEMENTS: <adc-cli-datamodel-01>
class OpenAIAgent(AIProvider):
    name = "openai"
    description = "OpenAI Chat Completions API"

    def __init__(self) -> None:
        self._client: Any = None

    def initialize(self) -> bool:
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            return False
        try:
            openai = importlib.import_module("openai")
        except ImportError:
            return False
        self._client = openai.OpenAI(api_key=key)
        return True

    def generate(self, system_prompt: str, user_content: str, model: str) -> str:
        assert self._client is not None
        resp = self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        return resp.choices[0].message.content or ""


# ADC-IMPLEMENTS: <adc-cli-datamodel-01>
class AnthropicAgent(AIProvider):
    name = "anthropic"
    description = "Anthropic Messages API"

    def __init__(self) -> None:
        self._client: Any = None

    def initialize(self) -> bool:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            return False
        try:
            anthropic = importlib.import_module("anthropic")
        except ImportError:
            return False
        self._client = anthropic.Anthropic(api_key=key)
        return True

    def generate(self, system_prompt: str, user_content: str, model: str) -> str:
        assert self._client is not None
        resp = self._client.messages.create(
            model=model,
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
        return "\n".join(parts)


# ADC-IMPLEMENTS: <adc-cli-datamodel-01>
class GeminiAgent(AIProvider):
    name = "gemini"
    description = "Google Gemini generative AI"

    def __init__(self) -> None:
        self._ready = False

    def initialize(self) -> bool:
        key = os.environ.get("GOOGLE_API_KEY")
        if not key:
            return False
        try:
            genai = importlib.import_module("google.generativeai")
        except ImportError:
            return False
        genai.configure(api_key=key)
        self._genai = genai
        self._ready = True
        return True

    def generate(self, system_prompt: str, user_content: str, model: str) -> str:
        assert self._ready
        m = self._genai.GenerativeModel(model, system_instruction=system_prompt)
        return m.generate_content(user_content).text or ""


PROVIDER_CLASSES: dict[str, type[AIProvider]] = {
    "openai": OpenAIAgent,
    "anthropic": AnthropicAgent,
    "gemini": GeminiAgent,
}


def load_config(path: Path = CONFIG_PATH) -> ADCConfig:
    """Load ~/.adcconfig.json or return defaults."""
    # ADC-IMPLEMENTS: <adc-cli-datamodel-02>
    if not path.exists():
        return ADCConfig()
    return ADCConfig.model_validate_json(path.read_text(encoding="utf-8"))


def save_config(config: ADCConfig, path: Path = CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(config.model_dump_json(indent=2) + "\n", encoding="utf-8")


def get_provider(name: str) -> AIProvider:
    """Dynamically construct and initialize a named provider."""
    cls = PROVIDER_CLASSES.get(name)
    if cls is None:
        raise SystemExit(f"Unknown AI provider: {name!r}. Choose from: {', '.join(PROVIDER_CLASSES)}")
    agent = cls()
    if not agent.initialize():
        raise SystemExit(
            f"Failed to initialize provider {name!r}. "
            "Check that the SDK is installed and the API key env var is set."
        )
    return agent


def resolve_agent(config: ADCConfig, task: str, override: str | None) -> tuple[str, str]:
    """Return (provider_name, model) for a task."""
    name = override or config.task_agents.get(task) or config.default_agent
    model = config.models.get(name, "")
    return name, model


def load_qmd_files(contracts_path: Path) -> str:
    path = contracts_path
    files = sorted(path.glob("**/*.qmd")) if path.is_dir() else [path]
    if not files:
        raise SystemExit(f"No .qmd contracts found at {contracts_path}")
    chunks: list[str] = []
    for f in files:
        chunks.append(f"### FILE: {f}\n{f.read_text(encoding='utf-8')}")
    return "\n\n".join(chunks)


def load_code_tree(code_path: Path) -> str:
    chunks: list[str] = []
    for f in sorted(code_path.rglob("*")):
        if not f.is_file():
            continue
        if any(p.startswith(".") for p in f.parts):
            continue
        if f.suffix not in {".py", ".md", ".toml", ".txt", ".qmd", ".json", ".yml", ".yaml"}:
            continue
        try:
            chunks.append(f"### FILE: {f}\n{f.read_text(encoding='utf-8')}")
        except OSError:
            continue
    return "\n\n".join(chunks) if chunks else f"(no readable source under {code_path})"


def find_prompt(task: str, prompts_dir: Path | None) -> str:
    filename = ROLE_FILES[task]
    candidates: list[Path] = []
    if prompts_dir is not None:
        candidates.append(prompts_dir / filename)
    # package-adjacent roles/ (repo layout)
    here = Path(__file__).resolve()
    candidates.append(here.parents[2] / "roles" / filename)
    candidates.append(Path.cwd() / "roles" / filename)
    for c in candidates:
        if c.is_file():
            return c.read_text(encoding="utf-8")
    raise SystemExit(f"Prompt file {filename!r} not found. Pass --prompts <dir>.")


# ponytail: naive fence parser; use a real AST/markdown lib if agents invent wild formats
_FILE_HEADING = re.compile(
    r"^#{1,6}\s+`(?P<path>[^`]+)`\s*$|^#{1,6}\s+(?P<path2>[\w./\\-]+\.py)\s*$",
    re.MULTILINE,
)
_FENCE = re.compile(
    r"```(?P<lang>[\w.+-]*)(?::(?P<path>[\w./\\-]+))?\n(?P<body>.*?)```",
    re.DOTALL,
)


def parse_and_write_files(markdown: str, dest_root: Path = Path(".")) -> list[Path]:
    """Parse code-generator markdown into files and write them."""
    written: list[Path] = []
    pending_path: str | None = None
    pos = 0
    for m in _FENCE.finditer(markdown):
        # heading immediately before this fence?
        before = markdown[pos : m.start()]
        heading = None
        for hm in _FILE_HEADING.finditer(before):
            heading = hm.group("path") or hm.group("path2")
        path_str = m.group("path") or heading or pending_path
        pos = m.end()
        if not path_str:
            continue
        rel = Path(path_str)
        if rel.is_absolute() or ".." in rel.parts:
            continue
        out = dest_root / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(m.group("body"), encoding="utf-8")
        written.append(out)
        pending_path = None
    return written


def run_ai_task(
    task: str,
    system_prompt: str,
    user_content: str,
    config: ADCConfig,
    agent_override: str | None,
    model_override: str | None,
) -> str:
    name, model = resolve_agent(config, task, agent_override)
    if model_override:
        model = model_override
    if not model:
        raise SystemExit(f"No model configured for provider {name!r}")
    provider = get_provider(name)
    return provider.generate(system_prompt, user_content, model)


# ADC-IMPLEMENTS: <adc-cli-feature-01>
def cmd_generate(args: argparse.Namespace, config: ADCConfig) -> int:
    system = find_prompt("generate", Path(args.prompts) if args.prompts else None)
    contracts = load_qmd_files(Path(args.contracts))
    user = (
        "Generate all the code for the following ADC contracts.\n\n"
        f"{contracts}\n\n"
        "Output a markdown file tree, then each source file as a heading "
        "`path/to/file.py` followed by a fenced code block."
    )
    result = run_ai_task("generate", system, user, config, args.agent, args.model)
    written = parse_and_write_files(result, Path(args.output) if args.output else Path("."))
    if written:
        print(f"Wrote {len(written)} file(s):")
        for p in written:
            print(f"  {p}")
    else:
        # still show raw response so the user can copy manually
        print(result)
    return 0


# ADC-IMPLEMENTS: <adc-cli-feature-02>
def cmd_audit(args: argparse.Namespace, config: ADCConfig) -> int:
    system = find_prompt("audit", Path(args.prompts) if args.prompts else None)
    contracts = load_qmd_files(Path(args.contracts))
    code = load_code_tree(Path(args.code))
    user = (
        "Audit the following codebase against its design contracts.\n\n"
        f"## Contracts\n\n{contracts}\n\n## Source\n\n{code}"
    )
    print(run_ai_task("audit", system, user, config, args.agent, args.model))
    return 0


# ADC-IMPLEMENTS: <adc-cli-feature-03>
def cmd_refine(args: argparse.Namespace, config: ADCConfig) -> int:
    system = find_prompt("refine", Path(args.prompts) if args.prompts else None)
    contracts = load_qmd_files(Path(args.contracts))
    user = f"Analyze and refine these ADC contracts:\n\n{contracts}"
    print(run_ai_task("refine", system, user, config, args.agent, args.model))
    return 0


# ADC-IMPLEMENTS: <adc-cli-feature-04>
def cmd_config(args: argparse.Namespace, config: ADCConfig) -> int:
    path = Path(args.config_path) if getattr(args, "config_path", None) else CONFIG_PATH
    if args.list:
        print(json.dumps(config.model_dump(), indent=2))
        return 0
    changed = False
    if args.set_default:
        config.default_agent = args.set_default
        changed = True
    if args.set_generate:
        config.task_agents["generate"] = args.set_generate
        changed = True
    if args.set_audit:
        config.task_agents["audit"] = args.set_audit
        changed = True
    if args.set_refine:
        config.task_agents["refine"] = args.set_refine
        changed = True
    if not changed:
        print("Nothing to do. Use --list, --set-default, --set-generate, --set-audit, or --set-refine.", file=sys.stderr)
        return 1
    save_config(config, path)
    print(f"Updated {path}")
    return 0


# ADC-IMPLEMENTS: <adc-cli-feature-05>
def cmd_setup_vscode(args: argparse.Namespace, config: ADCConfig) -> int:
    del config  # unused
    target = Path(args.target_dir)
    vscode = target / ".vscode"
    vscode.mkdir(parents=True, exist_ok=True)
    tasks = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "ADC: Generate",
                "type": "shell",
                "command": "adc generate --contracts ${input:contractsDir}",
                "problemMatcher": [],
            },
            {
                "label": "ADC: Audit",
                "type": "shell",
                "command": "adc audit --contracts ${input:contractsDir} --code ${input:codeDir}",
                "problemMatcher": [],
            },
            {
                "label": "ADC: Refine",
                "type": "shell",
                "command": "adc refine --contracts ${input:contractsDir}",
                "problemMatcher": [],
            },
        ],
        "inputs": [
            {
                "id": "contractsDir",
                "type": "promptString",
                "description": "Path to ADC contracts",
                "default": "contracts",
            },
            {
                "id": "codeDir",
                "type": "promptString",
                "description": "Path to source code",
                "default": "src",
            },
        ],
    }
    out = vscode / "tasks.json"
    out.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    return 0


# ADC-IMPLEMENTS: <adc-cli-agent-01>
# ADC-IMPLEMENTS: <adc-cli-impl-01>
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="adc",
        description="Agent Design Contracts (ADC) CLI Tool",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate code from ADC contracts")
    gen.add_argument("--contracts", required=True, help="Path to .qmd file or directory")
    gen.add_argument("--prompts", help="Directory with custom role prompts")
    gen.add_argument("--agent", choices=sorted(PROVIDER_CLASSES), help="AI provider override")
    gen.add_argument("--model", help="Model override")
    gen.add_argument("--output", default=".", help="Root directory for written files")
    gen.set_defaults(func=cmd_generate)

    audit = sub.add_parser("audit", help="Audit code against contracts")
    audit.add_argument("--contracts", required=True)
    audit.add_argument("--code", required=True)
    audit.add_argument("--prompts")
    audit.add_argument("--agent", choices=sorted(PROVIDER_CLASSES))
    audit.add_argument("--model")
    audit.set_defaults(func=cmd_audit)

    refine = sub.add_parser("refine", help="Refine ADC contracts")
    refine.add_argument("--contracts", required=True)
    refine.add_argument("--prompts")
    refine.add_argument("--agent", choices=sorted(PROVIDER_CLASSES))
    refine.add_argument("--model")
    refine.set_defaults(func=cmd_refine)

    cfg = sub.add_parser("config", help="View or update ~/.adcconfig.json")
    cfg.add_argument("--list", action="store_true")
    cfg.add_argument("--set-default", dest="set_default", metavar="AGENT")
    cfg.add_argument("--set-generate", dest="set_generate", metavar="AGENT")
    cfg.add_argument("--set-audit", dest="set_audit", metavar="AGENT")
    cfg.add_argument("--set-refine", dest="set_refine", metavar="AGENT")
    cfg.set_defaults(func=cmd_config)

    vs = sub.add_parser("setup-vscode", help="Create .vscode/tasks.json")
    vs.add_argument("--target-dir", default=".", dest="target_dir")
    vs.set_defaults(func=cmd_setup_vscode)

    return parser


# ADC-IMPLEMENTS: <adc-cli-agent-01>
def main(argv: list[str] | None = None) -> int:
    # 1. Command Parsing
    parser = build_parser()
    args = parser.parse_args(argv)
    # 2. Configuration Loading
    config = load_config()
    # 3–6. Context assembly, provider orchestration, response handling, output
    return int(args.func(args, config))


if __name__ == "__main__":
    raise SystemExit(main())
