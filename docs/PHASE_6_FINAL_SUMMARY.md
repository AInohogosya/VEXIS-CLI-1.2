# Phase 6 Summary: Final Summarization

## Purpose
Produce the user-facing final report.

## Inputs
- End-state pipeline context
- Terminal and progress history

## Core Outputs
- `final_summary`
- Pipeline completion state

## Validation Rules
- Must not include command blocks or shell-command-looking content.
- Should concisely reflect what was done, outcomes, and notable limitations.

## Result
Successful Phase 6 transitions pipeline state to `COMPLETED`.
