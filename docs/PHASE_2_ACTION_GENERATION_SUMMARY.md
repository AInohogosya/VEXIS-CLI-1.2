# Phase 2 Summary: Action Generation

## Purpose
Generate a single command block for the *current* step.

## Inputs
- Current step text
- Completed steps
- Remaining steps
- Recent terminal context and progress summaries

## Core Outputs
- `extracted_commands` (raw response containing command block)

## Constraints
- Output must include a Markdown code block.
- Commands should be executable directly (no placeholders).
- For code-edit tasks, prompts strongly guide the model to use `read_file(...)` and `<str_replace>` style edits instead of brittle shell text hacks.

## Failure Modes
- No code block returned
- Unsafe/incomplete command generation
