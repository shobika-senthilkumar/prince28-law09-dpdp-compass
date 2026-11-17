
# DPDP Compass

AI-powered compliance guidance for India's Digital Personal Data Protection (DPDP) Act 2023 and DPDP Rules 2025.

## Problem

Indian startups need to understand which data-protection duties apply to them, what requirements they must satisfy, and when those duties become legally enforceable.

DPDP Compass helps founders and developers answer these questions using authoritative Indian legal sources.

## Target User

Founder-developers of small and growing Indian startups handling personal data, especially teams that need practical compliance guidance without having a dedicated legal team.

## Core Features

- Compliance guidance for the DPDP Act 2023
- Guidance based on the final DPDP Rules 2025
- Effective-date awareness for phased commencement
- Compliance Clock for checking whether a duty is currently in force
- Source-backed answers with Act sections and Rule references
- Distinction between final Rules and earlier draft Rules
- Guidance for notices, consent, children's data, and personal data breaches

## Key Challenge

The DPDP framework has different commencement dates for different provisions. DPDP Compass must distinguish between:

- What is legally required
- When the requirement comes into force
- Whether a provision is from the final Rules or only from the earlier draft
- Which authoritative source supports the answer

## Success Criteria

- 100% correct in-force status across the 40 duty-date evaluation tests
- 90%+ correct Act section / Rule citations across the 40 citation questions
- Answers grounded in authoritative sources
- Clear distinction between final and draft requirements

## Project Structure

```text
src/dpdpcompass/
├── api/
├── core/
├── domain/
└── services/

docs/
data/
tests/
