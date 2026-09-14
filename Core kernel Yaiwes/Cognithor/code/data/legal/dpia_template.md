# Data Protection Impact Assessment (DPIA) — Cognithor

**Version:** 1.0
**Date:** 2026-03-28
**Assessor:** [Name]

## 1. Processing Description

| Field | Value |
|-------|-------|
| Processing Activity | [Name from register] |
| Purpose | [Purpose] |
| Legal Basis | [consent / legitimate_interest / contract] |
| Data Categories | [List] |
| Data Subjects | [Users / Investigated persons] |
| Recipients | [Cloud providers / Local only] |
| Retention | [Days] |

## 2. Necessity and Proportionality

- Is this processing necessary for the stated purpose? [Yes/No + justification]
- Could the purpose be achieved with less data? [Yes/No + justification]
- Is the retention period proportionate? [Yes/No + justification]

## 3. Risk Assessment

| Risk | Likelihood | Impact | Risk Level | Mitigation |
|------|-----------|--------|------------|------------|
| Unauthorized access to personal data | [Low/Med/High] | [Low/Med/High] | [L/M/H/C] | SQLCipher encryption, access control |
| Data breach via cloud LLM provider | [Low/Med/High] | [Low/Med/High] | [L/M/H/C] | Consent required, provider DPA |
| Excessive data collection | [Low/Med/High] | [Low/Med/High] | [L/M/H/C] | Privacy mode, data minimization |
| Failure to honor erasure request | [Low/Med/High] | [Low/Med/High] | [L/M/H/C] | Automated erasure across all tiers |
| Re-identification from pseudonymized data | [Low/Med/High] | [Low/Med/High] | [L/M/H/C] | Salt-based pseudonymization |

### Automated Risk Scoring

Risk score per activity (from processing_register.yaml):
- Involves PII: +1
- Sends data to cloud: +2
- Profiles/scores persons: +2
- Processes sensitive categories (Art. 9): +3
- Cross-border transfer: +2
- Retention > 180 days: +1

| Score | Level |
|-------|-------|
| 0-1 | LOW |
| 2-3 | MEDIUM |
| 4-6 | HIGH |
| 7+ | CRITICAL |

## 4. Measures Implemented

- [x] Consent management (per-channel, versioned)
- [x] ComplianceEngine (runtime enforcement, fail-closed)
- [x] Encryption at rest (SQLCipher with key management)
- [x] Right to erasure (erase_all across all tiers)
- [x] TTL enforcement (automated via cron)
- [x] Immutable audit log (SHA-256 chained)
- [x] GDPR-compliant privacy notices (DE + EN)
- [x] Cloud LLM consent flow
- [ ] Data minimization (Phase 3)
- [ ] Complete data export (Phase 3)

## 5. Conclusion

Overall risk level: [LOW / MEDIUM / HIGH / CRITICAL]
Recommendation: [Proceed / Proceed with conditions / Do not proceed]
Next review date: [Date]

---
*DPIA Template v1.0 | Cognithor Agent OS | Apache 2.0*
