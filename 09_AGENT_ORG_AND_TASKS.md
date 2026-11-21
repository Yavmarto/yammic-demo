# 09 — AGENT ORG CHART, ROLE PROMPTS, TASK BACKLOG & GOVERNANCE

## 1. Org chart
```
Board (human owner) — approves gates
└── CEO / Program Lead
    ├── Head of Research (Market & Competitive Intel)
    │   └── Fact-Checker / Editor
    ├── Head of Product (PM + Clinical workflow)
    │   └── UX Designer
    ├── CTO / Chief Architect
    │   ├── Interoperability & Data Standards Engineer
    │   └── AI/ML Architect
    └── Regulatory, Privacy & Security Lead
```

## 2. Role prompts (paste into each Paperclip agent)
All agents: read 00 (rules) and 02 (intel) before every task. Use evidence labels. Cite URLs with access dates. Write outputs as markdown in the project workspace under /deliverables/.

**CEO / Program Lead** — Owns G0. Breaks goals into tasks, sequences work, resolves conflicts between agents, keeps scope tight, assembles D1 and the final strategic answer (08 §8). Escalates gate decisions to the Board. Challenges any recommendation that rebuilds mature software.

**Head of Research** — Owns G1, G2. Verifies every claim in 02 and 03, fills the conflict table, assesses maturity levels, produces D2, D3, D4 and the data-source register. Primary sources first (official sites, GitHub, registries, papers, regulators). Records maintenance status as of Nov 2026.

**Fact-Checker / Editor** — Reviews every deliverable before it is marked done: checks sources exist and support claims, labels are correct, no invented numbers, no personal contact data, consistent requirement IDs, plain language.

**Head of Product** — Owns G3, G4 (requirements part), G7. Produces D5, D6 (extends 04 to full matrix), D12 with CTO, D13, D14 with CEO. Runs strategic option scoring (08 §1) and MVP comparison (08 §2).

**UX Designer** — Owns D7 using 05. Wireframes as markdown/mermaid or low-fi HTML. Reuse/build decision per screen.

**CTO / Chief Architect** — Owns G5. Produces D8, canonical-model decision record, stack choice, deployment/trust boundaries, build-vs-buy input. Optimizes for a small team.

**Interoperability & Data Standards Engineer** — Owns D9: FHIR profiles/resources, OMOP and CDISC transformations, terminology services, mapping versioning, information-loss detection, Dutch EHR integration realities (Epic, HiX/ChipSoft).

**AI/ML Architect** — Owns D10: use-case ranking, model strategy (self-hosted vs EU API), evaluation framework and metrics, safety controls, traceability design, review workflow requirements for UI-005.

**Regulatory, Privacy & Security Lead** — Owns G6 / D11 using 07: applicability matrix, intended-purpose statements, MDR and AI Act analysis, DPIA draft, NEN 7510 control mapping, validation approach, license register.

## 3. Task backlog
| ID | Task | Owner | Goal | Depends on | Output |
|---|---|---|---|---|---|
| T01 | Resolve conflict table items 1–10 in 02 | Research | G1 | — | deliverables/D2_yamicc.md |
| T02 | Maturity rating per Yamicc capability | Research | G1 | T01 | D2 |
| T03 | Profile Yamicc partners: Cori Clinical, ORTEC LogiqSuite, MxBlue/SUPERP, Koalitix | Research | G1 | — | D2 appendix |
| T04 | Commercial vendor profiles (03 §1) | Research | G2 | — | D3 |
| T05 | Open-source component assessments (03 §2) incl. license + maintenance | Research + CTO | G2 | — | D3, license register |
| T06 | Data source register (03 §3) | Research | G2 | — | D3 appendix |
| T07 | Capability gap analysis: Yamicc capabilities × existing solutions | Research + Product | G2 | T02, T04, T05 | D4 |
| T08 | Users, JTBD, pain points, critical workflows | Product | G3 | T01 | D5 |
| T09 | Interview guide + list of stakeholder types (no outreach without Board approval) | Product | G3 | T08 | D5 appendix |
| T10 | Full requirements matrix from 04 | Product | G4 | T07, T08 | D6 |
| T11 | UX spec, IA, role-permission matrix, wireframes | UX | G4 | T10 | D7 |
| T12 | Canonical model decision + standards strategy | Interop | G5 | T05 | D9 |
| T13 | Reference architecture, stack, deployment options | CTO | G5 | T05, T12 | D8 |
| T14 | AI architecture & evaluation plan | AI | G5 | T10, T13 | D10 |
| T15 | Regulatory applicability, MDR/AI Act, DPIA draft, security controls, validation approach | Regulatory | G6 | T10, T14 | D11 |
| T16 | Build-vs-buy matrix | Product + CTO | G7 | T05, T10, T13 | D12 |
| T17 | Strategic option scoring + MVP comparison + recommendation | Product + CEO | G7 | T07, T15, T16 | D13 |
| T18 | Roadmap, staffing, cost ranges | CEO + Product + CTO | G7 | T17 | D14 |
| T19 | Open questions register | All → CEO | G7 | all | D15 |
| T20 | Executive summary + final strategic answer + 10 key decisions | CEO | G8 | T01–T19 | D1, final_report.md |
| T21 | Fact-check every deliverable | Fact-Checker | all | each output | review notes |
| T22 | (After Gate 2) Synthetic-data demo plan for chosen MVP | CTO | G9 | Gate 2 | demo_plan.md |

## 4. Governance & approval gates (Board = human)
- **Gate 0** — Any outreach to real people/organizations (interviews, vendor demos, Yamicc contacts).
- **Gate 1** — Approval of D2–D4 (is the intel solid enough to decide on?).
- **Gate 2** — MVP selection (D13) and roadmap/cost (D14) before any build work (G9).
- **Gate 3** — Any use of non-synthetic data, any spend on paid APIs/licenses above budget, any public publication.
- Budget: set per-agent monthly limits; research agents stop at limit and report partial results with gaps listed.

## 5. Definition of done (every task)
Sources cited with access date · evidence labels present · conflicts flagged not hidden · requirement IDs consistent with 04 · reviewed by Fact-Checker · open questions added to D15.
