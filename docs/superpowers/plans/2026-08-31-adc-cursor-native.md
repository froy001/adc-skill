# ADC Cursor-native skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship one personal Cursor skill (`/adc`) so ADC write / generate / audit / refine works in any workspace without the Python CLI.

**Architecture:** Source of truth in `skills/adc/`; symlink to `~/.cursor/skills/adc`. `SKILL.md` routes to `references/*.md`. Schema symlinks to `adc-schema.qmd`.

**Tech Stack:** Cursor Agent Skills (Markdown), pytest for structure tests only.

## Global Constraints

- Personal skill: `~/.cursor/skills/adc` symlink to repo `skills/adc/`
- Native Cursor only; no CLI wrap
- `disable-model-invocation: true`; `name: adc`
- Default contracts dir: `contracts/`
- Do not modify `src/adc_cli/`

---

See spec: `docs/superpowers/specs/2026-08-31-adc-cursor-native-design.md`

**Status:** Implemented on `feature/adc-cursor-native`.
