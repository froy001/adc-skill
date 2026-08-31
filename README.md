# Agentic Design Contracts (ADC)

This repository contains the core implementation of the Agentic Design Contracts (ADC) methodology, a framework for designing and building AI-driven systems with the help of specialized AI agents.

## What is an Agentic Design Contract?

An **Agentic Design Contract (ADC)** is a machine-readable design document that serves as the single source of truth for an AI system's architecture. Written in a specific Markdown format, it allows specialized AI agents to automate key parts of the development lifecycle, including code generation, auditing, and design refinement.

The core idea is to close the gap between design and implementation. By defining the system in a structured, agent-friendly format, we can ensure that the code accurately reflects the design and detect "drift" as the system evolves.

## Quick start: provide ADC context to your coding agent:

> @code_generator create an ADC contract using @adc-schema.qmd for my new project. Here's the high-level idea...

> @code_generator generate the code based on @my-new-project-adc-001.qmd

> @auditor audit the code in this package based on my-new-project-adc-001.qmd

## How It Works: the ADC Framework

The ADC framework consists of three main components that work together:

### 1. The ADC Schema (`adc-schema.qmd`)

This is the foundation of the system. The schema defines a formal structure for the design contracts, specifying a series of typed "design blocks" that describe each component of the system.

**Key Block Types:**
- `[Agent: ...]`: Defines an autonomous agent's persona and thinking process.
- `[DataModel: ...]`: Defines a data structure, typically translated to a Pydantic model.
- `[Algorithm: ...]`: Describes a specific piece of logic or a business rule.
- `[TestScenario: ...]`: Describes a key scenario that must be covered by tests.
- And many more...

Each block has a unique, stable ID that is used to link the design directly to the code that implements it.

### 2. The Specialized AI Agents (`roles/`)

The "agentic" part of the methodology comes from 1) the schema for building systems with agents & tools and 2) a team of specialized AI agents, each with a distinct role and persona. These agents read the ADC files and perform specific tasks:

- **The Code Generator (`roles/code_generator.md`):** A Senior Staff Software Engineer persona that reads the contracts and generates high-quality, fully type-hinted Python code that implements the specified design. It places special `ADC-IMPLEMENTS: <ID>` markers in the code to create a traceable link back to the design contract.

- **The Auditor (`roles/auditor.md`):** A Principal Engineer and Systems Architect persona that inspects both the design contracts and the codebase. It performs a comprehensive audit to check for parity, detect design drift, and identify potential architectural roadblocks, performance issues, or security concerns.

- **The Refiner (`roles/refiner.md`):** A Senior Technical Product Manager persona that analyzes the design contracts themselves. It identifies gaps, inconsistencies, or ambiguities in the design and suggests specific improvements to make the contracts more clear, complete, and implementable.

### 3. The `adc` Command-Line Tool

This is the orchestrator of the ADC lifecycle. The `adc` tool is a command-line interface that allows a human developer to invoke the AI agents.

- **`adc generate`**: Deploys the Code Generator agent to scaffold a new project or add features based on contracts.
- **`adc audit`**: Deploys the Auditor agent to analyze a codebase for compliance with its contracts.
- **`adc refine`**: Deploys the Refiner agent to improve the quality of the contracts themselves.

For detailed usage instructions for the CLI tool, please see **[README-adc.md](README-adc.md)**.

## Cursor skill (any workspace)

Install once on this machine:

```bash
ln -sf "$(pwd)/skills/adc" ~/.cursor/skills/adc
```

Then in any project, invoke `/adc`:

- **Write:** `/adc Design a small REST API for todos with User and Task models`
- **Generate:** `/adc generate code from contracts/`
- **Audit:** `/adc audit src/ against contracts/`
- **Refine:** `/adc refine contracts/my-app-adc-001.qmd`

No Python CLI or API keys required in Cursor — the agent uses this skill plus workspace files.

## Getting Started

1.  **Understand the Schema:** Read through `adc-schema.qmd` to understand the different design blocks available.
2.  **Review the Agent Roles:** Look at the system prompts in the `roles/` directory to see the exact instructions and capabilities of each AI agent.
3.  **Install & Use the Tool:** Follow the instructions in `README-adc.md` to install the `adc` tool and start using it in your projects. 