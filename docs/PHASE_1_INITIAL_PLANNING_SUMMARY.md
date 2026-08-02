# Phase 1 Summary: Initial Planning

## Purpose
Phase 1 converts the raw user request into an executable plan (`step_list`) and can also decide whether to short-circuit into `answer_directly` or `ask_user` behavior.

## Inputs
- User instruction (`PipelineContext.user_prompt`)
- OS metadata (`metadata.os_info`)
- Conversation history (if available)

## Core Outputs
- `phase1_output`: raw model response
- `step_list`: normalized actionable steps
- `action_type`: one of `run_command`, `write_file`, `read_file`, `answer_directly`, `ask_user`

## Important Implementation Notes
- Action-type selection exists as an explicit control gate before normal step execution.
- If `answer_directly` is selected, the loop does not execute shell commands.
- If `ask_user` is selected, the app requests clarification and re-runs execution with enriched context.

## Failure Modes
- Empty/invalid planning output
- Step extraction failure
- Cancellation or timeout before the loop begins
