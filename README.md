# DPDP Compass

[![CI](https://github.com/shobika-senthilkumar/prince28-law09-dpdp-compass/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/shobika-senthilkumar/prince28-law09-dpdp-compass/actions/workflows/ci.yml)
[![Live](https://img.shields.io/website?url=https%3A%2F%2Fdpdp-compass.onrender.com%2Fhealth)](https://dpdp-compass.onrender.com/health)
[![Uptime (30 days)](https://img.shields.io/uptimerobot/ratio/m804789194-29ed3f823b7fe021fdc8b9d8?label=Uptime%20(30%20days))](https://dashboard.uptimerobot.com/)

**Status:** Week 1 complete · live at https://dpdp-compass.onrender.com

**Live:** https://dpdp-compass.onrender.com · [API docs](https://dpdp-compass.onrender.com/docs)


Practical compliance guidance for Indian startups navigating the Digital Personal Data Protection Act 2023 and the DPDP Rules 2025.

## Who It Is For

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
