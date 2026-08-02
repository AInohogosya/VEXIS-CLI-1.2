"""
Optimized 7-Phase Pipeline Application Entry Point for VEXIS-CLI-3
Implements the lean 7-phase architecture: Initial Planning -> Action Generation -> Execution -> Dynamic Update -> Summarization -> Bot User Review
"""

import sys
import argparse
import time
import signal
from typing import Optional, Dict, Any
from pathlib import Path

from ..core_processing.five_phase_engine import FivePhaseEngine, PipelinePhase, ActionType
from ..utils.exceptions import AIAgentException
from ..utils.logger import get_logger, setup_logging
from ..utils.config import load_config


class FivePhaseAIAgent:
    """Optimized 7-Phase Pipeline AI Agent (V3) implementing the lean architecture"""

    def __init__(self, provider: str = None, model: str = None, config_path: Optional[str] = None,
                 telegram_bot=None):
        self.config = load_config(config_path, force_reload=bool(config_path)) if config_path else load_config()
        self.logger = get_logger("five_phase_app")

        engine_config = self._build_engine_config()

        self.engine = FivePhaseEngine(provider=provider, model=model, config=engine_config,
                                     telegram_bot=telegram_bot)

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info("Optimized 7-Phase Pipeline AI Agent (V3) initialized")

    def _build_engine_config(self) -> Dict[str, Any]:
        """Build engine config from config.yaml"""
        execution = getattr(self.config, "execution", None)
        engine = getattr(self.config, "engine", None)

        return {
            "command_timeout": getattr(execution, "command_timeout", 600),
            "task_timeout": getattr(execution, "task_timeout", 7200),
            "max_iterations": getattr(
                engine,
                "max_iterations",
                getattr(execution, "max_iterations", 500),
            ),
        }

    def _apply_runtime_options(self, options: Dict[str, Any]) -> None:
        """Apply CLI/runtime options to the already-created engine."""
        for option_name in ("command_timeout", "task_timeout", "max_iterations"):
            if option_name in options and options[option_name] is not None:
                setattr(self.engine, option_name, options[option_name])

    def run(self, instruction: str, options: Dict[str, Any], conversation_history=None, cancel_event=None) -> int:
        """Run AI Agent with instruction using Optimized 7-Phase Pipeline (V3)"""
        try:
            self.logger.info(
                "Starting Optimized 7-Phase Pipeline (V3) execution",
                instruction=instruction,
                options=options,
            )

            if options.get("verbose"):
                setup_logging(level="DEBUG")
            elif options.get("log_file"):
                setup_logging(file_path=options["log_file"])

            if not instruction or not instruction.strip():
                self.logger.error("Instruction cannot be empty")
                return 1

            self._apply_runtime_options(options)

            execute_kwargs = {
                "conversation_history": conversation_history,
                "telegram_mode": False,
            }
            if cancel_event is not None:
                execute_kwargs["cancel_event"] = cancel_event

            context = self.engine.execute_instruction(instruction, **execute_kwargs)

            success = context.current_phase == PipelinePhase.COMPLETED

            # Handle ask_user: prompt user for clarification and re-run
            if context.action_type == ActionType.ASK_USER and context.ask_user_question:
                self.logger.info("Action type is ask_user, prompting user for clarification")
                question = context.ask_user_question
                print(f"\n[Agent needs clarification] {question}")
                try:
                    user_answer = input("> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nOperation cancelled by user.")
                    return 1

                if not user_answer:
                    self.logger.warning("User provided empty answer to ask_user question")
                    return 1

                enriched_prompt = f"{instruction}\n\nAdditional context: {question}\nUser response: {user_answer}"
                execute_kwargs.pop("cancel_event", None)
                context = self.engine.execute_instruction(enriched_prompt, **execute_kwargs)
                success = context.current_phase == PipelinePhase.COMPLETED

            # Store completed task info into conversation history for future context
            if success and conversation_history is not None:
                conversation_history.add_completed_task(
                    task_prompt=instruction,
                    steps=list(context.completed_steps),
                    summary=context.final_summary or "",
                )
                self.logger.info(
                    "Stored completed task in conversation history",
                    task=instruction,
                    steps=len(context.completed_steps),
                )

            if not options.get("quiet") and not getattr(context, "cancelled", False):
                self._print_results(context, instruction, success)

            if options.get("output"):
                self._save_results(context, options["output"])

            return 0 if success else 1

        except AIAgentException as e:
            self.logger.error(f"AI Agent error: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 3
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            print(f"Unexpected error: {e}", file=sys.stderr)
            return 4

    def _print_results(self, context, instruction: str, success: bool):
        """Print execution results to console"""
        print(f"\n{'='*60}")
        print("OPTIMIZED 7-PHASE PIPELINE (V3) EXECUTION SUMMARY")
        print(f"{'='*60}")
        print(f"Instruction: {instruction}")
        print(f"Success: {success}")
        print(f"Iterations: {context.iteration_count}")
        print(f"Steps completed: {len(context.completed_steps)}")

        if context.end_time and context.start_time:
            duration = context.end_time - context.start_time
            print(f"Duration: {duration:.2f} seconds")

        if context.error:
            print(f"Error: {context.error}")

        print(f"Final Phase: {context.current_phase.value}")

        if context.completed_steps:
            print(f"\nCompleted Steps:")
            for i, step in enumerate(context.completed_steps, 1):
                print(f"  {i}. {step}")

        if context.final_summary:
            print(f"\n{'='*60}")
            print("FINAL SUMMARY")
            print(f"{'='*60}")
            print(context.final_summary)

        print(f"{'='*60}")

    def _save_results(self, context, output_file: str):
        """Save execution results to file"""
        try:
            import json

            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            results = {
                "instruction": context.user_prompt,
                "success": context.current_phase == PipelinePhase.COMPLETED,
                "final_phase": context.current_phase.value,
                "iterations": context.iteration_count,
                "error": context.error,
                "phase1_output": context.phase1_output,
                "step_list": context.step_list,
                "completed_steps": context.completed_steps,
                "progress_summaries": context.progress_summaries,
                "phase4_output": context.phase4_output,
                "final_summary": context.final_summary,
                "bot_user_review_output": context.bot_user_review_output,
                "bot_user_instructions": context.bot_user_instructions,
                "terminal_log": context.terminal_log,
            }

            if context.end_time and context.start_time:
                results["duration_seconds"] = context.end_time - context.start_time

            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)

            self.logger.info(f"Results saved to: {output_file}")

        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
            print(f"Warning: Failed to save results to {output_file}: {e}", file=sys.stderr)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        try:
            if hasattr(self, 'engine') and self.engine:
                self.engine.cleanup()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        sys.exit(0)

    def shutdown(self):
        """Shutdown AI Agent"""
        self.logger.info("Shutting down Optimized 7-Phase AI Agent (V3)...")
        self.logger.info("Shutdown complete")


def create_five_phase_argument_parser() -> argparse.ArgumentParser:
    """Create V3 Optimized 7-Phase command line argument parser"""
    parser = argparse.ArgumentParser(
        description="VEXIS-CLI-3 - Optimized 7-Phase Pipeline CLI automation (Initial Planning -> Action Generation -> Execution -> Dynamic Update -> Summarization -> Bot User Review)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Create a new project folder"
  %(prog)s "List all files in the current directory"
  %(prog)s --verbose "Install dependencies using pip"
  %(prog)s --output results.json "Set up a development environment"
  %(prog)s --max-iterations 5 "Run a complex build process"
        """
    )

    parser.add_argument(
        "instruction",
        type=str,
        help="Natural language instruction for the AI agent"
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Save execution results to file (JSON format)"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress output except errors"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--log-file",
        type=str,
        help="Log to specified file"
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Maximum number of Phase 2-4 iterations (default: 10)"
    )

    parser.add_argument(
        "--command-timeout",
        type=int,
        default=600,
        help="Timeout for individual commands in seconds (default: 600)"
    )

    parser.add_argument(
        "--task-timeout",
        type=int,
        default=5400,
        help="Timeout for tasks in seconds (default: 5400)"
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate configuration and exit"
    )

    return parser


def validate_arguments(args: argparse.Namespace) -> bool:
    """Validate command line arguments"""
    if not args.instruction or not args.instruction.strip():
        print("Error: Instruction cannot be empty", file=sys.stderr)
        return False

    if args.config and not Path(args.config).exists():
        print(f"Error: Configuration file not found: {args.config}", file=sys.stderr)
        return False

    if args.log_file:
        log_path = Path(args.log_file)
        if not log_path.parent.exists():
            try:
                log_path.parent.mkdir(parents=True)
            except Exception as e:
                print(f"Error: Cannot create log directory: {e}", file=sys.stderr)
                return False

    if args.output:
        output_path = Path(args.output)
        if not output_path.parent.exists():
            try:
                output_path.parent.mkdir(parents=True)
            except Exception as e:
                print(f"Error: Cannot create output directory: {e}", file=sys.stderr)
                return False

    if args.command_timeout <= 0:
        print("Error: Command timeout must be positive", file=sys.stderr)
        return False

    if args.task_timeout <= 0:
        print("Error: Task timeout must be positive", file=sys.stderr)
        return False

    if args.max_iterations < 1:
        print("Error: Max iterations must be at least 1", file=sys.stderr)
        return False

    return True


def main():
    """Main entry point for V3 Optimized 7-Phase Pipeline AI Agent"""
    parser = create_five_phase_argument_parser()
    args = parser.parse_args()

    if not validate_arguments(args):
        sys.exit(1)

    if args.validate_only:
        try:
            config = load_config(args.config)
            print("Configuration validation passed")
            return 0
        except Exception as e:
            print(f"Configuration validation failed: {e}", file=sys.stderr)
            return 1

    try:
        agent = FivePhaseAIAgent(config_path=args.config)
    except Exception as e:
        print(f"Failed to initialize AI Agent: {e}", file=sys.stderr)
        return 1

    options = {
        "verbose": args.verbose,
        "quiet": args.quiet,
        "output": args.output,
        "log_file": args.log_file,
        "max_iterations": args.max_iterations,
        "command_timeout": args.command_timeout,
        "task_timeout": args.task_timeout,
    }

    start_time = time.time()
    exit_code = agent.run(args.instruction, options)
    execution_time = time.time() - start_time

    if not args.quiet:
        print(f"\nTotal execution time: {execution_time:.2f} seconds")
        print(f"Exit code: {exit_code}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())