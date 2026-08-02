# Phase 5 Summary: Verification

## Purpose
Validate whether the original user task is *actually complete* after iterative execution.

## Inputs
- Full terminal log
- Completed steps
- Remaining steps
- Progress summaries

## Core Outputs
- Verification judgment in structured text
- `Summary_of_Progress [...]`
- Optional `original_command [...]` for follow-up recovery work

## Loop Behavior
- If follow-up work is emitted, the engine returns to Phase 2.
- If verification passes with no additional command, execution proceeds to Phase 6.
