# ADC IaC Generation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `skills/adc/` so `/adc` write, generate, audit, and refine modes support `[Infrastructure]` and `[Resource]` blocks with multi-tool IaC generation (CDK, Terraform, CloudFormation).

**Architecture:** Shared `references/iac.md` holds IaC semantics (stack detection, markers, mapping). Mode files get thin IaC sections linking to `iac.md`. Replace broken `schema.md` symlink with a standalone schema file that adds two new block types. Structure validated by pytest in `tests/test_adc_skill.py`.

**Tech Stack:** Cursor Agent Skills (Markdown), pytest (structure tests only).

## Global Constraints

- Scope is **`skills/` only** — no changes to Python CLI, `roles/`, or root `adc-schema.qmd`
- MUST follow ADC syntax (`skills/adc/references/schema.md`, README-adc.md conventions)
- MUST document the addition within `skills/`
- Existing `/adc` UX unchanged — no new command or sub-skill
- `disable-model-invocation: true`; skill `name: adc`
- Multi-tool IaC: detect CDK / Terraform / CloudFormation from workspace; contract **Provider / Tool** resolves conflicts
- Full loop: write, generate, audit, refine all extended

**Spec:** `docs/superpowers/specs/2026-09-02-adc-iac-generation-design.md`

**Branch:** `feature/adc-iac-generation`

---

## File map

| File | Action | Responsibility |
|------|--------|----------------|
| `skills/adc/references/schema.md` | Replace broken symlink | Canonical ADC schema + `[Infrastructure]` / `[Resource]` block types |
| `skills/adc/references/iac.md` | Create | Shared IaC rules: detection, mapping, markers, Parity defaults, validation |
| `skills/adc/SKILL.md` | Modify | Mention IaC in description/mode table; link `iac.md` |
| `skills/adc/references/writer.md` | Modify | Infra authoring: co-locate vs split, required fields, ID conventions |
| `skills/adc/references/generator.md` | Modify | IaC generation rules + link to `iac.md` |
| `skills/adc/references/auditor.md` | Modify | Infrastructure parity and drift sections |
| `skills/adc/references/refiner.md` | Modify | Infra completeness heuristics |
| `tests/test_adc_skill.py` | Modify | Assert IaC files, keywords, cross-links |

---

### Task 1: Fix schema baseline and add Infrastructure block types

**Files:**
- Replace: `skills/adc/references/schema.md` (currently broken symlink)
- Modify: `tests/test_adc_skill.py`

**Interfaces:**
- Produces: standalone `schema.md` containing all v1.0 block types plus `[Infrastructure]` and `[Resource]` definitions with Parity examples

- [ ] **Step 1: Write failing tests for schema IaC block types**

Add to `tests/test_adc_skill.py`:

```python
IAC_BLOCK_TYPES = ("Infrastructure", "Resource")
IAC_KEYWORDS = ("Provider / Tool", "Parent:", "ADC-IMPLEMENTS")


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
```

Add `"iac.md"` is NOT in REQUIRED_REFS yet — that comes in Task 2.

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_adc_skill.py::test_schema_is_standalone_file tests/test_adc_skill.py::test_schema_documents_iac_block_types -v`

Expected: FAIL — `schema.md` is a broken symlink; new tests not present yet until Step 1 applied, then fail on symlink/content.

- [ ] **Step 3: Replace symlink with standalone schema**

Remove broken symlink and write `skills/adc/references/schema.md`. Start from ADC Schema v1.0 content (same as `adc-schema.qmd` on `feature/adc-cursor-native`). Insert this new subsection under **## 3. ADC Block Types**, after **System & Requirement Types** and before **Visual & Reference Types**:

```markdown
### Infrastructure Types

* **`[Infrastructure: ...]`**: Defines a deployable infrastructure stack. Specifies **Provider / Tool** (`aws-cdk` | `terraform` | `cloudformation`), optional **Region / Environment**, and **Dependencies** on other blocks. Implementable — requires Parity and `ADC-IMPLEMENTS` marker in generated IaC.

  **Required sections:**
  - **Provider / Tool:** `aws-cdk` | `terraform` | `cloudformation`
  - **Region / Environment:** (optional)
  - **Dependencies:** (optional) references to other block IDs

  **Parity example:**
  ```markdown
  **Parity:**
  - **Implementation Scope:** `terraform/`
  - **Configuration Scope:** `terraform/env/dev.tfvars`
  - **Tests:** `tests/infra/test_terraform_validate.sh`
  ```

* **`[Resource: ...]`**: Defines an atomic cloud resource within an `[Infrastructure]` stack. Implementable — requires Parity and `ADC-IMPLEMENTS` marker.

  **Required sections:**
  - **Parent:** `<infrastructure-block-id>`
  - **Type:** provider resource type (e.g. `aws_lambda_function`, `AWS::Lambda::Function`)
  - **Properties:** key-value design intent
  - **Dependencies:** (optional) other `<resource-id>` tokens
  - **Outputs:** (optional) exported values

  **Parity:** file path or module within parent stack's **Implementation Scope**.

See [iac.md](iac.md) for stack detection, block-to-artifact mapping, and marker syntax per IaC tool.
```

Also update the Parity section bullet list to include `Infrastructure` and `Resource`:

```markdown
Every implementable Design Block (e.g., `Agent`, `DataModel`, `Feature`, `Infrastructure`, `Resource`) MUST contain a `Parity` section.
```

Remove or replace `test_schema_is_symlink_to_adc_schema` in `tests/test_adc_skill.py`:

```python
# DELETE test_schema_is_symlink_to_adc_schema entirely
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_adc_skill.py -v`

Expected: PASS (all tests including new schema tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adc/references/schema.md tests/test_adc_skill.py
git commit -m "feat(skill): add Infrastructure and Resource block types to schema"
```

---

### Task 2: Create shared IaC reference (`iac.md`)

**Files:**
- Create: `skills/adc/references/iac.md`
- Modify: `tests/test_adc_skill.py`

**Interfaces:**
- Consumes: block type definitions from `schema.md` (Task 1)
- Produces: `iac.md` — referenced by all mode files and `schema.md`

- [ ] **Step 1: Write failing test for iac.md**

Add to `tests/test_adc_skill.py`:

```python
IAC_TOOLS = ("aws-cdk", "terraform", "cloudformation")
IAC_DETECTION_SIGNALS = ("cdk.json", "*.tf", "template.yaml")


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
```

Update `REQUIRED_REFS` tuple:

```python
REQUIRED_REFS = (
    "schema.md",
    "iac.md",
    "writer.md",
    "generator.md",
    "auditor.md",
    "refiner.md",
)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_adc_skill.py::test_iac_reference_exists tests/test_adc_skill.py::test_reference_files_exist_and_nonempty -v`

Expected: FAIL — `iac.md` missing

- [ ] **Step 3: Create `skills/adc/references/iac.md`**

Write the complete file:

```markdown
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_adc_skill.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skills/adc/references/iac.md tests/test_adc_skill.py
git commit -m "feat(skill): add shared IaC reference for ADC skill"
```

---

### Task 3: Update SKILL.md router

**Files:**
- Modify: `skills/adc/SKILL.md`
- Modify: `tests/test_adc_skill.py`

**Interfaces:**
- Consumes: `iac.md` (Task 2)
- Produces: updated frontmatter description and mode table with IaC mentions

- [ ] **Step 1: Write failing test for IaC in SKILL.md**

Add to `tests/test_adc_skill.py`:

```python
IAC_TERMS = ("infrastructure", "iac.md", "Infrastructure", "Resource")


def test_skill_mentions_iac() -> None:
    text = SKILL_MD.read_text(encoding="utf-8").lower()
    assert "infrastructure" in text or "iac" in text
    assert "iac.md" in text
    body = SKILL_MD.read_text(encoding="utf-8")
    assert "[Infrastructure]" in body or "Infrastructure" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_adc_skill.py::test_skill_mentions_iac -v`

Expected: FAIL

- [ ] **Step 3: Update `skills/adc/SKILL.md`**

Replace frontmatter `description` line:

```yaml
description: Agent Design Contracts (ADC) write .qmd contracts from a prompt, generate application code and IaC (CDK/Terraform/CloudFormation), audit parity/drift, refine contracts. Use when the user invokes /adc or mentions ADC, contract_id, ADC-IMPLEMENTS, Infrastructure, Resource, or .qmd design blocks.
```

After the mode table, add:

```markdown
All modes support `[Infrastructure]` and `[Resource]` blocks for IaC. Read [iac.md](references/iac.md) when contracts contain infra blocks.

Always read [schema.md](references/schema.md) before acting. For IaC blocks, also read [iac.md](references/iac.md).
```

Remove duplicate "Always read schema.md" if it appears twice — keep one consolidated line as above.

Update **Defaults** section — add after source line:

```markdown
- IaC output: Parity **Implementation Scope** on `[Infrastructure]` / `[Resource]` blocks (see [iac.md](references/iac.md))
```

Add to **Error handling**:

```markdown
- Infra blocks with no IaC tool in workspace → ask once (see [iac.md](references/iac.md))
- Contract **Provider / Tool** conflicts with workspace → stop; report mismatch
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_adc_skill.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skills/adc/SKILL.md tests/test_adc_skill.py
git commit -m "feat(skill): extend ADC router for IaC generation"
```

---

### Task 4: Extend writer for Infrastructure blocks

**Files:**
- Modify: `skills/adc/references/writer.md`
- Modify: `tests/test_adc_skill.py`

**Interfaces:**
- Consumes: `schema.md`, `iac.md`
- Produces: writer rules for `[Infrastructure]` / `[Resource]` authoring

- [ ] **Step 1: Write failing test**

Add to `tests/test_adc_skill.py`:

```python
def test_writer_documents_iac_authoring() -> None:
    text = (REFS / "writer.md").read_text(encoding="utf-8")
    assert "Infrastructure" in text
    assert "Resource" in text
    assert "iac.md" in text
    assert "Parent" in text
    assert "Provider / Tool" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_adc_skill.py::test_writer_documents_iac_authoring -v`

Expected: FAIL

- [ ] **Step 3: Append to `skills/adc/references/writer.md`**

Add section after **ID minting**:

```markdown
## Infrastructure blocks

Read [iac.md](iac.md) for shared IaC rules.

### When to write infra blocks

- Prompt mentions deploy, cloud, stack, Lambda, VPC, S3, etc. → include `[Infrastructure]` + `[Resource]` blocks.
- Small/full-stack prompt → same `.qmd` as app blocks.
- Infra-only or large stack → new file `contracts/<module>-infra-adc-NNN.qmd`; link app contract via `[Reference: ...]` when both exist.

### Required fields

**`[Infrastructure]`:**
- **Provider / Tool:** `aws-cdk` | `terraform` | `cloudformation` (required)
- **Region / Environment:** when known
- **Parity:** Implementation Scope, Configuration Scope, Tests (required)

**`[Resource]`:**
- **Parent:** `<infrastructure-block-id>` (required — writer MUST refuse if missing)
- **Type:** provider resource type (required)
- **Properties:** design intent key-values (required)
- **Dependencies:** when resource depends on another resource
- **Outputs:** when app blocks or other resources consume values
- **Parity:** path within parent stack scope

### Implementable blocks list

Add `Infrastructure` and `Resource` to implementable blocks requiring Parity:

`Agent`, `DataModel`, `Feature`, `Tool`, `Algorithm`, `APIEndpoint`, `TestScenario`, `Infrastructure`, `Resource`

### Infra ID prefixes

- Infrastructure: `<module>-infra-NN>`
- Resource: `<module>-res-<kind>-NN>`

If prompt lacks resource types, environment, or tool → ask specific questions; do not write TBD skeletons.
```

Also update the existing Parity bullet in **Body** section to include `Infrastructure`, `Resource`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_adc_skill.py::test_writer_documents_iac_authoring -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skills/adc/references/writer.md tests/test_adc_skill.py
git commit -m "feat(skill): extend ADC writer for Infrastructure blocks"
```

---

### Task 5: Extend generator for IaC output

**Files:**
- Modify: `skills/adc/references/generator.md`
- Modify: `tests/test_adc_skill.py`

**Interfaces:**
- Consumes: `iac.md`, infra blocks from contracts
- Produces: generator rules mapping blocks to CDK/Terraform/CloudFormation artifacts

- [ ] **Step 1: Write failing test**

Add to `tests/test_adc_skill.py`:

```python
def test_generator_documents_iac_generation() -> None:
    text = (REFS / "generator.md").read_text(encoding="utf-8")
    assert "Infrastructure" in text
    assert "Resource" in text
    assert "iac.md" in text
    assert "ADC-IMPLEMENTS" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_adc_skill.py::test_generator_documents_iac_generation -v`

Expected: FAIL

- [ ] **Step 3: Append to `skills/adc/references/generator.md`**

After rule 3 **Contract-to-code**, add IaC mappings:

```markdown
   - `[Infrastructure]` → stack entry point (CDK App/Stack class, Terraform root module, CloudFormation template)
   - `[Resource]` → resource definition (construct, `resource` block, `Resources` entry)
```

Add new section after rule 6:

```markdown
## Infrastructure generation

Read [iac.md](iac.md) before generating any `[Infrastructure]` or `[Resource]` blocks.

1. **Tool resolution:** Detect or validate **Provider / Tool** per `iac.md` stack detection rules.
2. **Reference following:** Load infra blocks from all referenced contracts (`[Reference]` links).
3. **File placement:** Write under each block's Parity **Implementation Scope**; respect **Parent** hierarchy for `[Resource]` blocks.
4. **Markers:** Add `ADC-IMPLEMENTS: <ID>` using comment syntax from `iac.md` immediately before each stack/resource implementation.
5. **Dependencies:** Wire `[Resource]` **Dependencies** in correct order (IAM roles before Lambda, etc.).
6. **Outputs:** Export `[Resource]` **Outputs** as stack outputs / module outputs / CFN Outputs as appropriate for the tool.
7. **Tests:** Create or update Parity **Tests** with smoke validation (`terraform validate`, `cdk synth`, or template lint) per `iac.md`.
8. **Mixed contracts:** App blocks (`DataModel`, `APIEndpoint`, etc.) still generate application code as today — infra and app in same run when both exist.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_adc_skill.py::test_generator_documents_iac_generation -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skills/adc/references/generator.md tests/test_adc_skill.py
git commit -m "feat(skill): extend ADC generator for IaC output"
```

---

### Task 6: Extend auditor for Infrastructure parity

**Files:**
- Modify: `skills/adc/references/auditor.md`
- Modify: `tests/test_adc_skill.py`

**Interfaces:**
- Consumes: `iac.md`, IaC files under Parity scopes
- Produces: audit report sections for infra parity and drift

- [ ] **Step 1: Write failing test**

Add to `tests/test_adc_skill.py`:

```python
def test_auditor_documents_iac_checks() -> None:
    text = (REFS / "auditor.md").read_text(encoding="utf-8")
    assert "Infrastructure" in text
    assert "iac.md" in text
    assert "Infrastructure Parity" in text or "Infrastructure Drift" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_adc_skill.py::test_auditor_documents_iac_checks -v`

Expected: FAIL

- [ ] **Step 3: Update `skills/adc/references/auditor.md`**

Add after line 3 (schema reference):

```markdown
For `[Infrastructure]` / `[Resource]` blocks, also read [iac.md](iac.md). Load IaC source from Parity **Implementation Scope** paths on infra blocks (not only `src/`).
```

Insert new reporting sections after **`## 2. Design Drift Report`** (renumber existing section 3 to section 4):

```markdown
2.  **`## 2. Design Drift Report`**
    * (existing content unchanged)
    * **Infrastructure Drift:** For each `[Infrastructure]` / `[Resource]` block with a matching marker, compare **Type**, **Properties**, **Dependencies**, and **Outputs** against the generated IaC. Report file path, line number, and discrepancy.

3.  **`## 3. Infrastructure Parity Check`**
    * Read [iac.md](iac.md) for marker syntax per tool.
    * Scan IaC files (Terraform, CDK, CloudFormation) for `ADC-IMPLEMENTS` markers.
    * Verify every `[Infrastructure]` and `[Resource]` block has at least one matching marker.
    * Report dangling markers and unimplemented infra blocks.
    * Verify Parity **Tests** exist and match smoke validation expectations from `iac.md`.

4.  **`## 4. Architectural & Technical Roadblock Analysis`**
    * (existing section 3 content — add IaC-specific checks)
    * **IaC Security:** open security groups, missing encryption at rest, overly permissive IAM policies, secrets in plain text.
    * **IaC Maintainability:** hardcoded ARNs, missing parameterization, resources not tagged.
```

Update OUTPUT section to list four report sections in order.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_adc_skill.py::test_auditor_documents_iac_checks -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skills/adc/references/auditor.md tests/test_adc_skill.py
git commit -m "feat(skill): extend ADC auditor for Infrastructure parity"
```

---

### Task 7: Extend refiner for Infrastructure completeness

**Files:**
- Modify: `skills/adc/references/refiner.md`
- Modify: `tests/test_adc_skill.py`

**Interfaces:**
- Consumes: `schema.md`, `iac.md`
- Produces: refiner heuristics for infra contract quality

- [ ] **Step 1: Write failing test**

Add to `tests/test_adc_skill.py`:

```python
def test_refiner_documents_iac_heuristics() -> None:
    text = (REFS / "refiner.md").read_text(encoding="utf-8")
    assert "Infrastructure" in text
    assert "iac.md" in text
    assert "Parent" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_adc_skill.py::test_refiner_documents_iac_heuristics -v`

Expected: FAIL

- [ ] **Step 3: Append to `skills/adc/references/refiner.md`**

After line 3, add:

```markdown
For contracts with `[Infrastructure]` / `[Resource]` blocks, read [iac.md](iac.md).
```

Add new section **6. Infrastructure Completeness** before the closing paragraph:

```markdown
6. **Infrastructure Completeness:**
   * **Missing Parent:** Every `[Resource]` MUST have **Parent** pointing to an existing `[Infrastructure]` block.
   * **Orphan resources:** Parent ID must exist in the same or referenced contract.
   * **Missing Provider / Tool:** `[Infrastructure]` blocks must specify `aws-cdk`, `terraform`, or `cloudformation`.
   * **Provider mismatch:** Flag when **Provider / Tool** likely conflicts with workspace layout (see `iac.md` detection signals).
   * **Missing Dependencies:** Flag resources that logically depend on others (e.g. Lambda without IAM role) but omit **Dependencies**.
   * **Missing Outputs:** Flag resources referenced by app blocks (via **Dependencies** or prose) that lack **Outputs**.
   * **Missing Parity Tests:** Infra blocks without **Tests** in Parity section.
   * **Vague Properties:** Properties with TBD values or missing required provider fields.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_adc_skill.py::test_refiner_documents_iac_heuristics -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skills/adc/references/refiner.md tests/test_adc_skill.py
git commit -m "feat(skill): extend ADC refiner for Infrastructure completeness"
```

---

### Task 8: Cross-link verification and final smoke test

**Files:**
- Modify: `tests/test_adc_skill.py` (final integration test)

**Interfaces:**
- Consumes: all files from Tasks 1–7
- Produces: passing full test suite confirming spec success criteria

- [ ] **Step 1: Write cross-link integration test**

Add to `tests/test_adc_skill.py`:

```python
def test_all_mode_refs_link_to_iac() -> None:
    for name in ("writer.md", "generator.md", "auditor.md", "refiner.md"):
        text = (REFS / name).read_text(encoding="utf-8")
        assert "iac.md" in text, f"{name} must link to iac.md"


def test_schema_links_to_iac() -> None:
    text = (REFS / "schema.md").read_text(encoding="utf-8")
    assert "iac.md" in text
```

- [ ] **Step 2: Run full test suite**

Run: `pytest tests/test_adc_skill.py -v`

Expected: PASS — all tests green

- [ ] **Step 3: Manual smoke checklist**

Verify spec success criteria (read-only checks):

```bash
rg -l "Infrastructure|iac\.md" skills/adc/
rg "\[Infrastructure:" skills/adc/references/schema.md
rg "Provider / Tool" skills/adc/references/iac.md
```

Expected: all seven skill files mention IaC; schema has block type; iac.md has Provider / Tool.

- [ ] **Step 4: Commit**

```bash
git add tests/test_adc_skill.py
git commit -m "test(skill): add IaC cross-link verification for ADC skill"
```

---

## Spec coverage checklist

| Spec requirement | Task |
|------------------|------|
| `[Infrastructure]` block type | Task 1 |
| `[Resource]` block type | Task 1 |
| Shared `iac.md` reference | Task 2 |
| Multi-tool stack detection | Task 2 |
| `ADC-IMPLEMENTS` marker syntax per tool | Task 2 |
| SKILL.md updated | Task 3 |
| Writer: co-locate vs split, required fields | Task 4 |
| Generator: IaC artifact emission | Task 5 |
| Auditor: infra parity + drift | Task 6 |
| Refiner: infra completeness heuristics | Task 7 |
| Full loop (write/generate/audit/refine) | Tasks 4–7 |
| Documented within `skills/` | Tasks 1–7 |
| Structure tests | Tasks 1–8 |
| skills/ only scope | All tasks (no CLI/roles/adc-schema.qmd) |

## Out of scope (do not implement)

- Python CLI changes
- `roles/` prompt updates
- Root `adc-schema.qmd` sync
- Pulumi, Crossplane, Bicep
- Full deploy integration tests
- MCP / AWS API integration
