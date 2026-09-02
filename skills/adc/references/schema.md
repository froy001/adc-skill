# Agent Design Contract (ADC) Schema v1.0

## 1. Overview

An Agent Design Contract (ADC) is a machine-readable design document, written in Markdown, that specifies the architecture and intent of an AI-driven system. An ADC contract serves as the single source of truth for development, enabling automated code generation, auditing, and drift detection by specialized agents used for development.

The rationale for ADC is to:
1. Define a lightweight specification for designs for agentic systems that's easily read and implemented by humans and AI agents.
2. Support agent-based development using any agent, tool, or IDE.
3. Critically, create a single source of truth that supports cross-team collaboration and communication.

An ADC file consists of two parts:
1.  **YAML Front Matter:** Contains structured metadata about the contract.
2.  **Design Blocks:** A series of typed, addressable sections that describe each component of the system.

---

## 2. File Structure

### YAML Front Matter

Every ADC file MUST begin with a YAML front matter block.

```yaml
---
contract_id: module_name-unique-identifier-adc-001
title: "Human-Readable Title of the Contract"
author: "Author Name"
status: "proposed" # proposed | active | deprecated | superseded
version: 1.2
created_date: "YYYY-MM-DD"
last_updated: "YYYY-MM-DD"
---
```

### Design Blocks

The body of the contract is composed of "Design Blocks." Each block represents an atomic component of the design and follows a strict format:

**Format:** `### [Type: Name] <ID>`

* **`[Type]`**: The official ADC block type (e.g., `[Agent]`, `[DataModel]`).
* **`Name`**: A human-readable name for the block.
* **`<ID>`**: A stable, globally unique identifier (e.g., `<adc-pipe-agent-01>`). This ID is critical for linking and auditing.

---

## 3. ADC Block Types

The following are the official block types supported by the ADC schema.

### High-Level & Scoping Types

* **`[Rationale: ...]`**: Explains the "why" behind the contract or a major design decision. It provides context for human readers and AI agents.
* **`[Implementation: ...]`**: Provides high-level guidance, notes, or constraints for how the entire contract should be implemented, often specifying libraries or architectural patterns.

### Agentic & Logic Types

* **`[Agent: ...]`**: The core agentic component. Defines an autonomous agent with a specific `Persona` and a `Thinking Process` (algorithm) that dictates its behavior.
* **`[Algorithm: ...]`**: Describes a specific, self-contained piece of logic, a calculation, or a business rule, often using mathematical notation (LaTeX) or structured pseudocode.
* **`[prompt<Name>: ...]`**: Defines a typed, reusable prompt for an LLM. The `<Name>` allows it to be referenced directly from code. The body specifies the prompt's inputs, template, and expected output format.

### Data & Structure Types

* **`[DataModel: ...]`**: Defines a data structure, schema, or class. Supports inheritance notation (e.g., `[DataModel: MyModel(BaseModel)]`) to show relationships. This block is typically translated into a Pydantic model.
* **`[DataTransform: ...]`**: Describes a function or process that converts data from one `DataModel` to another. Specifies inputs, outputs, and the transformation logic.

### System & Requirement Types

* **`[Tool: ...]`**: Describes a tool or service that is used by an agent and provides an interface to the agent.
* **`[Feature: ...]`**: Describes a user-facing capability or a significant system feature, including its configuration and benefits.
* **`[Constraint: ...]`**: Defines a non-functional requirement, boundary condition, or performance gate (e.g., "Response time must be <100ms").
* **`[APIEndpoint: ...]`**: The contract for a service API endpoint, defining the path, method, request/response objects, and error codes.
* **`[TestScenario: ...]`**: Describes a key user story, edge case, or scenario that must be covered by tests.

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

### Visual & Reference Types

* **`[Diagram: ...]`**: A visual representation of the system architecture or a process flow. MUST use Mermaid.js syntax. Nodes in the diagram should use ADC IDs to be verifiable.
* **`[Reference: ...]`**: A pointer to definitions located in another ADC file, used to link contracts together without duplicating content.

---

## 4. Core Sections within Blocks

### The `Parity` Section

Every implementable Design Block (e.g., `Agent`, `DataModel`, `Feature`, `Infrastructure`, `Resource`) MUST contain a `Parity` section. This creates the explicit, traceable link between design, code, and documentation.

```markdown
**Parity:**
- **Implementation Scope:** `src/pipelines/orchestrator/`
- **Configuration Scope:** `configs/pipelines/`
- **Tests:**
  - `tests/test_pipeline_orchestrator.py`
  - `tests/test_pipeline_e2e.py`
```

### The `ADC-IMPLEMENTS` Marker

To complete the loop from design to code, the `code_generator` agent MUST add a marker in the source code immediately before the class or function that implements a design block. The `auditor` agent uses this marker to verify compliance.

**Format:** `ADC-IMPLEMENTS: <ID>`

**Example (in Python):**

```python
# ADC-IMPLEMENTS: <adc-pipe-agent-01>
class TuningPipelineOrchestrator:
    def run(self):
        # ... implementation of the agent's thinking process
```
