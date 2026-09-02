# ADC Infrastructure-as-Code Reference

Shared rules for `[Infrastructure]` and `[Resource]` blocks. All ADC modes that touch IaC MUST read this file.

Schema block definitions: [schema.md](schema.md)

## Stack detection

Detect IaC tool from workspace signals:

| Signal | Tool |
|--------|------|
| `cdk.json` or `**/cdk/**/*.ts`, `**/cdk/**/*.py` | `aws-cdk` |
| `*.tf` or `terraform/` directory | `terraform` |
| `template.yaml`, `*.cfn.yaml`, or `cloudformation/` | `cloudformation` |

**Resolution rules:**
1. If contract **Provider / Tool** is set, it takes precedence.
2. If multiple tools detected and contract is silent, ask once.
3. If contract tool conflicts with workspace, stop and report mismatch.
4. If workspace is empty, ask once which tool to target.

## Block-to-artifact mapping

| Block | aws-cdk | terraform | cloudformation |
|-------|---------|-----------|----------------|
| `[Infrastructure]` | Stack/App construct class | root module (`main.tf`, backend config) | root template |
| `[Resource]` | Construct instantiation | `resource` block in HCL | `Resources` entry in YAML |

Respect each block's Parity **Implementation Scope**. Create missing directories.

## ADC-IMPLEMENTS markers

Format: `ADC-IMPLEMENTS: <ID>` — placed immediately before the resource, construct, or block implementing the design block.

| Format | Comment syntax |
|--------|----------------|
| CDK (Python) | `# ADC-IMPLEMENTS: <ID>` |
| CDK (TypeScript) | `// ADC-IMPLEMENTS: <ID>` |
| Terraform (HCL) | `# ADC-IMPLEMENTS: <ID>` |
| CloudFormation (YAML) | `# ADC-IMPLEMENTS: <ID>` |

## Default Parity paths (writer)

When prompt omits paths, use based on **Provider / Tool**:

| Tool | Implementation Scope | Configuration Scope | Tests |
|------|---------------------|---------------------|-------|
| `terraform` | `terraform/` | `terraform/env/dev.tfvars` | `tests/infra/test_terraform_validate.sh` |
| `aws-cdk` | `cdk/` | `cdk/cdk.json` | `tests/infra/test_cdk_synth.py` |
| `cloudformation` | `cloudformation/` | `cloudformation/parameters/dev.json` | `tests/infra/test_cfn_template.py` |
| (generic) | `infra/` | `infra/env/` | `tests/infra/` |

## Validation expectations (generator)

Parity **Tests** must include smoke-level validation — no full deploy in v1:

| Tool | Minimum test |
|------|-------------|
| `terraform` | `terraform validate` against generated config |
| `aws-cdk` | `cdk synth` asserting expected logical IDs exist |
| `cloudformation` | template structure validation (required `Resources`, valid YAML) |

## Contract layout

- **Same contract:** app + infra blocks in one `.qmd` for small/full-stack prompts.
- **Split contract:** infra-only or large stacks → `contracts/<module>-infra-adc-NNN.qmd`, linked via `[Reference: ...]` from app contract.

## ID conventions

- Infrastructure: `<module>-infra-NN>` (e.g. `<todo-infra-01>`)
- Resource: `<module>-res-<kind>-NN>` (e.g. `<todo-res-lambda-01>`)

Glob workspace `**/*.qmd` before minting; never reuse IDs.

## Error handling

| Situation | Behavior |
|-----------|----------|
| Infra blocks present, no IaC tool in workspace | Ask once which tool to target |
| Contract **Provider / Tool** conflicts with workspace | Stop; report mismatch |
| `[Resource]` missing **Parent** | Writer refuses; refiner flags |
| Vague prompt ("deploy to AWS") | Ask for resources, environment, tool |
| Multi-tool workspace | Prefer contract **Provider / Tool**; warn if ambiguous |
