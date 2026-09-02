# ADC skill: Infrastructure-as-Code generation

## Problem

The Cursor-native `/adc` skill supports the full ADC loop for **application code** — write contracts, generate source, audit parity, refine designs — but has no first-class support for **Infrastructure-as-Code (IaC)**. Users designing cloud stacks must either describe infra outside ADC syntax or manually map generic blocks (`[Feature]`, `[Tool]`) to Terraform, CDK, or CloudFormation without traceability conventions.

## Goal

Extend `skills/adc/` so the existing `/adc` modes (write, generate, audit, refine) also handle `[Infrastructure]` and `[Resource]` design blocks, emitting and auditing IaC artifacts with the same Parity + `ADC-IMPLEMENTS` traceability loop used for application code.

## Decisions (validated in brainstorming)

| Decision | Choice |
|----------|--------|
| IaC tools | **Multi-tool** — detect AWS CDK, Terraform, or CloudFormation from workspace; contract **Provider / Tool** resolves conflicts |
| Schema | **Hybrid** — new `[Infrastructure: Stack]` parent block + child `[Resource: ...]` blocks |
| Contract layout | **Both** — infra blocks in same `.qmd` as app blocks for small projects; separate infra contract linked via `[Reference]` for larger stacks |
| Skill modes | **Full loop** — write, generate, audit, refine all extended |
| Implementation approach | **Shared IaC reference** (`references/iac.md`) + thin hooks in existing mode files |

## Constraints

- MUST follow ADC syntax and structure (`skills/adc/references/schema.md`, README-adc.md conventions).
- Scope is **`skills/` only** in v1 — no changes to Python CLI, `roles/`, or root `adc-schema.qmd`.
- MUST document the addition within `skills/`.
- Existing `/adc` UX unchanged — no new command or sub-skill.

## Architecture

### New file: `skills/adc/references/iac.md`

Single source of truth for IaC semantics. All four mode reference files link here for shared rules:

1. **Stack detection** — infer tool from workspace signals.
2. **Block-to-artifact mapping** — how `[Infrastructure]` and `[Resource]` translate per tool.
3. **`ADC-IMPLEMENTS` marker syntax** — comment format per IaC language.
4. **Default Parity path conventions** — writer defaults when prompt omits paths.
5. **Validation expectations** — smoke-level tests (no full deploy).

### Updated files

| File | Change |
|------|--------|
| `skills/adc/SKILL.md` | Extend description and mode table to mention IaC blocks; link to `iac.md` |
| `skills/adc/references/schema.md` | Add `[Infrastructure]` and `[Resource]` block type definitions with Parity examples |
| `skills/adc/references/writer.md` | Infra authoring rules: co-locate vs split contracts, required fields, ID conventions |
| `skills/adc/references/generator.md` | IaC generation section: read `iac.md`, detect stack, emit under Parity scopes |
| `skills/adc/references/auditor.md` | Infrastructure parity and drift checks on IaC files |
| `skills/adc/references/refiner.md` | Infra completeness heuristics |

## Schema extension

### `[Infrastructure: Stack Name] <ID>`

Top-level stack definition. Implementable — requires Parity and `ADC-IMPLEMENTS` marker in generated IaC.

**Required sections:**

- **Provider / Tool:** `aws-cdk` | `terraform` | `cloudformation`
- **Region / Environment:** optional defaults
- **Dependencies:** references to other `[Infrastructure]` blocks or app blocks (e.g. Lambda consuming `[APIEndpoint]` outputs)

**Parity:**

- **Implementation Scope:** e.g. `infra/`, `terraform/`, `cdk/`
- **Configuration Scope:** e.g. `terraform/env/dev.tfvars`
- **Tests:** e.g. `tests/infra/test_stack.py`

### `[Resource: Resource Name] <ID>`

Atomic infra unit within a stack. Implementable — requires Parity and `ADC-IMPLEMENTS` marker.

**Required sections:**

- **Parent:** `<infrastructure-block-id>` — links resource to its stack
- **Type:** provider resource type (e.g. `aws_lambda_function`, `AWS::Lambda::Function`, CDK construct class)
- **Properties:** key-value design intent (not full HCL/YAML — the generator fills in syntax)
- **Dependencies:** other `<resource-id>` tokens
- **Outputs:** exported values for app code or downstream resources

**Parity:** file path or module within parent stack's **Implementation Scope**.

### Contract layout rules (writer)

- **Same contract:** when prompt describes a small/full-stack feature (app + infra together).
- **Split contract:** when prompt is infra-only or stack is large/complex. New file: `contracts/<module>-infra-adc-NNN.qmd`. Link to app contract via `[Reference: ...]` when both exist.

### ID conventions

Follow existing ADC rules. Suggested prefixes:

- Infrastructure: `<module>-infra-NN>` (e.g. `<todo-infra-01>`)
- Resource: `<module>-res-<kind>-NN>` (e.g. `<todo-res-lambda-01>`)

Glob workspace `**/*.qmd` before minting; never reuse IDs.

## Stack detection

| Workspace signal | Tool |
|------------------|------|
| `cdk.json` or `**/cdk/**/*.ts`, `**/cdk/**/*.py` | AWS CDK |
| `*.tf`, `terraform/` directory | Terraform |
| `template.yaml`, `*.cfn.yaml`, `cloudformation/` | CloudFormation |

**Resolution:** if contract **Provider / Tool** is set, it takes precedence over detection. If multiple tools detected and contract is silent, ask once. If contract tool conflicts with workspace, stop and report mismatch.

## Block-to-artifact mapping

| Block | CDK | Terraform | CloudFormation |
|-------|-----|-----------|----------------|
| `[Infrastructure]` | Stack/App construct class | root module (`main.tf` + backend) | root template |
| `[Resource]` | Construct instantiation | `resource` block | `Resources` entry |

## Traceability: `ADC-IMPLEMENTS` markers

Same format as application code: `ADC-IMPLEMENTS: <ID>`

| Format | Comment syntax |
|--------|----------------|
| CDK (Python) | `# ADC-IMPLEMENTS: <ID>` |
| CDK (TypeScript) | `// ADC-IMPLEMENTS: <ID>` |
| Terraform (HCL) | `# ADC-IMPLEMENTS: <ID>` |
| CloudFormation (YAML) | `# ADC-IMPLEMENTS: <ID>` |

Marker placed immediately before the resource, construct, or block implementing the design block.

## Mode behavior

### Write

- Author `[Infrastructure]` + `[Resource]` blocks with full Parity sections.
- Set **Provider / Tool** explicitly.
- Every `[Resource]` MUST have **Parent** pointing to an `[Infrastructure]` block.
- Refuse TBD skeletons; ask for missing resource types, environment, or tool if prompt is vague.

### Generate

- Read infra blocks from referenced contracts (follow `[Reference]` links).
- Detect or validate tool per stack detection rules.
- Emit IaC files under each block's Parity **Implementation Scope**.
- Add `ADC-IMPLEMENTS` markers per `iac.md`.
- App blocks in the same contract continue generating application code as today.

### Audit

Extend existing report with infrastructure checks:

1. **Infrastructure Parity Check** — scan IaC files for `ADC-IMPLEMENTS` markers; verify every `[Infrastructure]` / `[Resource]` block has a matching marker; report dangling markers and unimplemented blocks.
2. **Infrastructure Drift** — compare Properties, Dependencies, Outputs, and Type against generated IaC.
3. Existing architectural analysis applies to IaC (security groups open to world, missing encryption, etc.).

### Refine

Add infra-specific heuristics:

- Missing **Parent** on `[Resource]` blocks
- Orphan resources (Parent ID doesn't exist)
- Unspecified **Dependencies** when resource logically depends on another
- **Provider / Tool** mismatch with workspace
- Missing **Outputs** on resources that app blocks reference

## Data flow

```
Prompt → Writer → .qmd ([Infrastructure] + [Resource])
       → Generator → stack detection → IaC artifacts (with ADC-IMPLEMENTS)
       → Auditor → parity + drift report
       → Refiner → contract improvements
```

## Error handling

| Situation | Behavior |
|-----------|----------|
| Infra blocks present, no IaC tool in workspace | Ask once which tool to target |
| Contract **Provider / Tool** conflicts with workspace | Stop; report mismatch |
| `[Resource]` missing **Parent** | Writer refuses; refiner flags |
| No `.qmd` for generate/audit/refine | Stop (existing rule) |
| Vague prompt ("deploy to AWS") | Ask for resources, environment, tool |
| Multi-tool workspace | Prefer contract **Provider / Tool**; warn if ambiguous |

## Testing

Infra blocks require Parity **Tests** entries. Minimum smoke tests per tool:

| Tool | Test |
|------|------|
| Terraform | `terraform validate` against generated config |
| CDK | `cdk synth` asserting expected logical IDs |
| CloudFormation | template structure validation |

Full deploy/integration tests are out of scope for v1 (ponytail: smoke only).

## Example contract fragment

```markdown
### [Infrastructure: Todo API Stack] <todo-infra-01>
**Provider / Tool:** terraform
**Region:** us-east-1

**Parity:**
- **Implementation Scope:** `terraform/`
- **Configuration Scope:** `terraform/env/dev.tfvars`
- **Tests:** `tests/infra/test_terraform_validate.sh`

### [Resource: Lambda Execution Role] <todo-res-role-01>
**Parent:** `<todo-infra-01>`
**Type:** `aws_iam_role`
**Properties:**
- assume_role_policy: lambda.amazonaws.com
**Outputs:**
- role_arn

### [Resource: Todo Lambda] <todo-res-lambda-01>
**Parent:** `<todo-infra-01>`
**Type:** `aws_lambda_function`
**Properties:**
- runtime: python3.12
- handler: todo.handler
**Dependencies:** `<todo-res-role-01>`
**Outputs:**
- function_arn
```

## Out of scope (v1)

- Python CLI (`adc generate`) changes
- `roles/` prompt template updates
- Root `adc-schema.qmd` sync (deferred; skill `schema.md` is authoritative for Cursor users)
- Pulumi, Crossplane, Bicep, or other IaC tools
- Full deploy / integration test generation
- MCP or AWS API integration during generation

## Success criteria

1. `/adc` write mode produces valid `[Infrastructure]` / `[Resource]` blocks following ADC syntax.
2. `/adc` generate mode emits CDK, Terraform, or CloudFormation artifacts with `ADC-IMPLEMENTS` markers based on workspace detection.
3. `/adc` audit mode reports infra parity and drift alongside app code checks.
4. `/adc` refine mode suggests improvements for incomplete infra contracts.
5. All additions documented in `skills/adc/` (`iac.md`, updated `schema.md`, updated `SKILL.md`).
