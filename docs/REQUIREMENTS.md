# DPDP Compass — Requirements

## Functional Requirements

### FR1 — Compliance Questions
The system shall answer user questions about the DPDP Act 2023 and the final DPDP Rules 2025 using authoritative sources.

### FR2 — Effective-Date Checking
The system shall determine whether a specific DPDP duty is in force on a given date and provide its applicable commencement date.

### FR3 — Source Citations
The system shall provide the relevant Act section, Rule, or authoritative source supporting each compliance answer.

### FR4 — Final vs Draft Rules
The system shall distinguish requirements from the final DPDP Rules 2025 from requirements that appeared only in the earlier draft Rules.

### FR5 — Compliance Clock
The system shall allow a user to select a compliance duty and date and return whether the duty is currently in force, when it becomes effective, and the relevant legal provision.

## Non-Functional Requirements

### NFR1 — Accuracy
The system shall achieve 100% correct in-force status across the 40 duty-date evaluation tests.

### NFR2 — Citation Accuracy
The system shall achieve at least 90% correct Act section or Rule citations across the 40 citation questions.

### NFR3 — Response Clarity
The system shall clearly distinguish between requirements that are currently applicable and requirements that have not yet commenced.

### NFR4 — Source Reliability
The system shall prioritize authoritative sources such as MeitY, India Code, PIB, and official commencement notifications.

### NFR5 — Maintainability
The system shall keep compliance knowledge and application logic organized so that legal updates and commencement changes can be incorporated without rewriting the entire application.