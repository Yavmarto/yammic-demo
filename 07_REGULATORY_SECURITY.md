# 07 — REGULATORY, PRIVACY, SECURITY & VALIDATION

A production deployment requires formal legal, security and regulatory assessment by qualified humans. Agents produce analysis and draft artefacts, not legal sign-off.

## 1. Privacy (GDPR / UAVG)
Analyse: legal bases; Article 9 conditions for health and genetic data; controller vs processor roles (hospital, platform operator, sponsor); joint controllership in multicenter studies; DPIA template; data minimization; pseudonymization (pseudonymized ≠ anonymous); consent vs other research bases (and WMO consent); international transfers (avoid; EU hosting); retention; data subject rights; ethics approvals (METC/CCMO).

## 2. Clinical research regulation
| Framework | Applies when | Platform impact |
|---|---|---|
| EU CTR 536/2014 + CTIS | Interventional drug trials in EU | Data integrity, submissions, transparency |
| ICH E6(R3) GCP | Clinical trials | Risk-based quality, computerized system expectations, audit trails |
| EU GMP Annex 11 / EMA guideline on computerised systems & electronic data in clinical trials | Systems handling trial data | Validation, audit trail, e-signatures |
| 21 CFR Part 11 | US FDA-regulated data | Only if US sponsors |
| Dutch WMO, CCMO/METC | Research with human subjects in NL | Approvals, consent |
| HIPAA | US PHI only | Not default [CONFLICT with C, which listed it as baseline] |

## 3. AI and medical device regulation
- Define intended purpose per AI feature first.
- EU MDR / IVDR: software that informs treatment decisions for individual patients (matching, drug recommendation, diagnostics) may qualify as a medical device (MDCG 2019-11 guidance, Rule 11). Data capture/admin automation for research generally does not.
- EU AI Act: high-risk mainly via MDR-regulated products (Annex I) or Annex III uses; transparency and AI-literacy obligations otherwise. Do not assume all clinical-research AI is high-risk, and do not assume human review removes obligations. [CONFLICT with C, which framed the platform as high-risk clinical decision support by default.]
- Recommendation [INFERRED]: keep MVP features outside MDR scope (research data capture, mapping, quality); treat matching/recommendation as a later, deliberately certified module or explicitly research-only with no individual treatment use.

## 4. Security requirements
Encryption in transit/at rest · Keycloak-based IAM with MFA · least privilege, RBAC + ABAC · tenant/institution isolation · secrets management · secure SDLC · SAST/DAST, dependency and container scanning, SBOM · backup and disaster recovery with tested restores · incident response plan · security monitoring · annual penetration testing · tamper-evident audit logs · NEN 7510/7512/7513 and ISO 27001 alignment · EU-only hosting.

## 5. Validation (computerized system validation)
User requirements spec · functional spec · risk assessment (GAMP 5 categories) · test plans · requirements traceability matrix · IQ/OQ/PQ where appropriate · release controls · change management · validation evidence packages · SOPs · training records. Build traceability (requirement ID → test → evidence) into the repo and CI from day one.

## 6. Open-source licensing risks
Check every dependency: copyleft (GPL/AGPL) obligations for distributed or hosted software; source-available licenses (e.g. some Camunda/Elastic versions); REDCap license terms; OncoKB commercial licensing; SNOMED CT national licensing (NL is a member country); questionnaire copyrights (EORTC QLQ). Produce a license register.

## 7. Deliverables
Regulatory applicability matrix · intended-purpose statements per feature · MDR classification analysis · AI Act analysis · DPIA draft · security control set mapped to NEN 7510 · validation approach · license register · top regulatory risks with mitigations.
