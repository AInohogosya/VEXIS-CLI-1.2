# Phase 3 Summary: Programmatic Execution

## Purpose
Execute model-generated commands deterministically without additional LLM parsing.

## Inputs
- Parsed command list extracted from Phase 2 output
- Command timeout
- Cancellation event

## Core Outputs
- `last_execution_result` (success, return code, stdout/stderr, timing)
- Updated terminal history/log for downstream phases

## Guarantees
- Command extraction/execution is programmatic.
- Terminal activity is persisted for verification and summarization.
- Cancellation can terminate the foreground command when supported.

## Failure Modes
- Command non-zero exit
- Timeout
- Execution exception
