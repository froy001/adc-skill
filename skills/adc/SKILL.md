---
name: adc
description: Agent Design Contracts (ADC) write .qmd contracts from a prompt, generate application code and IaC (CDK/Terraform/CloudFormation), audit parity/drift, refine contracts. Use when the user invokes /adc or mentions ADC, contract_id, ADC-IMPLEMENTS, Infrastructure, Resource, or .qmd design blocks.
disable-model-invocation: true
---

# ADC — Agent Design Contracts

You run the ADC loop in the **current workspace** using Read/Write tools. No CLI, no extra API keys.

## Pick a mode

| Mode | User intent | Read next |
|------|-------------|-----------|
| **write** | New idea or prompt → contract | [writer.md](references/writer.md) |
| **generate** | Contracts → code | [generator.md](references/generator.md) |
| **audit** | Check code vs contracts | [auditor.md](references/auditor.md) |
| **refine** | Improve contracts | [refiner.md](references/refiner.md) |

If unclear, ask once: write / generate / audit / refine — then proceed.

All modes support `[Infrastructure]` and `[Resource]` blocks for IaC.

Always read [schema.md](references/schema.md) before acting. For IaC blocks, also read [iac.md](references/iac.md).

## Defaults

- Contracts: `contracts/` (create if missing)
- Output contract path: `contracts/<contract_id>.qmd`
- Source for audit/generate: Parity **Implementation Scope** paths; if none, `src/`
- IaC output: Parity **Implementation Scope** on `[Infrastructure]` / `[Resource]` blocks (see [iac.md](references/iac.md))

## ID rules (write mode)

Before writing or extending a contract, scan workspace `**/*.qmd` for existing `contract_id` values and `<block-id>` tokens.

- `contract_id`: `module_name-unique-identifier-adc-NNN` — increment `NNN` to avoid collision
- Block IDs: `<prefix-kind-nn>` — globally unique in the workspace; never reuse
- Extend an existing `.qmd` when the prompt clearly targets it; mint IDs only for new blocks
- Do not rewrite existing IDs unless the user asked

## Error handling

- Vague write prompt → ask; no TBD skeletons
- No `.qmd` for generate/audit/refine → stop; do not invent a contract
- Audit findings → report only; fix code only if asked
- Refine → apply `.qmd` edits only if asked
- Infra blocks with no IaC tool in workspace → ask once (see [iac.md](references/iac.md))
- Contract **Provider / Tool** conflicts with workspace → stop; report mismatch
