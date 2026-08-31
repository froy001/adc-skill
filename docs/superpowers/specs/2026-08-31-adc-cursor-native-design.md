# ADC as a Cursor-native skill

## Problem

ADC (schema, writer, generator, auditor, refiner) only lives in this repo. Using it from another workspace means copying files or running the Python CLI (extra API keys, Python-only generate, VSCode tasks). Cursor already has the model and file tools. The missing piece is the methodology, available in every workspace.

## Goal

One personal Cursor skill, `/adc`, that runs the full ADC loop in **any** workspace on this machine: write a contract from a prompt, generate code, audit, refine.

## Constraints

- Available in every workspace (personal skill, not project `.cursor/`).
- Native Cursor only: skills + the agent’s Read/Write. No MCP, no plugin, no wrapping `adc` CLI.
- Prefer simplicity: one skill, not four. Cursor’s agent does the LLM work.
- Existing Python CLI is unchanged and out of scope.

## Architecture

Source of truth: `skills/adc/` in this repo. Install is a symlink:

```bash
ln -sf "$(pwd)/skills/adc" ~/.cursor/skills/adc
```

After that, `/adc` is available in every workspace. The agent reads the skill, routes to a mode, and uses Cursor tools against the **current workspace**. No `~/.adcconfig.json`, no extra network.

`disable-model-invocation: true` — the skill loads only when the user types `/adc` (or attaches it). It does not auto-fire because `.qmd` files exist.

## Skill layout

```
skills/adc/
  SKILL.md                 # router, ID rules, default paths
  references/schema.md     # symlink to repo adc-schema.qmd (one canonical schema)
  references/writer.md     # prompt → well-formed contract
  references/generator.md  # contract → code (target-project stack)
  references/auditor.md    # audit report (from roles/auditor.md)
  references/refiner.md    # contract refinement (from roles/refiner.md)
```

`SKILL.md` stays short. It picks a mode, then the agent reads `references/schema.md` plus that mode’s file only.

Frontmatter:

- `name: adc`
- `description`: third person, WHAT + WHEN, trigger terms write / generate / audit / refine / contract / `.qmd` / ADC-IMPLEMENTS.

## Routing

| Mode | When | Result |
|------|------|--------|
| **write** | Idea or prompt; no usable contract yet | Well-formed `contracts/<contract_id>.qmd` |
| **generate** | Contracts exist; user wants code | Code matching the target project’s language and layout |
| **audit** | User wants a parity/drift check | Three-section report in chat |
| **refine** | User wants the contract improved | Suggestions; apply to `.qmd` only if asked |

If mode is unclear, ask once (write / generate / audit / refine), then proceed.

## Writer

Input is the user’s prompt (plus any `@` files). Output is a complete ADC file, not a TBD skeleton.

**New vs extend:** if `contracts/` already has a `.qmd` that the prompt is clearly about, edit that file and mint IDs only for new blocks. Otherwise write one new file. Do not split one prompt into multiple contract files unless the user asked.

**Front matter defaults** for a new file:

- `status: proposed`
- `version: 1.0`
- `created_date` / `last_updated`: today (`YYYY-MM-DD`)
- `author`: from the prompt if given, else `git config user.name`, else `unknown`
- `title` / `contract_id`: derived from the prompt’s module name

**Body:**

- Typed design blocks: `### [Type: Name] <ID>`.
- **Parity** on every implementable block (`Agent`, `DataModel`, `Feature`, and other implementable types; not `Rationale`).
- Default path: `contracts/<contract_id>.qmd`. Create `contracts/` if missing.

### ID management

Before writing, scan workspace `**/*.qmd` for existing `contract_id` values and `<block-id>` tokens.

- `contract_id`: `module_name-unique-identifier-adc-NNN` (schema form). Increment `NNN` so it does not collide.
- Block IDs: `<prefix-kind-nn>`, stable and globally unique in that workspace. Derive `prefix` from the contract’s module; never reuse an id already present.
- Do not rewrite IDs on existing blocks unless the user asked to.

If the prompt is too vague to fill required blocks, ask for the missing bits. Do not emit placeholder TBDs.

## Generator

- Load `.qmd` contracts (default directory `contracts/`).
- Follow each block’s Parity **Implementation Scope**. Create that directory if missing; do not dump files at repo root.
- Match the **target workspace**: language, layout, stack inferred from existing files. Schema, Parity, and `ADC-IMPLEMENTS: <ID>` (and `ADC-USES-PROMPT:` where relevant) stay required. Comment/marker syntax follows that language.
- If the tree is empty and language is unclear, ask once.
- Honor Parity **Tests** paths: add or update the listed tests so they cover the contract.

This replaces the Python-only assumptions in `roles/code_generator.md`.

## Auditor

Same contract as `roles/auditor.md`: one Markdown report in chat, sections in order:

1. Parity Check
2. Design Drift Report
3. Architectural & Technical Roadblock Analysis

Load contracts plus source (Parity scopes, or `src/` if present). Dangling markers and unimplemented blocks are findings, not auto-fixes. Do not write files unless the user asked to save the report. If no `.qmd` is found, stop and say so.

## Refiner

Same contract as `roles/refiner.md`: completeness, consistency, feasibility, pattern alignment; each suggestion is original quote + issue + concrete revision. Apply edits to `.qmd` files only when the user asked to apply.

## Data flow

1. User: `/adc` + prompt (optional `@` files).
2. Agent reads `SKILL.md` → mode → `schema.md` + mode reference.
3. All reads/writes are in the current workspace, paths workspace-relative.
4. **write** scans IDs, writes or updates `contracts/*.qmd` (one new file per prompt unless extending an existing contract).
5. **generate** writes/updates source under Parity scopes.
6. **audit** prints the report.
7. **refine** prints suggestions; writes `.qmd` only if asked.

## Error handling

| Situation | Behavior |
|-----------|----------|
| Mode unclear | Ask once |
| Write prompt too vague | Ask; do not write TBD skeletons |
| ID collision | Next free id; never reuse or silently overwrite |
| Generate/audit/refine with no `.qmd` | Stop; do not invent a contract |
| Generate Parity path missing | Create the directory |
| Generate language unclear | Infer from files; if empty, ask once |
| Audit findings | Report only, unless user asked to fix |
| Skill not installed | `/adc` missing; README one-liner for the symlink |

## Out of scope

- Python CLI (`src/adc_cli`), `~/.adcconfig.json`, `adc setup-vscode`.
- Cursor plugin / MCP / marketplace publish.
- Auto-invoke without `/adc`.
- Registry file for IDs (scan is enough).
- Saving audit reports by default.

## Testing

**Automated (this repo):** one small test that reads `skills/adc/` and asserts:

- `SKILL.md` YAML has `name: adc` and a description that names write, generate, audit, refine.
- `references/schema.md`, `writer.md`, `generator.md`, `auditor.md`, `refiner.md` exist and are non-empty.
- `SKILL.md` body names all four modes.

**Smoke (this machine):** symlink installed; open a workspace that is not this repo; `/adc` with a short prompt; confirm `contracts/*.qmd` exists, IDs unique, blocks match the schema.

No extra LLM calls in CI. No fixture framework.

## Install / docs

README (this repo) gets a short “Cursor skill” section: the symlink command and example `/adc` prompts for write, generate, audit, refine. Do not require copying `adc-schema.qmd` or `roles/` into other projects.
