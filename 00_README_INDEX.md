# 00 — README & INDEX: Open, AI-Native Alternative to the Yamicc Platform

Prepared: 21 November 2026. Merged from three research sets:
- (A) Claude research prompt (web-verified facts on Yamicc, landscape, requirements)
- (B) "Master Research & Product Specification Prompt" (roles, FR-001..058, UX, MVP A/B/C, deliverables)
- (C) "Context & Objective" prompt (Mendix/digital-thread framing, open-source stack, 3-phase roadmap)
Plus an extra verification pass (Yamicc partner ecosystem, March 2026 demo).

## How to load this into Paperclip

| File | Use in Paperclip |
|---|---|
| 01_COMPANY_MISSION_AND_GOALS.md | Company mission + top-level goal tree. Paste mission into the company; create goals as listed. |
| 02_YAMICC_INTEL.md | Shared context / knowledge file for ALL agents. Source of truth for what is known about Yamicc. |
| 03_LANDSCAPE.md | Shared context for Research, Architecture and Strategy agents. |
| 04_REQUIREMENTS_SPEC.md | Project spec for Product, Architecture, UX agents. Canonical requirement IDs. |
| 05_UX_UI_SPEC.md | Project spec for the UX agent. |
| 06_ARCHITECTURE_STANDARDS_AI.md | Project spec for Architecture, Interoperability and AI agents. |
| 07_REGULATORY_SECURITY.md | Project spec for the Regulatory/Privacy/Security agent. |
| 08_STRATEGY_MVP_ROADMAP.md | Project spec for the Strategy/PM agent; contains final deliverable structure. |
| 09_AGENT_ORG_AND_TASKS.md | Org chart, agent role prompts, task backlog with dependencies, approval gates. |

## Labels used in every file
- **[VERIFIED]** — confirmed against a public source (URL given).
- **[CLAIMED-B] / [CLAIMED-C]** — stated in input B or C, not yet independently verified.
- **[GK]** — general domain knowledge; verify current status before relying on it.
- **[INFERRED]** — reasoning, not fact.
- **[CONFLICT]** — sources disagree; see conflict table in 02.

## Global rules for all agents
1. Public sources only. Do not contact Yamicc staff, partners or hospitals without human approval.
2. Never use or request real patient data. Synthetic data only (e.g. Synthea, MIMIC-style demo sets with proper licensing).
3. Do not collect personal contact details of individuals (phone numbers, private emails) even if found on data-broker sites.
4. Keep the evidence labels above on every claim; add source URL and access date.
5. Do not overstate maturity of any product (announced ≠ demo ≠ pilot ≠ production ≠ validated).
6. FHIR, OMOP and CDISC are different things with different purposes; never treat them as interchangeable.
7. Prefer integrating mature components over rebuilding them.
