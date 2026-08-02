"""
Optimized 7-Phase Pipeline Execution Engine for VEXIS-CLI-3

Phase 0 (optional): Critic & Optimizer pre-phase
Phase 1: Initial Planning (User Prompt -> Step List)
Phase 2: Action Generation (Current Step -> Code Block)
Phase 3: Execution (Programmatic Command Extraction & Execution)
Phase 4: Dynamic Update & Progress Reporting (VEXIS Commands)
Phase 5: Verification (LLM checks if execution was truly successful)
Phase 6: Summarization (Final Report)
Phase 7: Bot User Review (LLM reviews conversation and evaluates output)
"""

import os
import re
import time
import platform
import threading
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field

from .plan_graph import PlanGraph, SubgoalNode, RiskLevel, NodeStatus
from .critic_optimizer import CriticReport, run_critic_optimizer
from .repo_index import RepositoryIndex, IndexManager
from .tool_policy import ToolPolicyEngine, get_default_policy_engine
from .provenance import ProvenanceTracker
from enum import Enum
from pathlib import Path

from ..external_integration.model_runner import ModelRunner, TaskType, ModelRequest, ModelResponse
from ..external_integration.telegram_bot import TelegramBotManager, ConversationHistory
from ..utils.exceptions import ExecutionError, ValidationError
from ..utils.logger import get_logger
from .terminal_history import TerminalHistory, get_terminal_history, TerminalEntryType
from .code_block_handler import extract_code_block as _multi_format_extract, has_code_block as _multi_format_has, remove_code_blocks as _multi_format_remove


class PipelineCancelledError(Exception):
    """Raised when a newer user request cancels the active pipeline."""


class ActionType(Enum):
    """Seven explicit action types the LLM must always select from."""
    RUN_COMMAND = "run_command"
    WRITE_FILE = "write_file"
    READ_FILE = "read_file"
    KEEP_TEXT = "keep_text"
    KEEP_FILE = "keep_file"
    SEARCH = "search"
    LIST_FILES = "list_files"
    ANSWER_DIRECTLY = "answer_directly"
    ASK_USER = "ask_user"


class PipelinePhase(Enum):
    """Optimized 7-Phase Pipeline phases for V3"""
    PHASE0_CRITIC_OPTIMIZER = "phase0_critic_optimizer"
    ACTION_TYPE_SELECTION = "action_type_selection"
    PHASE1_INITIAL_PLANNING = "phase1_initial_planning"
    PHASE2_ACTION_GENERATION = "phase2_action_generation"
    PHASE3_EXECUTION = "phase3_execution"
    PHASE4_DYNAMIC_UPDATE = "phase4_dynamic_update"
    PHASE5_VERIFICATION = "phase5_verification"
    PHASE6_SUMMARIZATION = "phase6_summarization"
    BOT_USER_REVIEW = "bot_user_review"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(Enum):
    """Status of a task in the DAG execution engine"""
    PENDING = "pending"
    EXECUTABLE = "executable"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Task:
    """Represents a single task in the DAG-based execution engine"""
    id: str
    action: str
    waiting_for: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class PipelineContext:
    """Context for tracking Optimized 7-Phase Pipeline execution (V3)"""
    user_prompt: str
    action_type: Optional[ActionType] = None
    ask_user_question: Optional[str] = None
    phase1_output: Optional[str] = None
    step_list: List[str] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    completed_steps: List[str] = field(default_factory=list)
    progress_summaries: List[str] = field(default_factory=list)
    current_step_index: int = 0
    extracted_commands: Optional[str] = None
    terminal_log: str = ""
    last_execution_result: Optional[Dict[str, Any]] = None
    phase4_output: Optional[str] = None
    final_summary: Optional[str] = None
    current_phase: PipelinePhase = PipelinePhase.PHASE1_INITIAL_PLANNING
    iteration_count: int = 0
    max_iterations: int = 500
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    conversation_history: Optional[ConversationHistory] = None
    telegram_mode: bool = False
    telegram_user_id: Optional[int] = None
    cancel_event: Optional[threading.Event] = None
    cancelled: bool = False
    compressed_context: Optional[str] = None
    kept_text_records: List[str] = field(default_factory=list)
    kept_file_records: Dict[str, str] = field(default_factory=dict)
    bot_user_review_output: Optional[str] = None
    bot_user_instructions: Optional[str] = None
    plan_graph: Optional[PlanGraph] = None
    critic_report: Optional[CriticReport] = None
    tool_policy_engine: Optional[ToolPolicyEngine] = None
    provenance_tracker: Optional[ProvenanceTracker] = None
    repository_index: Optional[RepositoryIndex] = None


CODING_TASK_GUIDANCE = """
If the current step involves writing, editing, or modifying code files, here are the RECOMMENDED approaches in order of preference:

1. ALWAYS start by reading the current state of any file you plan to modify:
   read_file(path/to/file)
   The system will read the file and display its contents so you can see the exact code before editing.
   You MUST call read_file BEFORE attempting to write or modify any existing file.

2. For editing EXISTING files, ALWAYS use the str_replace format. This is the PREFERRED approach:
   <str_replace>
   <path>path/to/file.py</path>
   <old>
   [the exact existing code to replace — copy it verbatim from the file you just read]
   </old>
   <new>
   [the new code to insert in place of the old code]
   </new>
   </str_replace>
   The system will apply the replacement automatically. This is MORE RELIABLE than shell-based text manipulation
   because it preserves file encoding, doesn't require escaping special characters, and avoids sed/awk edge cases.

3. For creating NEW files (that do not yet exist), use the write_file format:
   write_file(path/to/newfile.py)
   
   [content to write]
   
   The system will create the file if it does not exist, or apply the changes as a diff-based edit
   if the file already contains content.

CRITICAL RULES:
- You MUST call read_file() before writing or editing any existing file.
- For EXISTING files, prefer str_replace over write_file or shell commands.
- Do NOT use sed/awk/perl one-liners for file editing — they are error-prone.
- Do NOT output entire file contents for edits — use str_replace for targeted changes.
- Normal shell commands remain available for non-file tasks like running builds, git operations, etc."""


class FivePhaseEngine:
    """
    Optimized 7-Phase Pipeline Execution Engine (V3)

    Implements the lean 7-phase architecture:
    - Phase 1: Initial Planning - Build step list from user prompt
    - Phase 2: Action Generation - Generate command for current step
    - Phase 3: Execution - Programmatic command extraction & execution (zero LLM)
    - Phase 4: Dynamic Update - Evaluate results, update step list via VEXIS commands
    - Phase 5: Verification - LLM checks if execution was truly successful
    - Phase 6: Summarization - Final report
    - Phase 7: Bot User Review - LLM reviews conversation and evaluates output
    """

    def __init__(self, provider: str = None, model: str = None, config: Optional[Dict[str, Any]] = None,
                 telegram_bot: Optional[TelegramBotManager] = None):
        self.config = config or {}
        self.logger = get_logger("five_phase_engine")

        self.terminal_history = get_terminal_history()

        self.model_runner = ModelRunner(provider=provider, model=model, config=self.config)

        self.telegram_bot = telegram_bot
        if self.telegram_bot and self.telegram_bot.terminal_history is None:
            self.telegram_bot.terminal_history = self.terminal_history

        self.max_iterations = self.config.get("max_iterations", 500)
        self.command_timeout = self.config.get("command_timeout", 1800)
        self.task_timeout = self.config.get("task_timeout", 7200)
        self._active_cancel_event: Optional[threading.Event] = None
        self._cancel_lock = threading.Lock()

        self._last_failed_instruction: Optional[str] = None
        self._last_failed_conversation_history = None
        self._last_failed_phase: Optional[PipelinePhase] = None
        self._last_failed_iteration: Optional[int] = None
        self._last_failed_terminal_log: Optional[str] = None

        self.tool_policy_engine = get_default_policy_engine()
        self.provenance_tracker = ProvenanceTracker()
        self.repository_index = IndexManager.get_index()

        self.logger.info("Optimized 7-Phase Pipeline Engine (V3) initialized")

    def request_cancel(self) -> None:
        """Request cancellation of the active pipeline and foreground command."""
        with self._cancel_lock:
            if self._active_cancel_event:
                self._active_cancel_event.set()
        if hasattr(self.terminal_history, "cancel_current_command"):
            self.terminal_history.cancel_current_command()

    def get_partial_context(self, conversation_history) -> None:
        """
        Save partial progress from the currently running context into the
        given conversation history.  This is called *before* a newer user
        request cancels and supersedes the active pipeline, so that the
        new task can see what had already been completed.

        Thread-safe: only reads from _current_context under _cancel_lock,
        and writes to the caller-owned conversation_history.
        """
        if conversation_history is None:
            return
        with self._cancel_lock:
            ctx = getattr(self, "_current_context", None)
        if ctx is None:
            return
        steps = list(getattr(ctx, "completed_steps", []))
        summaries = list(getattr(ctx, "progress_summaries", []))
        if not steps and not summaries:
            return
        summary_text = summaries[-1] if summaries else ""
        conversation_history.add_cancelled_task(
            task_prompt=getattr(ctx, "user_prompt", ""),
            steps=steps,
            summary=summary_text,
        )

    def execute_instruction(self, user_prompt: str, conversation_history: Optional[ConversationHistory] = None,
                       telegram_mode: bool = False, telegram_user_id: Optional[int] = None,
                       cancel_event: Optional[threading.Event] = None) -> PipelineContext:
        """
        Execute user instruction through the Optimized 7-Phase Pipeline (V3)

        Flow:
        Phase 1: Generate initial step list
        Loop (Phase 2 -> Phase 3 -> Phase 4) until step_list is empty
        Phase 5: Verify execution success via LLM
          - If original_command exists → go back to Phase 2
          - If no original_command → proceed to Phase 6
        Phase 6: Generate final summary
        Bot User Phase: Review conversation and evaluate output
          - If acceptable → mark completed
          - If instructions provided → execute through Phase 2-4, re-run Phase 6
        """
        self.logger.info("Starting Optimized 7-Phase Pipeline (V3) execution",
                        user_prompt=user_prompt, telegram_mode=telegram_mode)

        context = PipelineContext(
            user_prompt=user_prompt,
            conversation_history=conversation_history,
            telegram_mode=telegram_mode,
            telegram_user_id=telegram_user_id,
            cancel_event=cancel_event or threading.Event(),
            metadata={"os_info": self._get_os_info()},
            tool_policy_engine=self.tool_policy_engine,
            provenance_tracker=self.provenance_tracker,
            repository_index=self.repository_index,
        )

        self._current_context = context
        with self._cancel_lock:
            self._active_cancel_event = context.cancel_event

        try:
            self._raise_if_cancelled(context)

            # Phase 0 (optional): Critic & Optimizer pre-phase
            self._run_phase0(context)

            # Phase 1: Initial Planning
            if not self._run_phase1(context):
                context.current_phase = PipelinePhase.FAILED
                context.error = "Phase 1 (Initial Planning) failed"
                self._send_phase_error_telegram(context, "1", "Initial Planning")
                return context

            # Immediate response gate: check action_type after Phase 1
            if context.action_type == ActionType.ANSWER_DIRECTLY:
                self.logger.info("Action type is answer_directly, skipping to Phase 6 (Summarization)")
                context.current_phase = PipelinePhase.PHASE6_SUMMARIZATION
                if not self._run_immediate_response(context):
                    context.current_phase = PipelinePhase.FAILED
                    context.error = "Immediate response generation failed"
                    return context

                self._raise_if_cancelled(context)

                # Bot User Phase: Review conversation and evaluate output
                if not self._run_bot_user_review(context):
                    context.current_phase = PipelinePhase.FAILED
                    context.error = "Bot User review failed"
                    return context

                self._raise_if_cancelled(context)

                context.current_phase = PipelinePhase.COMPLETED
                context.end_time = time.time()
                self.logger.info("Immediate response completed successfully",
                               duration=context.end_time - context.start_time)
                return context

            if context.action_type == ActionType.ASK_USER:
                self.logger.info("Action type is ask_user, returning question to caller")
                context.current_phase = PipelinePhase.COMPLETED
                context.end_time = time.time()
                return context

            if context.action_type == ActionType.KEEP_TEXT:
                self.logger.info("Action type is keep_text, storing text in memory records and completing")
                context.current_phase = PipelinePhase.COMPLETED
                context.end_time = time.time()
                kept_count = len(context.kept_text_records)
                self.logger.info(f"KeepTextCommand completed. Total text records in memory: {kept_count}")
                return context

            if context.action_type == ActionType.KEEP_FILE:
                self.logger.info("Action type is keep_file, storing file in memory records and completing")
                context.current_phase = PipelinePhase.COMPLETED
                context.end_time = time.time()
                kept_count = len(context.kept_file_records)
                self.logger.info(f"KeepFileCommand completed. Total file records in memory: {kept_count}")
                return context

            # Check if we have DAG tasks to execute
            if context.tasks:
                self.logger.info("Using DAG-based task execution engine", task_count=len(context.tasks))
                task_start_time = time.time()
                
                if not self._execute_dag_tasks(context):
                    if not context.error:
                        context.error = "DAG task execution failed"
                    context.current_phase = PipelinePhase.FAILED
                    self._send_phase_error_telegram(context, "2-4", "DAG Task Execution")
                    return context
                
                self._raise_if_cancelled(context)
                self.logger.info("DAG task execution completed, proceeding to Phase 5 (Verification)")
            else:
                # Legacy Phase 2-4 Loop: Action Generation -> Execution -> Dynamic Update
                self.logger.info("Using legacy step_list execution")
                task_start_time = time.time()
                while context.iteration_count < context.max_iterations:
                    context.iteration_count += 1
                    self.logger.info(f"Starting iteration {context.iteration_count}",
                                   phase=context.current_phase.value)

                    if self.task_timeout > 0:
                        elapsed = time.time() - task_start_time
                        if elapsed > self.task_timeout:
                            error_msg = f"Task timeout after {elapsed:.1f}s (limit: {self.task_timeout}s)"
                            self.logger.error(error_msg)
                            context.current_phase = PipelinePhase.FAILED
                            context.error = error_msg
                            self._last_failed_instruction = context.user_prompt
                            self._last_failed_conversation_history = context.conversation_history
                            self._last_failed_phase = context.current_phase
                            self._last_failed_iteration = context.iteration_count
                            self._last_failed_terminal_log = context.terminal_log
                            self._send_timeout_telegram(context, elapsed)
                            return context

                    self._raise_if_cancelled(context)

                    # Phase 2: Action Generation
                    if not self._run_phase2(context):
                        context.current_phase = PipelinePhase.FAILED
                        context.error = "Phase 2 (Action Generation) failed"
                        self._send_phase_error_telegram(context, "2", "Action Generation")
                        return context

                    self._raise_if_cancelled(context)

                    # Phase 3: Execution (100% programmatic, zero LLM)
                    if not self._run_phase3(context):
                        context.current_phase = PipelinePhase.FAILED
                        context.error = "Phase 3 (Execution) failed"
                        self._send_phase_error_telegram(context, "3", "Execution")
                        return context

                    self._raise_if_cancelled(context)

                    # Phase 4: Dynamic Update & Progress Reporting
                    if not self._run_phase4(context):
                        context.current_phase = PipelinePhase.FAILED
                        context.error = "Phase 4 (Dynamic Update) failed"
                        self._send_phase_error_telegram(context, "4", "Dynamic Update")
                        return context

                    self._raise_if_cancelled(context)

                    # Context compression at iteration intervals (every 10 iterations)
                    if context.iteration_count > 0 and context.iteration_count % 10 == 0:
                        self._compress_context(context)

                    # State transition: if step_list is empty, task is complete
                    if not context.step_list:
                        self.logger.info("Step list is empty, proceeding to Phase 5 (Verification)")
                        break

                    self.logger.info(f"Phase 4 completed, {len(context.step_list)} steps remaining, continuing loop")

                if context.iteration_count >= context.max_iterations:
                    self.logger.warning("Maximum iterations reached, forcing verification")

                self._raise_if_cancelled(context)

                # Phase 5: Verification - LLM confirms true success
                if not self._run_phase5(context):
                    context.current_phase = PipelinePhase.FAILED
                    context.error = "Phase 5 (Verification) failed"
                    self._send_phase_error_telegram(context, "5", "Verification")
                    return context

                self._raise_if_cancelled(context)

                # If verification generated an original_command, go back to Phase 2
                if context.step_list:
                    self.logger.info(
                        f"Verification found issues, {len(context.step_list)} recovery steps added. "
                        "Returning to Phase 2 (Action Generation)"
                    )
                    # Reset commands; step_list already populated, loop back to Phase 2
                    context.extracted_commands = None
                    while context.iteration_count < context.max_iterations:
                        context.iteration_count += 1
                        self.logger.info(f"Recovery iteration {context.iteration_count}",
                                       phase=context.current_phase.value)

                        if self.task_timeout > 0:
                            elapsed = time.time() - task_start_time
                            if elapsed > self.task_timeout:
                                error_msg = f"Task timeout after {elapsed:.1f}s (limit: {self.task_timeout}s)"
                                self.logger.error(error_msg)
                                context.current_phase = PipelinePhase.FAILED
                                context.error = error_msg
                                self._send_timeout_telegram(context, elapsed)
                                return context

                        self._raise_if_cancelled(context)

                        if not self._run_phase2(context):
                            context.current_phase = PipelinePhase.FAILED
                            context.error = "Phase 2 (Action Generation) failed during recovery"
                            return context

                        self._raise_if_cancelled(context)

                        if not self._run_phase3(context):
                            context.current_phase = PipelinePhase.FAILED
                            context.error = "Phase 3 (Execution) failed during recovery"
                            return context

                        self._raise_if_cancelled(context)

                        if not self._run_phase4(context):
                            context.current_phase = PipelinePhase.FAILED
                            context.error = "Phase 4 (Dynamic Update) failed during recovery"
                            return context

                        self._raise_if_cancelled(context)

                        # Context compression at iteration intervals (every 10 iterations)
                        if context.iteration_count > 0 and context.iteration_count % 10 == 0:
                            self._compress_context(context)

                        if not context.step_list:
                            self.logger.info("Recovery step list is empty, proceeding to Phase 5 (Verification)")
                            break

                    # After recovery loop, verify again
                    self._raise_if_cancelled(context)

                    if context.step_list:
                        if not self._run_phase5(context):
                            context.current_phase = PipelinePhase.FAILED
                            context.error = "Phase 5 (Verification) failed after recovery"
                            return context

                        self._raise_if_cancelled(context)

                        # If still has original_command after recovery, force proceed
                        if context.step_list:
                            self.logger.warning("Still has recovery steps after verification, clearing to continue")
                            context.step_list = []

                    self._raise_if_cancelled(context)

            # Phase 6: Summarization (old Phase 5)
            if not self._run_phase6(context):
                context.current_phase = PipelinePhase.FAILED
                context.error = "Phase 6 (Summarization) failed"
                self._send_phase_error_telegram(context, "6", "Summarization")
                return context

            self._raise_if_cancelled(context)

            # Bot User Phase: Review conversation and evaluate output
            if not self._run_bot_user_review(context):
                context.current_phase = PipelinePhase.FAILED
                context.error = "Bot User review failed"
                return context

            self._raise_if_cancelled(context)

            # If Bot User provided instructions, execute them
            if context.bot_user_instructions:
                self.logger.info("Bot User provided correction instructions, executing them")
                context.step_list = [context.bot_user_instructions]
                context.bot_user_instructions = None

                # Execute the correction instructions through Phase 2-4 loop
                task_start_time = time.time()
                while context.iteration_count < context.max_iterations:
                    context.iteration_count += 1
                    self.logger.info(f"Bot User correction iteration {context.iteration_count}")

                    if self.task_timeout > 0:
                        elapsed = time.time() - task_start_time
                        if elapsed > self.task_timeout:
                            error_msg = f"Task timeout after {elapsed:.1f}s (limit: {self.task_timeout}s)"
                            self.logger.error(error_msg)
                            context.current_phase = PipelinePhase.FAILED
                            context.error = error_msg
                            return context

                    self._raise_if_cancelled(context)

                    if not self._run_phase2(context):
                        context.current_phase = PipelinePhase.FAILED
                        context.error = "Phase 2 (Action Generation) failed during Bot User correction"
                        return context

                    self._raise_if_cancelled(context)

                    if not self._run_phase3(context):
                        context.current_phase = PipelinePhase.FAILED
                        context.error = "Phase 3 (Execution) failed during Bot User correction"
                        return context

                    self._raise_if_cancelled(context)

                    if not self._run_phase4(context):
                        context.current_phase = PipelinePhase.FAILED
                        context.error = "Phase 4 (Dynamic Update) failed during Bot User correction"
                        return context

                    self._raise_if_cancelled(context)

                    if not context.step_list:
                        self.logger.info("Bot User correction steps completed")
                        break

                # Re-run summarization after corrections
                if not self._run_phase6(context):
                    context.current_phase = PipelinePhase.FAILED
                    context.error = "Phase 6 (Summarization) failed after Bot User correction"
                    return context

            context.current_phase = PipelinePhase.COMPLETED
            context.end_time = time.time()
            self._emit_final_summary(context)

            self.logger.info("Optimized 7-Phase Pipeline (V3) execution completed successfully",
                           duration=context.end_time - context.start_time,
                           iterations=context.iteration_count)

            return context

        except PipelineCancelledError as e:
            self.logger.info(f"Pipeline execution cancelled: {e}")
            context.current_phase = PipelinePhase.FAILED
            context.error = str(e)
            context.cancelled = True
            context.end_time = time.time()
            return context
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}")
            context.current_phase = PipelinePhase.FAILED
            context.error = str(e)
            context.end_time = time.time()
            if context.telegram_mode and self.telegram_bot and context.telegram_user_id:
                try:
                    self._send_telegram_message_sync(
                        context.telegram_user_id,
                        f"Error Occurred\n\n{str(e)}\n\nThe task could not be completed due to an error."
                    )
                except Exception as te:
                    self.logger.warning(f"Failed to send error notification to Telegram: {te}")
            return context
        finally:
            with self._cancel_lock:
                if self._active_cancel_event is context.cancel_event:
                    self._active_cancel_event = None

    def _get_executable_tasks(self, tasks: List[Task]) -> List[Task]:
        """
        Find tasks that are ready to execute (waiting_for is empty and status is PENDING or EXECUTABLE).
        
        Args:
            tasks: List of all tasks
            
        Returns:
            List of tasks that can be executed
        """
        executable = []
        for task in tasks:
            if task.status in (TaskStatus.PENDING, TaskStatus.EXECUTABLE) and not task.waiting_for:
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.EXECUTABLE
                executable.append(task)
        return executable

    def _check_deadlock(self, tasks: List[Task]) -> bool:
        """
        Check if the task graph is in a deadlock state.
        
        Deadlock occurs when there are no executable tasks but there are still
        uncompleted tasks (all remaining tasks have unmet dependencies).
        
        Note: BLOCKED tasks are excluded from deadlock detection since they
        are blocked due to prerequisite failures, not circular dependencies.
        
        Args:
            tasks: List of all tasks
            
        Returns:
            True if deadlock detected, False otherwise
        """
        has_pending = False
        for task in tasks:
            if task.status in (TaskStatus.PENDING, TaskStatus.EXECUTABLE):
                has_pending = True
                if not task.waiting_for:
                    return False
        # If we only have BLOCKED tasks left (no PENDING), it's not a deadlock
        # - it's a failure propagation
        if not has_pending:
            return False
        return has_pending

    def _mark_task_completed(self, task: Task, tasks: List[Task]) -> None:
        """
        Mark a task as completed and remove its ID from waiting_for of other tasks.
        
        Args:
            task: The completed task
            tasks: List of all tasks
        """
        task.status = TaskStatus.COMPLETED
        for other_task in tasks:
            if task.id in other_task.waiting_for:
                other_task.waiting_for.remove(task.id)

    def _mark_task_failed(self, task: Task, tasks: List[Task]) -> None:
        """
        Mark a task as failed and block all dependent tasks (transitively).
        
        Args:
            task: The failed task
            tasks: List of all tasks
        """
        task.status = TaskStatus.FAILED
        # Use a queue to handle transitive blocking
        failed_ids = {task.id}
        queue = [task.id]
        
        while queue:
            current_id = queue.pop(0)
            for other_task in tasks:
                if other_task.status == TaskStatus.PENDING and current_id in other_task.waiting_for:
                    other_task.status = TaskStatus.BLOCKED
                    if other_task.id not in failed_ids:
                        failed_ids.add(other_task.id)
                        queue.append(other_task.id)

    def _execute_dag_tasks(self, context: PipelineContext) -> bool:
        """
        Execute tasks using a DAG-based execution engine.
        
        This method implements the following logic:
        1. Find tasks where waiting_for is empty (executable tasks)
        2. If no executable tasks and uncompleted tasks remain, deadlock detected
        3. Execute the executable task
        4. On success, remove task ID from waiting_for of other tasks
        5. On failure, mark dependent tasks as blocked
        6. Repeat until all tasks are complete
        
        Args:
            context: The pipeline context containing tasks
            
        Returns:
            True if all tasks completed successfully, False otherwise
        """
        self.logger.info("Starting DAG-based task execution", task_count=len(context.tasks))
        
        iteration = 0
        max_task_iterations = len(context.tasks) * 10
        
        while iteration < max_task_iterations:
            iteration += 1
            
            # Check if all tasks are done
            all_done = all(
                task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.BLOCKED)
                for task in context.tasks
            )
            if all_done:
                break
            
            # Find executable tasks
            executable_tasks = self._get_executable_tasks(context.tasks)
            
            if not executable_tasks:
                # Check for deadlock
                if self._check_deadlock(context.tasks):
                    self.logger.error("Deadlock detected: no executable tasks but uncompleted tasks remain")
                    context.error = "Task dependency deadlock detected"
                    return False
                break
            
            # Execute the first executable task
            task = executable_tasks[0]
            task.status = TaskStatus.RUNNING
            
            self.logger.info(f"Executing task {task.id}: {task.action[:50]}...")
            
            # Execute the task using Phase 2, 3, 4
            success = self._execute_single_task(context, task)
            
            if success:
                self._mark_task_completed(task, context.tasks)
                self.logger.info(f"Task {task.id} completed successfully")
            else:
                self._mark_task_failed(task, context.tasks)
                self.logger.warning(f"Task {task.id} failed, dependent tasks blocked")
        
        # Check if all tasks completed
        completed_count = sum(1 for t in context.tasks if t.status == TaskStatus.COMPLETED)
        failed_count = sum(1 for t in context.tasks if t.status == TaskStatus.FAILED)
        blocked_count = sum(1 for t in context.tasks if t.status == TaskStatus.BLOCKED)
        
        self.logger.info(
            "DAG execution completed",
            completed=completed_count,
            failed=failed_count,
            blocked=blocked_count
        )
        
        return failed_count == 0 and blocked_count == 0

    def _execute_single_task(self, context: PipelineContext, task: Task) -> bool:
        """
        Execute a single task through Phases 2, 3, and 4.
        
        Args:
            context: The pipeline context
            task: The task to execute
            
        Returns:
            True if task executed successfully, False otherwise
        """
        # Temporarily set step_list for compatibility with existing phase methods
        original_step_list = context.step_list
        context.step_list = [task.action]
        
        try:
            # Phase 2: Action Generation
            if not self._run_phase2(context):
                task.error = "Phase 2 (Action Generation) failed"
                return False
            
            self._raise_if_cancelled(context)
            
            # Phase 3: Execution
            if not self._run_phase3(context):
                task.error = "Phase 3 (Execution) failed"
                return False
            
            self._raise_if_cancelled(context)
            
            # Phase 4: Dynamic Update (simplified for DAG)
            # For DAG execution, we don't need the full Phase 4 iteration
            # Record the result and let the normal flow handle updates
            if not self._run_phase4(context):
                task.error = "Phase 4 (Dynamic Update) failed"
                return False

            task.result = str(context.last_execution_result or {})
            
            return True
            
        except PipelineCancelledError:
            raise
        except Exception as e:
            task.error = str(e)
            self.logger.error(f"Task execution failed: {e}")
            return False
        finally:
            context.step_list = original_step_list

    def _raise_if_cancelled(self, context: PipelineContext) -> None:
        if context.cancel_event and context.cancel_event.is_set():
            raise PipelineCancelledError("Task cancelled because a newer user request was received")

    def _run_phase0(self, context: PipelineContext) -> None:
        """
        Phase 0 (optional): Critic & Optimizer pre-phase.

        - Converts the user prompt into a PlanGraph if a step_list exists
        - Analyzes the plan for ambiguity, risk, missing elements
        - Optimizes the plan for lower risk and fewer commands
        - Sets low-confidence nodes for dry-run execution
        """
        self.logger.info("Phase 0: Critic & Optimizer pre-phase started")
        context.current_phase = PipelinePhase.PHASE0_CRITIC_OPTIMIZER

        enable_critic = self.config.get("enable_critic", True)
        enable_optimizer = self.config.get("enable_optimizer", True)

        if not enable_critic and not enable_optimizer:
            self.logger.info("Phase 0 disabled via config")
            return

        graph = PlanGraph(goal_description=context.user_prompt)
        context.plan_graph = graph

        graph, report = run_critic_optimizer(
            graph,
            enable_critic=enable_critic,
            enable_optimizer=enable_optimizer,
        )
        context.critic_report = report

        if report.issues:
            self.logger.info(
                f"Phase 0 found {len(report.issues)} issue(s)",
                risk_score=f"{report.risk_score:.2f}",
                ambiguity_score=f"{report.ambiguity_score:.2f}",
                optimizations=report.optimizations_applied,
            )
            for issue in report.issues[:5]:
                self.logger.info(
                    f"  [{issue.issue_type}] {issue.description[:80]}",
                    severity=f"{issue.severity:.2f}",
                )

        if report.passes:
            self.logger.info("Phase 0: Plan passes critic analysis")
        else:
            self.logger.info(
                "Phase 0: Plan requires attention",
                optimizations_applied=report.optimizations_applied,
            )

    def _run_phase1(self, context: PipelineContext) -> bool:
        """
        Phase 1: Initial Planning

        Send the full conversation history (including completed tasks' step lists)
        as the main prompt to the base model, so the model understands the complete
        context of what has been done and what remains.

        The LLM outputs a step_list in VEXIS format which is parsed to populate
        the step list.

        Includes retry logic with progressively simpler prompts and a fallback
        default action_type to prevent frequent Phase 1 failures.
        """
        self.logger.info("Phase 1: Initial Planning started")
        context.current_phase = PipelinePhase.PHASE1_INITIAL_PLANNING

        try:
            os_info = context.metadata.get("os_info", self._get_os_info())

            # Build the main prompt from full conversation history.
            # Truncate history to prevent oversized prompts that cause model failures.
            if context.conversation_history:
                full_history = context.conversation_history.format_for_prompt()
                combined_prompt = self._truncate_text(full_history, max_chars=8000, label="conversation_history")
                self.logger.info("Phase 1: Using full conversation history as prompt")
            else:
                combined_prompt = context.user_prompt

            response = self._run_phase1_with_retry(combined_prompt, os_info, context)
            self._raise_if_cancelled(context)

            if not response or not response.success:
                self.logger.error(f"Phase 1 model execution failed after retries: {response.error if response else 'no response'}")
                return False

            context.phase1_output = response.content

            # Parse action_type and step_list from Phase 1 output
            parsed = self._parse_vexis_commands(response.content)

            action_type_str = parsed.get("action_type")
            if action_type_str:
                try:
                    context.action_type = ActionType(action_type_str)
                    self.logger.info(f"Phase 1: Parsed action_type={context.action_type.value}")
                except ValueError:
                    self.logger.warning(f"Phase 1: Unknown action_type '{action_type_str}', defaulting to run_command")
                    context.action_type = ActionType.RUN_COMMAND
            else:
                # Fallback: if no action_type found but we have tasks/step_list, default to run_command
                if parsed.get("tasks") or parsed.get("step_list"):
                    self.logger.warning("Phase 1: No action_type found but tasks/step_list present, defaulting to run_command")
                    context.action_type = ActionType.RUN_COMMAND
                else:
                    # Last resort: treat the entire prompt as a single run_command step
                    self.logger.warning("Phase 1: No action_type or tasks found, creating default run_command step")
                    context.action_type = ActionType.RUN_COMMAND
                    context.step_list = [context.user_prompt]
                    context.tasks = [Task(id="task_0", action=context.user_prompt, waiting_for=[])]
                    self.logger.info("Phase 1: Created default task from user prompt")

            # Parse ask_user question if present
            if parsed.get("question"):
                context.ask_user_question = parsed["question"]

            # Parse keep_text payload if present
            if parsed.get("keep_text"):
                context.kept_text_records.append(parsed["keep_text"])
                self.logger.info(f"Phase 1: Stored keep_text ({len(parsed['keep_text'])} chars) in memory records")

            # Parse keep_file payload if present
            if parsed.get("keep_file"):
                keep_filepath = parsed["keep_file"]
                if not os.path.isabs(keep_filepath):
                    keep_filepath = os.path.join(os.getcwd(), keep_filepath)
                path_error = self._validate_file_path(keep_filepath)
                if path_error:
                    self.logger.warning(f"Phase 1: keep_file path validation failed: {path_error}")
                else:
                    try:
                        with open(keep_filepath, 'r', encoding='utf-8', errors='replace') as f:
                            kept_content = f.read()
                        context.kept_file_records[keep_filepath] = kept_content
                        self.logger.info(f"Phase 1: Stored keep_file {keep_filepath} ({len(kept_content)} chars) in memory records")
                    except Exception as e:
                        self.logger.warning(f"Phase 1: Failed to read keep_file {keep_filepath}: {e}")

            if parsed.get("tasks"):
                context.tasks = [
                    Task(
                        id=t["id"],
                        action=t["action"],
                        waiting_for=t.get("waiting_for", [])
                    )
                    for t in parsed["tasks"]
                ]
                self.logger.info(f"Phase 1: Parsed {len(context.tasks)} tasks from LLM output")
                if not context.step_list:
                    context.step_list = [t.action for t in context.tasks]
            elif parsed.get("step_list"):
                context.step_list = parsed["step_list"]
                context.tasks = [
                    Task(id=f"task_{i}", action=step, waiting_for=[] if i == 0 else [f"task_{i-1}"])
                    for i, step in enumerate(context.step_list)
                ]
                self.logger.info(f"Phase 1: Parsed {len(context.step_list)} steps from LLM output")
            elif not context.step_list:
                self.logger.warning("Phase 1: No tasks or step_list found in output, treating as single step")
                context.step_list = [context.user_prompt]
                context.tasks = [Task(id="task_0", action=context.user_prompt, waiting_for=[])]

            self.logger.info("Phase 1 completed successfully",
                           task_count=len(context.tasks),
                           step_count=len(context.step_list),
                           output_length=len(response.content) if response.content else 0)

            return True

        except PipelineCancelledError:
            raise
        except Exception as e:
            self.logger.error(f"Phase 1 failed: {e}")
            return False

    def _run_phase1_with_retry(self, combined_prompt: str, os_info: str, context: PipelineContext):
        """
        Attempt Phase 1 with retry logic.

        First attempt uses the full prompt with conversation history.
        Second attempt uses a simplified prompt focusing only on the user request.
        Third attempt uses an ultra-minimal prompt.
        """
        max_attempts = 3

        for attempt in range(max_attempts):
            self._raise_if_cancelled(context)

            if attempt == 0:
                # First attempt: full prompt (original behavior)
                prompt = combined_prompt
            elif attempt == 1:
                # Second attempt: simplified prompt with just the user request
                self.logger.warning("Phase 1 retry attempt 2: using simplified prompt without conversation history")
                prompt = context.user_prompt
            else:
                # Third attempt: ultra-minimal prompt
                self.logger.warning("Phase 1 retry attempt 3: using minimal prompt")
                prompt = f"Plan how to: {context.user_prompt}"

            request = ModelRequest(
                task_type=TaskType.PHASE1_INITIAL_PLANNING,
                prompt=prompt,
                context={
                    "user_prompt": context.user_prompt,
                    "os_info": os_info,
                },
                max_tokens=4000,
                temperature=0.7
            )

            response = self.model_runner.run_model(request)

            if response and response.success:
                return response

            self.logger.warning(
                f"Phase 1 attempt {attempt + 1}/{max_attempts} failed",
                error=response.error if response else "no response",
            )

        # All attempts exhausted — return the last response (with error info)
        return response

    def _run_phase2(self, context: PipelineContext) -> bool:
        """
        Phase 2: Action Generation

        Take the current step (first in step_list) and have the LLM generate
        the OS command to execute it. The command MUST be inside a markdown
        code block. No midway progress summaries. No text outside the code block.

        Strict constraints:
        - Command MUST be inside a markdown code block
        - No incomplete commands (no placeholders)
        - Nothing outside the code block except # comments inside it
        - No midway progress summaries (COMPLETELY ABOLISHED from V2)
        """
        self.logger.info("Phase 2: Action Generation started")
        context.current_phase = PipelinePhase.PHASE2_ACTION_GENERATION

        if not context.step_list:
            self.logger.error("Phase 2: No steps remaining in step list")
            return False

        current_step = context.step_list[0]
        self.logger.info(f"Phase 2: Generating command for step: {current_step}")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                context_data = {
                    "current_step": current_step,
                    "os_info": context.metadata.get("os_info", self._get_os_info()),
                }
                if self._is_coding_task(current_step, context.user_prompt):
                    context_data["coding_task_guidance"] = CODING_TASK_GUIDANCE
                else:
                    context_data["coding_task_guidance"] = ""

                request = ModelRequest(
                    task_type=TaskType.PHASE2_ACTION_GENERATION,
                    prompt=current_step,
                    context=context_data,
                    max_tokens=3000,
                    temperature=0.3
                )

                response = self.model_runner.run_model(request)
                self._raise_if_cancelled(context)

                if not response.success:
                    self.logger.error(f"Phase 2 model execution failed: {response.error}")
                    if attempt < max_retries - 1:
                        continue
                    return False

                # Extract code block from response (programmatic, zero LLM)
                commands = self._extract_code_block(response.content)

                if commands:
                    context.extracted_commands = commands
                    self.logger.info("Phase 2 completed successfully",
                                   commands_length=len(commands))

                    trace_id = context.provenance_tracker.start_trace(
                        phase="phase2_action_generation",
                        model=getattr(self.model_runner, 'model', None),
                        provider=getattr(self.model_runner, 'provider', None),
                    ) if context.provenance_tracker else ""
                    if context.provenance_tracker:
                        context.provenance_tracker.record(
                            trace_id,
                            phase="phase2_action_generation",
                            confidence=0.7 if attempt == 0 else 0.5,
                            source_command=current_step,
                            iteration=context.iteration_count,
                        )

                    policy_score = None
                    if context.tool_policy_engine:
                        first_line = commands.strip().split("\n")[0] if commands else ""
                        policy_score = context.tool_policy_engine.score_command(first_line)
                        if policy_score and policy_score.composite < 0.4:
                            safe_alts = context.tool_policy_engine.get_safe_alternatives(first_line)
                            if safe_alts:
                                self.logger.info(
                                    f"Low-score command ({policy_score.composite:.2f}), "
                                    f"suggested alternatives: {safe_alts[:2]}"
                                )

                    if context.telegram_mode and self.telegram_bot and context.telegram_user_id:
                        try:
                            self._send_telegram_message_sync(
                                context.telegram_user_id,
                                f"Executing step: {current_step}\n```\n{commands}\n```"
                            )
                        except PipelineCancelledError:
                            raise
                        except Exception as e:
                            self.logger.warning(f"Failed to send command to Telegram: {e}")

                    return True
                else:
                    self.logger.warning(f"Phase 2: No code block found in attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        continue
                    return False

            except PipelineCancelledError:
                raise
            except Exception as e:
                self.logger.error(f"Phase 2 failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    continue
                return False

        return False

    def _validate_file_path(self, filepath: str) -> Optional[str]:
        """Validate file path for path traversal and sensitive directory access.

        Returns None if valid, or an error message string if invalid.
        """
        try:
            resolved = Path(filepath).resolve()
        except (ValueError, OSError) as e:
            return f"Invalid path: {e}"

        sensitive_prefixes = [
            Path("/etc"), Path("/var"), Path("/usr"), Path("/bin"),
            Path("/sbin"), Path("/lib"), Path("/lib64"), Path("/opt"),
            Path("/sys"), Path("/proc"), Path("/dev"), Path("/boot"),
            Path("/root"),
        ]
        for prefix in sensitive_prefixes:
            try:
                resolved.relative_to(prefix)
                return f"Access denied: {filepath} (restricted system directory)"
            except ValueError:
                continue

        parent = resolved.parent
        if not os.access(parent, os.R_OK):
            return f"Access denied: parent directory not readable for {filepath}"

        return None

    def _run_phase3(self, context: PipelineContext) -> bool:
        """
        Phase 3: Execution

        100% programmatic command extraction and execution.
        NO LLM calls for command extraction (abolished from V2).
        Uses regex to extract commands from the code block, then executes them.

        Supports native action formats:
        - read_file(path) - Read and display file contents
        - write_file(path) - Write content to file (diff-based if file exists)
        - keep_text("...") - Keep text in memory records (excluded from compression)
        - keep_file(path) - Keep a file snapshot in memory records (excluded from compression)
        - <str_replace> blocks - Targeted text replacement in existing files
        - Shell commands - Standard terminal commands
        - search("pattern", "path") - Search file contents across the project (read-only)
        - list_files("path") - List files and directories to explore structure (read-only)

        After execution, captures stdout and stderr, classifies failures,
        and passes results to Phase 4.
        """
        self.logger.info("Phase 3: Execution started")
        context.current_phase = PipelinePhase.PHASE3_EXECUTION

        try:
            if not context.extracted_commands:
                self.logger.error("Phase 3: No commands to execute")
                return False

            raw_code = context.extracted_commands or ""

            # Handle <str_replace> blocks programmatically (before command parsing)
            str_replace_results = []
            str_replace_pattern = re.compile(
                r'<str_replace>\s*<path>(.*?)</path>\s*<old>(.*?)</old>\s*<new>(.*?)</new>\s*</str_replace>',
                re.DOTALL | re.IGNORECASE
            )
            for match in str_replace_pattern.finditer(raw_code):
                filepath = match.group(1).strip()
                old_str = match.group(2)
                new_str = match.group(3)
                path_error = self._validate_file_path(filepath)
                if path_error:
                    str_replace_results.append(f"--- Error: {path_error} ---")
                    continue
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                        existing = f.read()
                    if old_str in existing:
                        existing = existing.replace(old_str, new_str, 1)
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(existing)
                        str_replace_results.append(
                            f"--- str_replace applied to {filepath}: replaced {len(old_str)} chars with {len(new_str)} chars ---"
                        )
                    else:
                        str_replace_results.append(
                            f"--- Warning: target text not found in {filepath} - edit skipped ---"
                        )
                except Exception as e:
                    str_replace_results.append(f"--- Error applying str_replace to {filepath}: {e} ---")

            # Remove str_replace blocks before parsing remaining commands
            remaining_code = str_replace_pattern.sub('', raw_code)

            # Parse remaining commands (zero LLM)
            commands = self._parse_commands(remaining_code)

            # Separate native action commands from shell commands
            file_read_outputs = []
            file_write_outputs = []
            shell_commands = []
            for cmd in commands:
                stripped = cmd.strip()
                # Handle read_file with proper quote handling
                read_file_match = re.match(r'^read_file\(\s*["\']?(.+?)["\']?\s*\)$', stripped)
                if read_file_match:
                    filepath = read_file_match.group(1).strip().strip("'\"")
                    # Handle relative paths
                    if not os.path.isabs(filepath):
                        filepath = os.path.join(os.getcwd(), filepath)
                    path_error = self._validate_file_path(filepath)
                    if path_error:
                        file_read_outputs.append(f"--- Error reading {filepath}: {path_error} ---")
                    else:
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                                content = f.read()
                            file_read_outputs.append(f"--- Content of {filepath} ---\n{content}")
                        except Exception as e:
                            file_read_outputs.append(f"--- Error reading {filepath}: {e} ---")
                else:
                    search_match = re.match(
                        r'^search\(\s*["\'](.+?)["\'](?:\s*,\s*["\'](.+?)["\'])?\s*\)$',
                        stripped,
                    )
                    if search_match:
                        search_pattern = search_match.group(1)
                        search_path = (search_match.group(2) or ".").strip()
                        file_read_outputs.append(
                            self._handle_search(search_pattern, search_path)
                        )
                        continue

                    list_files_match = re.match(
                        r'^list_files\(\s*["\'](.+?)["\'](?:\s*,\s*["\'](.+?)["\'])?\s*\)$',
                        stripped,
                    )
                    if list_files_match:
                        list_path = list_files_match.group(1).strip()
                        recursive = (list_files_match.group(2) or "").strip().lower() in (
                            "recursive", "r", "true"
                        )
                        file_read_outputs.append(
                            self._handle_list_files(list_path, recursive)
                        )
                        continue

                    keep_text_match = re.match(r'^keep_text\(\s*["\'](.+)["\']\s*\)$', stripped, re.DOTALL)
                    if keep_text_match:
                        keep_text_payload = keep_text_match.group(1)
                        context.kept_text_records.append(keep_text_payload)
                        file_read_outputs.append(
                            f"--- KeepTextCommand stored {len(keep_text_payload)} characters in memory records ---"
                        )
                        continue

                    keep_file_match = re.match(r'^keep_file\(\s*["\'](.+)["\']\s*\)$', stripped)
                    if keep_file_match:
                        keep_filepath = keep_file_match.group(1).strip().strip("'\"")
                        if not os.path.isabs(keep_filepath):
                            keep_filepath = os.path.join(os.getcwd(), keep_filepath)
                        path_error = self._validate_file_path(keep_filepath)
                        if path_error:
                            file_read_outputs.append(f"--- Error keeping file {keep_filepath}: {path_error} ---")
                        else:
                            try:
                                with open(keep_filepath, 'r', encoding='utf-8', errors='replace') as f:
                                    kept_content = f.read()
                                context.kept_file_records[keep_filepath] = kept_content
                                file_read_outputs.append(
                                    f"--- KeepFileCommand stored {keep_filepath} in memory records ({len(kept_content)} chars) ---"
                                )
                            except Exception as e:
                                file_read_outputs.append(f"--- Error keeping file {keep_filepath}: {e} ---")
                        continue

                    # Handle write_file with proper quote handling
                    write_file_match = re.match(r'^write_file\(\s*["\']?(.+?)["\']?\s*\)$', stripped)
                    if write_file_match:
                        filepath = write_file_match.group(1).strip().strip("'\"")
                        # Handle relative paths
                        if not os.path.isabs(filepath):
                            filepath = os.path.join(os.getcwd(), filepath)
                        path_error = self._validate_file_path(filepath)
                        if path_error:
                            file_write_outputs.append(f"--- Error writing {filepath}: {path_error} ---")
                        else:
                            file_write_outputs.append(
                                self._handle_write_file(
                                    filepath, shell_commands,
                                    provenance_tracker=context.provenance_tracker,
                                )
                        )
                    else:
                        hack_match = re.match(r'^hack\(\s*["\']?(.+?)["\']?\s*\)$', stripped)
                        if hack_match:
                            custom_cmd = hack_match.group(1).strip()
                            file_read_outputs.append(
                                f"--- Note: custom command accepted (not executed as shell): {custom_cmd} ---"
                            )
                            continue
                        shell_commands.append(cmd)

            collected_output = "\n\n".join(str_replace_results + file_read_outputs + file_write_outputs)

            if not shell_commands and not collected_output:
                self.logger.error("Phase 3: No valid commands, read_file/write_file actions, or str_replace blocks found")
                return False

            if shell_commands:
                self.logger.info(f"Phase 3: Executing {len(shell_commands)} shell commands in batch")

                provenance_metadata = {}
                if context.provenance_tracker:
                    trace_id = context.provenance_tracker.start_trace(
                        phase="phase3_execution",
                        model=getattr(self.model_runner, 'model', None),
                        provider=getattr(self.model_runner, 'provider', None),
                    )
                    context.metadata["phase3_trace_id"] = trace_id
                    for cmd in shell_commands:
                        annotated = context.provenance_tracker.annotate_command(cmd, trace_id)
                        provenance_metadata[cmd[:60]] = annotated.get("provenance", {})

                result = self.terminal_history.execute_commands_batch(
                    shell_commands,
                    timeout=self.command_timeout,
                    cancel_event=context.cancel_event
                )
                self._raise_if_cancelled(context)

                result["provenance"] = provenance_metadata

                if context.repository_index:
                    changed_files = []
                    for cmd in shell_commands:
                        write_match = re.match(r'^\s*(write_file|cat.*>|echo.*>>|cp|mv|sed -i)\s', cmd)
                        if write_match:
                            file_paths = re.findall(r'[\w./\\]+\.\w+', cmd)
                            changed_files.extend(file_paths)
                    if changed_files:
                        updated = context.repository_index.delta_refresh(changed_files)
                        if updated:
                            self.logger.debug(f"Index refreshed for {updated} changed file(s)")

                # Classify failure if command failed
                if not result.get("success"):
                    from ..utils.exceptions import CommandFailureClassifier
                    failure_classification = CommandFailureClassifier.classify(
                        stderr=result.get("stderr", ""),
                        stdout=result.get("stdout", ""),
                        return_code=result.get("return_code", -1),
                        command="\n".join(shell_commands),
                    )
                    result["failure_classification"] = failure_classification
                    self.logger.info(
                        f"Command failure classified as: {failure_classification.category.value}",
                        reason=failure_classification.reason,
                        suggestion=failure_classification.suggestion,
                    )

                if collected_output:
                    existing_stdout = result.get("stdout", "")
                    result["stdout"] = (
                        collected_output + "\n\n" + existing_stdout
                    ) if existing_stdout else collected_output
            else:
                # Only native actions, no shell commands
                result = {
                    "success": True,
                    "stdout": collected_output,
                    "stderr": "",
                    "return_code": 0,
                }

            # Store execution result for Phase 4
            context.last_execution_result = result

            if result.get("success"):
                self.logger.info("Phase 3: Batch execution succeeded")
            else:
                self.logger.warning(f"Phase 3: Batch execution had issues: {result.get('stderr', 'Unknown')}")
                stderr = result.get('stderr', '')
                if 'timed out' in stderr.lower() and context.telegram_mode and self.telegram_bot and context.telegram_user_id:
                    try:
                        self._send_telegram_message_sync(
                            context.telegram_user_id,
                            f"Timeout Error\n\nCommand execution timed out after {self.command_timeout} seconds."
                        )
                    except PipelineCancelledError:
                        raise
                    except Exception as e:
                        self.logger.warning(f"Failed to send timeout notification to Telegram: {e}")

            context.terminal_log = self.terminal_history.display_terminal_log(max_entries=1000)

            self.logger.info("Phase 3 completed successfully")
            return True

        except PipelineCancelledError:
            raise
        except Exception as e:
            self.logger.error(f"Phase 3 failed: {e}")
            return False

    def _handle_write_file(self, filepath: str, commands_after: List[str],
                            provenance_tracker: Optional[ProvenanceTracker] = None) -> str:
        """Handle write_file(path) action with diff-based content extraction.

        The content to write is expected in subsequent command lines after the
        write_file(path) declaration. If the file already exists, the content
        is compared and only the differences are applied. If it does not exist,
        the file is created with the specified content.

        Args:
            filepath: Path to the file to write
            commands_after: List of subsequent command lines (consumed for content)
            provenance_tracker: Optional tracker for provenance metadata

        Returns:
            A string describing what was done
        """
        # Collect content lines until next action declaration or end
        content_lines = []
        while commands_after:
            next_line = commands_after[0].strip()
            # Stop at next action declaration
            if re.match(r'^(read_file|write_file|str_replace|keep_text|keep_file|hack)\(', next_line):
                break
            content_lines.append(commands_after.pop(0))
        content = "\n".join(content_lines)

        if not content and not content_lines:
            return f"--- No content provided for {filepath}, skipping ---"

        trace_id = ""
        if provenance_tracker:
            trace_id = provenance_tracker.start_trace(phase="phase3_write_file")

        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    existing = f.read()

                if existing == content:
                    return f"--- {filepath} unchanged (content is identical) ---"

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

                old_lines = existing.count('\n') + 1
                new_lines = content.count('\n') + 1

                if provenance_tracker and trace_id:
                    provenance_tracker.record(
                        trace_id, phase="phase3_write_file",
                        confidence=1.0,
                        metadata={"filepath": filepath, "old_lines": old_lines, "new_lines": new_lines},
                    )

                return (
                    f"--- write_file applied to {filepath} ---\n"
                    f"File existed ({old_lines} lines). "
                    f"Updated to {new_lines} lines (diff-based write)."
                )
            else:
                parent_dir = os.path.dirname(filepath)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                lines = content.count('\n') + 1

                if provenance_tracker and trace_id:
                    provenance_tracker.record(
                        trace_id, phase="phase3_write_file",
                        confidence=1.0,
                        metadata={"filepath": filepath, "new_lines": lines, "created": True},
                    )

                return f"--- write_file created {filepath} ({lines} lines) ---"
        except Exception as e:
            return f"--- Error writing to {filepath}: {e} ---"


    def _handle_search(self, pattern: str, path: str, max_results: int = 100) -> str:
        """Search file contents under `path` for `pattern` (read-only, case-insensitive)."""
        try:
            base = Path(path)
            if not base.is_absolute():
                base = Path(os.getcwd()) / base
            base = base.resolve()
            if not base.exists():
                return f"--- Error searching '{path}': path does not exist ---"

            targets = [base] if base.is_file() else [p for p in base.rglob("*") if p.is_file()]
            matches = []
            for fpath in targets:
                try:
                    if not os.access(fpath, os.R_OK):
                        continue
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        for lineno, line in enumerate(f, 1):
                            if pattern.lower() in line.lower():
                                try:
                                    display = fpath.relative_to(base)
                                except ValueError:
                                    display = fpath
                                matches.append(f"{display}:{lineno}: {line.rstrip()}")
                                if len(matches) >= max_results:
                                    break
                except (OSError, UnicodeDecodeError):
                    continue
                if len(matches) >= max_results:
                    break

            if not matches:
                return f"--- search('{pattern}', '{path}'): no matches found ---"
            header = f"--- search('{pattern}', '{path}'): {len(matches)} match(es) ---"
            return header + "\n" + "\n".join(matches)
        except Exception as e:
            return f"--- Error searching '{path}': {e} ---"

    def _handle_list_files(self, path: str, recursive: bool = False) -> str:
        """List files and directories under `path` (read-only exploration)."""
        try:
            base = Path(path)
            if not base.is_absolute():
                base = Path(os.getcwd()) / base
            base = base.resolve()
            if not base.exists():
                return f"--- Error listing '{path}': path does not exist ---"
            if base.is_file():
                return f"--- list_files('{path}'): is a file ({base.stat().st_size} bytes) ---"

            if recursive:
                entries = []
                for p in sorted(base.rglob("*")):
                    depth = len(p.relative_to(base).parts)
                    kind = "d" if p.is_dir() else "f"
                    entries.append(f"{'  ' * depth}{kind} {p.relative_to(base)}")
            else:
                entries = []
                for p in sorted(base.iterdir()):
                    kind = "d" if p.is_dir() else "f"
                    entries.append(f"{kind} {p.name}")

            if not entries:
                return f"--- list_files('{path}'): directory is empty ---"
            word = "y" if len(entries) == 1 else "ies"
            header = f"--- list_files('{path}'): {len(entries)} entr{word} ---"
            return header + "\n" + "\n".join(entries)
        except Exception as e:
            return f"--- Error listing '{path}': {e} ---"
    def _run_phase4(self, context: PipelineContext) -> bool:
        """
        Phase 4: Dynamic Update & Progress Reporting (Most Critical Phase)

        Send execution logs and current state to the LLM to evaluate results
        and determine the future step list. The LLM must output VEXIS commands:

        1. Summary_of_Progress [...] - Mandatory every step. Reports what was done
           and the result from the AI's first-person perspective.
        2. step_list [...] - Overwrites the entire unexecuted (future) step list.
           On failure, add recovery steps. On success, delete completed steps.

        First-Person Perspective: The prompt explicitly states that the AI agent
        executed the command and is receiving the result. The AI must use "I".

        Past Protection: Only future steps can be rewritten. The current step
        is moved to completed_steps before the LLM evaluation.

        State Transition: If step_list is empty after update, the task is complete
        and the loop transitions to Phase 5.
        """
        self.logger.info("Phase 4: Dynamic Update & Progress Reporting started")
        context.current_phase = PipelinePhase.PHASE4_DYNAMIC_UPDATE

        try:
            # Move current step to completed before evaluation
            if context.step_list:
                current_step = context.step_list.pop(0)
                context.completed_steps.append(current_step)

            full_terminal_log = self._truncate_text(
                self.terminal_history.display_terminal_log(max_entries=1000),
                max_chars=4000, label="terminal_log"
            )
            if context.compressed_context:
                full_terminal_log = (
                    "[COMPRESSED EXECUTION HISTORY - Earlier iterations summarized]\n"
                    f"{context.compressed_context}\n\n"
                    "[RECENT TERMINAL LOG - Most recent commands and outputs]\n"
                    f"{full_terminal_log}"
                )
                full_terminal_log = self._truncate_text(
                    full_terminal_log, max_chars=5000, label="compressed_terminal_log"
                )

            # Build execution log for the LLM
            exec_result = context.last_execution_result or {}
            stdout = self._truncate_text(exec_result.get("stdout", ""), max_chars=2000, label="stdout")
            stderr = self._truncate_text(exec_result.get("stderr", ""), max_chars=2000, label="stderr")
            return_code = exec_result.get("return_code", -1)

            execution_log = f"Command executed: {context.extracted_commands}\n"
            execution_log += f"Return code: {return_code}\n"
            if stdout:
                execution_log += f"Standard output:\n{stdout}\n"
            if stderr:
                execution_log += f"Standard error:\n{stderr}\n"

            # Include failure classification if available
            failure_classification = exec_result.get("failure_classification")
            if failure_classification:
                execution_log += (
                    f"\nFailure Classification:\n"
                    f"Category: {failure_classification.category.value}\n"
                    f"Reason: {failure_classification.reason}\n"
                    f"Suggestion: {failure_classification.suggestion}\n"
                    f"Retry allowed: {failure_classification.retry_allowed}\n"
                )

            completed_steps_text = "\n".join(
                f"{i+1}. {step}" for i, step in enumerate(context.completed_steps)
            ) if context.completed_steps else "None yet"

            remaining_steps_text = "\n".join(
                f"{i+1}. {step}" for i, step in enumerate(context.step_list)
            ) if context.step_list else "None (task may be complete)"

            request = ModelRequest(
                task_type=TaskType.PHASE4_DYNAMIC_UPDATE,
                prompt=execution_log,
                context={
                    "user_prompt": context.user_prompt,
                    "execution_log": execution_log,
                    "completed_steps": completed_steps_text,
                    "remaining_steps": remaining_steps_text,
                    "full_terminal_log": full_terminal_log,
                },
                max_tokens=4000,
                temperature=0.5
            )

            response = self.model_runner.run_model(request)
            self._raise_if_cancelled(context)

            if not response.success:
                self.logger.error(
                    f"Phase 4 model execution failed: {response.error}",
                    content_preview=(response.content or "")[:300],
                )

            context.phase4_output = response.content or ""

            # Parse VEXIS commands from the response (even partial/non-success content)
            parsed = self._parse_vexis_commands(context.phase4_output)

            # Handle Summary_of_Progress (mandatory every step)
            progress_summary = parsed.get("summary", "")
            if progress_summary:
                context.progress_summaries.append(progress_summary)
                self.logger.info(f"Phase 4: Progress summary: {progress_summary[:100]}...")

                # Route to terminal or Telegram based on mode
                if context.telegram_mode and self.telegram_bot and context.telegram_user_id:
                    try:
                        self._send_telegram_message_sync(
                            context.telegram_user_id,
                            f"Progress: {progress_summary}"
                        )
                    except PipelineCancelledError:
                        raise
                    except Exception as e:
                        self.logger.warning(f"Failed to send progress summary to Telegram: {e}")
                else:
                    print(f"\nProgress: {progress_summary}")
            else:
                self.logger.warning("Phase 4: No Summary_of_Progress found in LLM output")

            # Handle step_list update (overwrites future steps)
            if parsed.get("step_list") is not None:
                new_steps = parsed["step_list"]
                context.step_list = new_steps
                self.logger.info(f"Phase 4: Step list updated to {len(new_steps)} steps")
            elif not response.success:
                self.logger.warning("Phase 4: Model failed and no step_list found — keeping existing step_list")
            else:
                self.logger.warning("Phase 4: No step_list found in LLM output, keeping existing step list")

            # Even if the model technically failed (validation error), if we have
            # usable content, treat Phase 4 as a partial success rather than a hard failure.
            if not response.success and not context.phase4_output.strip():
                return False

            # FALLBACK RECOVERY: If no step_list was explicitly provided by the LLM
            # and execution failed with "command not found" or "permission denied",
            # automatically inject an installation step.
            if "step_list" not in parsed and not context.step_list:
                exec_result = context.last_execution_result or {}
                if exec_result.get("success") is False:
                    stderr = exec_result.get("stderr", "").lower()
                    if "command not found" in stderr or "permission denied" in stderr:
                        # Try to detect the missing command/package from error message
                        # Patterns: 'command', "command", or command: command not found
                        match = re.search(r"'([^']+)'|\"([^\"]+)\"|(\S+): command not found", stderr)
                        if match:
                            missing_cmd = match.group(1) or match.group(2) or match.group(3)
                        else:
                            missing_cmd = "python3"  # default guess
                        
                        # Determine appropriate package manager based on OS
                        os_info = context.metadata.get("os_info", "").lower()
                        if "debian" in os_info or "ubuntu" in os_info or "linux" in os_info:
                            install_step = f"apt-get update && apt-get install -y {missing_cmd}"
                        elif "darwin" in os_info or "macos" in os_info:  # macOS
                            install_step = f"brew install {missing_cmd}"
                        elif "red hat" in os_info or "centos" in os_info or "fedora" in os_info:
                            install_step = f"yum install -y {missing_cmd}"
                        else:
                            install_step = f"echo 'Unknown OS, attempting apt...'; apt-get update && apt-get install -y {missing_cmd}"
                        
                        context.step_list = [install_step]
                        self.logger.warning(
                            "Phase 4: Automatic recovery triggered - added installation step for missing package",
                            missing_command=missing_cmd,
                            install_step=install_step
                        )

            self.logger.info("Phase 4 completed",
                           steps_remaining=len(context.step_list),
                           output_length=len(context.phase4_output))

            return True

        except PipelineCancelledError:
            raise
        except Exception as e:
            self.logger.error(f"Phase 4 failed: {e}")
            return False

    def _compress_context(self, context: PipelineContext) -> None:
        """
        Compress accumulated pipeline context data (terminal log, progress summaries,
        completed steps) at iteration intervals. This prevents unbounded context growth
        by condensing the execution history while preserving all semantically important
        information needed to continue the task.

        Triggered every time iteration_count reaches a multiple of 10.
        """
        self.logger.info(
            f"Compressing accumulated context at iteration {context.iteration_count}"
        )

        terminal_log = self.terminal_history.display_terminal_log(max_entries=1000)

        completed_steps_text = "\n".join(
            f"{i+1}. {step}" for i, step in enumerate(context.completed_steps)
        ) if context.completed_steps else "None yet"

        progress_text = "\n".join(
            f"- {s}" for s in context.progress_summaries
        ) if context.progress_summaries else "No progress recorded"

        kept_text_section = ""
        if context.kept_text_records:
            entries = "\n".join(
                f"  [{i+1}] {entry}" for i, entry in enumerate(context.kept_text_records)
            )
            kept_text_section = f"\n\n## Kept Text Records (DO NOT SUMMARIZE OR COMPRESS)\n{entries}"

        kept_file_section = ""
        if context.kept_file_records:
            entries = "\n".join(
                f"  [{path}] ({len(content)} chars)"
                for path, content in context.kept_file_records.items()
            )
            kept_file_section = f"\n\n## Kept File Records (DO NOT SUMMARIZE OR COMPRESS)\n{entries}"

        context_to_compress = (
            f"# Pipeline Execution Context\n\n"
            f"## Terminal Log\n{terminal_log}\n\n"
            f"## Completed Steps\n{completed_steps_text}\n\n"
            f"## Progress Summaries\n{progress_text}"
            f"{kept_text_section}"
            f"{kept_file_section}"
        )

        compressed = self.model_runner.compress_context_data(context_to_compress)
        if compressed and len(compressed.strip()) > 50 and compressed != context_to_compress:
            original_len = len(context_to_compress)
            compressed_len = len(compressed)

            preserved_sections = ""
            if context.kept_text_records:
                entries = "\n".join(
                    f"  [{i+1}] {entry}" for i, entry in enumerate(context.kept_text_records)
                )
                preserved_sections += f"\n\n## Kept Text Records (PRESERVED — DO NOT SUMMARIZE OR COMPRESS)\n{entries}"
            if context.kept_file_records:
                entries = "\n".join(
                    f"  [{path}]\n{content}"
                    for path, content in context.kept_file_records.items()
                )
                preserved_sections += f"\n\n## Kept File Records (PRESERVED — DO NOT SUMMARIZE OR COMPRESS)\n{entries}"

            context.compressed_context = compressed + preserved_sections
            self.logger.info(
                "Context compressed successfully",
                original_chars=original_len,
                compressed_chars=compressed_len,
                reduction_percent=round((1 - compressed_len / original_len) * 100, 1),
                kept_text_entries=len(context.kept_text_records),
                kept_file_entries=len(context.kept_file_records),
            )
        else:
            self.logger.warning("Context compression produced no usable reduction, keeping original context")

    def _run_phase5(self, context: PipelineContext) -> bool:
        """
        Phase 5: Verification

        Send execution logs and user prompt to the LLM to verify whether the
        execution was TRULY successful. The LLM analyzes the terminal output
        to detect hidden failures, partial successes, or silent errors.

        If the LLM finds issues, it outputs an original_command VEXIS command
        containing recovery steps. These steps are added to the step_list and
        execution loops back to Phase 2.

        If no original_command is output, the task is considered truly successful
        and proceeds to Phase 6 (Summarization).
        """
        self.logger.info("Phase 5: Verification started")
        context.current_phase = PipelinePhase.PHASE5_VERIFICATION

        max_retries = 3
        for attempt in range(max_retries):
            try:
                full_terminal_log = self._truncate_text(
                    self.terminal_history.display_terminal_log(max_entries=1000),
                    max_chars=4000, label="terminal_log"
                )

                completed_steps_text = "\n".join(
                    f"{i+1}. {step}" for i, step in enumerate(context.completed_steps)
                ) if context.completed_steps else "No steps were completed"

                progress_text = "\n".join(
                    f"- {s}" for s in context.progress_summaries
                ) if context.progress_summaries else "No progress summaries recorded"

                request = ModelRequest(
                    task_type=TaskType.PHASE5_VERIFICATION,
                    prompt=full_terminal_log,
                    context={
                        "user_prompt": context.user_prompt,
                        "full_terminal_log": full_terminal_log,
                        "completed_steps": completed_steps_text,
                        "progress_summaries": progress_text,
                    },
                    max_tokens=4000,
                    temperature=0.3
                )

                response = self.model_runner.run_model(request)
                self._raise_if_cancelled(context)

                if not response.success:
                    self.logger.error(f"Phase 5 model execution failed: {response.error}")
                    if attempt < max_retries - 1:
                        continue
                    return False

                context.phase4_output = response.content

                # Parse VEXIS commands from the response
                parsed = self._parse_vexis_commands(response.content)

                # Handle Summary_of_Progress (mandatory)
                progress_summary = parsed.get("summary", "")
                if progress_summary:
                    context.progress_summaries.append(progress_summary)
                    self.logger.info(f"Phase 5: Progress summary: {progress_summary[:100]}...")

                    if context.telegram_mode and self.telegram_bot and context.telegram_user_id:
                        try:
                            self._send_telegram_message_sync(
                                context.telegram_user_id,
                                f"Verification: {progress_summary}"
                            )
                        except PipelineCancelledError:
                            raise
                        except Exception as e:
                            self.logger.warning(f"Failed to send verification to Telegram: {e}")
                    else:
                        print(f"\nVerification: {progress_summary}")
                else:
                    self.logger.warning("Phase 5: No Summary_of_Progress found in LLM output")

                # Handle original_command - extends step list for re-execution
                if parsed.get("original_command") is not None:
                    original_steps = parsed["original_command"]
                    if original_steps:
                        context.step_list = original_steps + context.step_list
                        self.logger.info(
                            f"Phase 5: original_command found with {len(original_steps)} recovery steps. "
                            "Will return to Phase 2."
                        )
                    else:
                        self.logger.info("Phase 5: original_command is empty, no recovery needed")
                else:
                    self.logger.info("Phase 5: No original_command found, execution verified as successful")

                self.logger.info("Phase 5 completed",
                               has_original_command=parsed.get("original_command") is not None,
                               steps_in_list=len(context.step_list))

                return True

            except PipelineCancelledError:
                raise
            except Exception as e:
                self.logger.error(f"Phase 5 failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    continue
                return False

        return False

    def _run_phase6(self, context: PipelineContext) -> bool:
        """
        Phase 6: Summarization

        After verification confirms true success, create a final summary detailing
        how the task was executed and what the result was, based on the
        execution logs, user prompt, and the entire trajectory.
        """
        self.logger.info("Phase 6: Summarization started")
        context.current_phase = PipelinePhase.PHASE6_SUMMARIZATION

        max_retries = 3
        full_terminal_log = self._truncate_text(
            self.terminal_history.display_terminal_log(max_entries=1000),
            max_chars=4000, label="terminal_log"
        )

        completed_steps_text = "\n".join(
            f"{i+1}. {step}" for i, step in enumerate(context.completed_steps)
        ) if context.completed_steps else "No steps were completed"

        progress_text = "\n".join(
            f"- {s}" for s in context.progress_summaries
        ) if context.progress_summaries else "No progress summaries recorded"
        for attempt in range(max_retries):
            try:
                request = ModelRequest(
                    task_type=TaskType.PHASE6_SUMMARIZATION,
                    prompt=full_terminal_log,
                    context={
                        "user_prompt": context.user_prompt,
                        "full_terminal_log": full_terminal_log,
                        "completed_steps": completed_steps_text,
                        "progress_summaries": progress_text,
                    },
                    max_tokens=4000,
                    temperature=0.7
                )

                response = self.model_runner.run_model(request)
                self._raise_if_cancelled(context)

                if not response.success:
                    self.logger.error(f"Phase 6 model execution failed: {response.error}")
                    if attempt < max_retries - 1:
                        continue

                    self.logger.warning(
                        "Phase 6: using deterministic fallback summary after repeated model failures",
                        error=response.error,
                    )
                    context.final_summary = self._build_fallback_summary(context)
                    return True

                summary = response.content.strip()
                summary = self._remove_code_blocks(summary)

                if not summary:
                    summary = "Task completed successfully. The objective was achieved through the executed steps."
                    self.logger.warning("Phase 6: LLM returned only code blocks, using fallback summary")

                context.final_summary = summary
                self.logger.info("Phase 6 completed successfully",
                               summary_length=len(summary))

                return True

            except PipelineCancelledError:
                raise
            except Exception as e:
                self.logger.error(f"Phase 6 failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    continue
                self.logger.warning(
                    "Phase 6: exception fallback activated, creating deterministic summary",
                    error=str(e),
                )
                context.final_summary = self._build_fallback_summary(context)
                return True

        context.final_summary = self._build_fallback_summary(context)
        return True

    def _run_bot_user_review(self, context: PipelineContext) -> bool:
        """
        Bot User Phase: Review conversation between AI agent and user

        The Bot User (large language model) reviews the conversation to determine
        whether the agent's final output properly fulfills the user's intended task
        and whether there are any failures or deviations from the intended direction.

        The evaluation result:
        - "Well, I guess this is fine.": Output is flawless → proceed to completion
        - Otherwise, correction guidance is extracted and fed back into the
          pipeline as new user prompts

        Design choices:
        - Even on LLM failure, the pipeline continues (returns True) so the user
          still gets their result rather than a hard error
        - The Bot User has no persistent state of its own—each review is stateless
          and based solely on the provided conversation artifacts
        """
        self.logger.info("Bot User Phase: Review started")
        context.current_phase = PipelinePhase.BOT_USER_REVIEW

        try:
            full_terminal_log = self._truncate_text(
                self.terminal_history.display_terminal_log(max_entries=1000),
                max_chars=4000, label="terminal_log"
            )

            completed_steps_text = "\n".join(
                f"{i+1}. {step}" for i, step in enumerate(context.completed_steps)
            ) if context.completed_steps else "No steps were completed"

            final_output = context.final_summary or "No final output was generated"

            request = ModelRequest(
                task_type=TaskType.BOT_USER_REVIEW,
                prompt=full_terminal_log,
                context={
                    "user_prompt": context.user_prompt,
                    "final_output": final_output,
                    "completed_steps": completed_steps_text,
                    "execution_log": full_terminal_log,
                },
                max_tokens=4000,
                temperature=0.3
            )

            response = self.model_runner.run_model(request)
            self._raise_if_cancelled(context)

            # If the LLM call itself fails, don't block the user's result
            if not response.success:
                self.logger.warning(f"Bot User review model execution failed: {response.error}")
                return True

            review_output = response.content.strip()
            context.bot_user_review_output = review_output

            # Required acceptance phrase means no corrective action needed
            if review_output.startswith("Well, I guess this is fine."):
                self.logger.info("Bot User review: Output deemed acceptable")
                return True

            # Any code block in the response is treated as corrective instructions
            # to be fed back into the pipeline
            instructions = self._extract_code_block(review_output)
            if instructions:
                context.bot_user_instructions = instructions
                self.logger.info("Bot User review: Found correction instructions",
                               instructions_length=len(instructions))
            else:
                # Non-acceptance free text is also treated as correction feedback
                context.bot_user_instructions = review_output
                self.logger.info(
                    "Bot User review: Treating free-text feedback as correction instructions",
                    instructions_length=len(review_output),
                )

            return True

        except PipelineCancelledError:
            raise
        except Exception as e:
            # Never let a review failure prevent the user from seeing results
            self.logger.error(f"Bot User review failed: {e}")
            return True

    def _build_fallback_summary(self, context: PipelineContext) -> str:
        """Create a deterministic summary when LLM summarization is unavailable."""
        objective = context.user_prompt.strip() or "the requested task"
        completed_count = len(context.completed_steps)
        progress_count = len(context.progress_summaries)

        summary_parts = [
            f"The task was to {objective}.",
            f"Execution completed {completed_count} planned step(s) through the pipeline."
        ]

        if context.completed_steps:
            preview_steps = context.completed_steps[:3]
            summary_parts.append(
                "Key completed steps included: " + "; ".join(preview_steps) + "."
            )

        if context.progress_summaries:
            summary_parts.append(
                f"I recorded {progress_count} progress update(s) during execution and used them to verify outcomes."
            )

        if context.step_list:
            summary_parts.append(
                f"There are {len(context.step_list)} remaining step(s) flagged for follow-up or additional verification."
            )
        else:
            summary_parts.append("No remaining steps were left in the active execution queue.")

        summary_parts.append(
            "This summary was generated by a reliability fallback because the AI summarization phase was unavailable."
        )

        return " ".join(summary_parts)

    def _emit_final_summary(self, context: PipelineContext) -> None:
        """Emit final summary to Telegram or stdout."""
        if context.telegram_mode and self.telegram_bot and context.telegram_user_id:
            self._send_telegram_message_sync(
                context.telegram_user_id,
                f"Task Completed\n\n{context.final_summary}"
            )
        else:
            print("")
            print(context.final_summary)

    def _run_immediate_response(self, context: PipelineContext) -> bool:
        """
        Generate a direct response when action_type is answer_directly.
        This skips P2-P5 entirely and produces the final output immediately.
        """
        self.logger.info("Phase 6: Generating immediate response (gate: answer_directly)")
        context.current_phase = PipelinePhase.PHASE6_SUMMARIZATION

        try:
            parsed = self._parse_vexis_commands(context.phase1_output or "")

            direct_answer = parsed.get("answer", "")
            progress_summary = parsed.get("summary", "")

            if direct_answer:
                context.final_summary = direct_answer
                context.progress_summaries.append(progress_summary or direct_answer)
                self.logger.info("Immediate response: using direct answer from LLM")
            elif progress_summary:
                context.final_summary = progress_summary
                context.progress_summaries.append(progress_summary)
                self.logger.info("Immediate response: using progress summary from LLM")
            else:
                query = context.user_prompt.strip()
                context.final_summary = (
                    f"Regarding your request: '{query}'\n\n"
                    "This task was classified as a direct-answer request "
                    "and no commands needed to be executed."
                )
                self.logger.warning("Immediate response: no answer or summary found in LLM output, using fallback")

            self.logger.info("Immediate response completed",
                           summary_length=len(context.final_summary))
            return True

        except Exception as e:
            self.logger.error(f"Immediate response generation failed: {e}")
            query = context.user_prompt.strip()
            context.final_summary = (
                f"Regarding your request: '{query}'\n\n"
                "This was handled as a direct answer with no command execution needed."
            )
            return True

    def _parse_vexis_commands(self, text: str) -> Dict[str, Any]:
        """
        Parse VEXIS commands from LLM output.

        VEXIS Commands:
        1. action_type [type] - The action type the LLM selected
        2. question [content] - The question to ask the user (when action_type is ask_user)
        3. answer [content] - Direct answer content (when action_type is answer_directly)
        4. keep_text("content") - Text to store in memory records (when action_type is keep_text)
        5. keep_file("/path") - File path to store in memory records (when action_type is keep_file)
        6. Summary_of_Progress [...] - Reports what was done and the result
        7. step_list [...] - Overwrites the entire unexecuted (future) step list
        8. original_command [...] - Extends the step list with recovery steps (Phase 5)
        9. tasks [...] - DAG-based task list with id, action, and waiting_for

        Args:
            text: LLM output text

        Returns:
            Dict with keys 'action_type' (str or None), 'question' (str or None),
            'answer' (str or None), 'keep_text' (str or None), 'keep_file' (str or None),
            'summary' (str), 'step_list' (List[str] or None),
            'original_command' (List[str] or None), and 'tasks' (List[Dict] or None)
        """
        result: Dict[str, Any] = {}

        if not text:
            return result

        # Parse action_type [type]
        action_match = re.search(
            r'action_type\s*\[(.*?)\]',
            text,
            re.DOTALL
        )
        if action_match:
            action_type_str = action_match.group(1).strip().lower()
            result["action_type"] = action_type_str

        # Parse question [content] (for ask_user action type)
        question_match = re.search(
            r'question\s*\[(.*?)\]',
            text,
            re.DOTALL
        )
        if question_match:
            result["question"] = question_match.group(1).strip()

        # Parse answer [content] (for answer_directly action type)
        answer_match = re.search(
            r'answer\s*\[(.*?)\]',
            text,
            re.DOTALL
        )
        if answer_match:
            result["answer"] = answer_match.group(1).strip()

        # Parse keep_text("content") (for keep_text action type)
        # Use greedy (.+) with the final quote as anchor to handle quotes inside content
        keep_text_match = re.search(
            r'keep_text\(\s*["\'](.+)["\']\s*\)',
            text,
            re.DOTALL
        )
        if keep_text_match:
            result["keep_text"] = keep_text_match.group(1)

        # Parse keep_file("/path") (for keep_file action type)
        # Use greedy (.+) with the final quote as anchor for consistent path parsing
        keep_file_match = re.search(
            r'keep_file\(\s*["\'](.+)["\']\s*\)',
            text,
            re.DOTALL
        )
        if keep_file_match:
            result["keep_file"] = keep_file_match.group(1)

        # Parse Summary_of_Progress [content]
        progress_match = re.search(
            r'Summary_of_Progress\s*\[(.*?)\]',
            text,
            re.DOTALL
        )
        if progress_match:
            summary = progress_match.group(1).strip()
            result["summary"] = summary

        # Parse step_list [content]
        steps_match = re.search(
            r'step_list\s*\[(.*?)\]',
            text,
            re.DOTALL
        )
        if steps_match:
            steps_text = steps_match.group(1).strip()
            steps = []
            for line in steps_text.split('\n'):
                line = line.strip()
                if line:
                    cleaned = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                    if cleaned:
                        steps.append(cleaned)
            result["step_list"] = steps

        # Parse original_command [content] (Phase 5 verification recovery)
        original_match = re.search(
            r'original_command\s*\[(.*?)\]',
            text,
            re.DOTALL
        )
        if original_match:
            original_text = original_match.group(1).strip()
            original_steps = []
            for line in original_text.split('\n'):
                line = line.strip()
                if line:
                    cleaned = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                    if cleaned:
                        original_steps.append(cleaned)
            result["original_command"] = original_steps

        # Parse tasks [content] - DAG-based task list
        # Use a more robust approach to find the tasks block
        text_lower_for_tasks = text.lower()
        tasks_idx = text_lower_for_tasks.find('tasks')
        if tasks_idx >= 0:
            # Skip past "tasks" and then past the opening bracket
            after_keyword = text[tasks_idx + 5:]
            bracket_start = after_keyword.find('[')
            if bracket_start >= 0:
                start_pos = tasks_idx + 5 + bracket_start + 1
                bracket_count = 1
                pos = start_pos
                while pos < len(text) and bracket_count > 0:
                    if text[pos] == '[':
                        bracket_count += 1
                    elif text[pos] == ']':
                        bracket_count -= 1
                    pos += 1
                if bracket_count == 0:
                    tasks_text = text[start_pos:pos-1].strip()
                    tasks = self._parse_task_list(tasks_text)
                    if tasks:
                        result["tasks"] = tasks

        return result

    def _parse_task_list(self, tasks_text: str) -> List[Dict[str, Any]]:
        """
        Parse a task list text into a list of task dictionaries.
        
        Expected format per task (JSON):
        {"id": "task_1", "action": "First step", "waiting_for": []}
        
        Expected format per task (key-value):
        id: task_1
        action: First step
        waiting_for: []
        
        Args:
            tasks_text: Text containing task definitions
            
        Returns:
            List of task dictionaries with 'id', 'action', and 'waiting_for' keys
        """
        tasks = []
        
        # Try to parse as JSON first
        try:
            import json
            # Clean up the text - remove extra whitespace
            cleaned_text = tasks_text.strip()
            if not cleaned_text.startswith('['):
                cleaned_text = f"[{cleaned_text}]"
            parsed = json.loads(cleaned_text)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and 'id' in item and 'action' in item:
                        task = {
                            'id': str(item['id']),
                            'action': str(item['action']),
                            'waiting_for': [str(x) for x in item.get('waiting_for', [])]
                        }
                        tasks.append(task)
                if tasks:
                    return tasks
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Fallback: Parse line by line
        # Format: "id: task1\naction: do something\nwaiting_for: []\n"
        current_task = {}
        for line in tasks_text.split('\n'):
            line = line.strip()
            if not line:
                if current_task and 'id' in current_task and 'action' in current_task:
                    if 'waiting_for' not in current_task:
                        current_task['waiting_for'] = []
                    tasks.append(current_task)
                    current_task = {}
                continue
            
            # Try to parse key: value format
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key == 'id':
                    if current_task and 'id' in current_task and 'action' in current_task:
                        if 'waiting_for' not in current_task:
                            current_task['waiting_for'] = []
                        tasks.append(current_task)
                        current_task = {}
                    current_task['id'] = value
                elif key == 'action':
                    current_task['action'] = value
                elif key == 'waiting_for':
                    # Parse array format: [id1, id2] or []
                    waiting = []
                    if value.startswith('[') and value.endswith(']'):
                        inner = value[1:-1].strip()
                        if inner:
                            waiting = [x.strip().strip("'\"") for x in inner.split(',')]
                    current_task['waiting_for'] = waiting
        
        # Don't forget the last task
        if current_task and 'id' in current_task and 'action' in current_task:
            if 'waiting_for' not in current_task:
                current_task['waiting_for'] = []
            tasks.append(current_task)
        
        return tasks

    def _send_telegram_message_sync(self, user_id: int, message: str):
        self.logger.info(f"Queueing Telegram message to user {user_id}")
        self.telegram_bot.queue_message(user_id, message)
        self.logger.info(f"Message queued successfully for user {user_id}")

    def _send_phase_error_telegram(self, context: PipelineContext, phase_num: str, phase_name: str):
        if context.telegram_mode and self.telegram_bot and context.telegram_user_id:
            try:
                self._send_telegram_message_sync(
                    context.telegram_user_id,
                    f"Phase {phase_num} Failed\n\n{phase_name} phase failed.\n\nError: {context.error}"
                )
                self.logger.info(f"Sent Phase {phase_num} failure notification to Telegram")
            except Exception as e:
                self.logger.warning(f"Failed to send Phase {phase_num} failure notification: {e}")

    def _send_timeout_telegram(self, context: PipelineContext, elapsed: float):
        if context.telegram_mode and self.telegram_bot and context.telegram_user_id:
            try:
                self._send_telegram_message_sync(
                    context.telegram_user_id,
                    f"Task Timeout\n\nThe task exceeded the maximum execution time.\n\nElapsed: {elapsed:.1f}s\nLimit: {self.task_timeout}s"
                )
            except Exception as e:
                self.logger.warning(f"Failed to send timeout notification: {e}")

    def _extract_code_block(self, text: str) -> Optional[str]:
        """
        Extract code block from text in any supported format.
        If multiple code blocks are present, use the last one.
        Supports Markdown (```), XML (<code>), BBCode ([code]),
        custom delimiter (---code---), and HTML (<pre><code>) formats.

        Args:
            text: Text containing code blocks

        Returns:
            Extracted code block content or None if not found
        """
        return _multi_format_extract(text)

    def _has_code_block(self, text: str) -> bool:
        """Check if text contains a code block in any supported format"""
        return _multi_format_has(text)

    def _remove_code_blocks(self, text: str) -> str:
        """Remove code blocks in any supported format from text, keeping only plain text."""
        return _multi_format_remove(text)

    def _parse_commands(self, code_block: str) -> List[str]:
        """
        Parse commands from a code block (programmatic, zero LLM).

        Args:
            code_block: Code block content

        Returns:
            List of individual commands
        """
        commands = []
        lines = code_block.split('\n')

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('```'):
                continue

            vexis_match = re.match(
                r'^(SHELL|READ_FILE|WRITE_FILE|KEEP_TEXT|KEEP_FILE|STR_REPLACE|HACK|SEARCH|LIST_FILES)\s*:\s*(.+)$',
                line,
                re.IGNORECASE
            )
            if vexis_match:
                command_type = vexis_match.group(1).upper()
                payload = vexis_match.group(2).strip()
                if command_type == "SHELL":
                    commands.append(payload)
                elif command_type == "READ_FILE":
                    commands.append(f'read_file("{payload}")')
                elif command_type == "WRITE_FILE":
                    commands.append(f'write_file("{payload}")')
                elif command_type == "KEEP_TEXT":
                    safe_payload = payload.replace("'", "\\'")
                    commands.append(f"keep_text('{safe_payload}')")
                elif command_type == "KEEP_FILE":
                    safe_payload = payload.replace("'", "\\'")
                    commands.append(f"keep_file('{safe_payload}')")
                elif command_type == "STR_REPLACE":
                    commands.append(payload)
                elif command_type == "HACK":
                    commands.append(f'hack("{payload}")')
                elif command_type == "SEARCH":
                    safe_payload = payload.replace("'", "\\'")
                    commands.append(f"search('{safe_payload}')")
                elif command_type == "LIST_FILES":
                    safe_payload = payload.replace("'", "\\'")
                    commands.append(f"list_files('{safe_payload}')")
                continue

            commands.append(line)

        return commands

    def cleanup(self):
        pass

    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass

    @staticmethod
    def _truncate_text(text: str, max_chars: int = 4000, label: str = "content") -> str:
        """Truncate text to max_chars, keeping head and tail for context.

        This prevents prompt context window overflow when sending large
        terminal logs or command outputs to the LLM.
        """
        if not text or len(text) <= max_chars:
            return text
        half = max_chars // 2
        head = text[:half]
        tail = text[-(half):]
        truncated = len(text) - max_chars
        return (
            f"{head}\n\n... [{label.upper()} TRUNCATED: {truncated} chars removed] ...\n\n{tail}"
        )

    def _get_os_info(self) -> str:
        """Get OS information for CLI context"""
        try:
            system = platform.system()
            release = platform.release()
            version = platform.version()
            machine = platform.machine()
            shell = os.environ.get('SHELL', 'Unknown')

            if system == "Linux":
                try:
                    with open('/etc/os-release', 'r') as f:
                        lines = f.readlines()
                    distro_info = {}
                    for line in lines:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            distro_info[key] = value.strip('"')
                    distro_name = distro_info.get('NAME', 'Unknown Linux')
                    distro_version = distro_info.get('VERSION', '')
                    os_info = f"{distro_name} {distro_version} ({system} {release} {machine})"
                except (FileNotFoundError, KeyError, ValueError):
                    os_info = f"Linux {release} {machine}"
            elif system == "Darwin":
                os_info = f"macOS {release} {machine}"
            elif system == "Windows":
                os_info = f"Windows {release} {machine}"
            else:
                os_info = f"{system} {release} {machine}"

            if system in ["Linux", "Darwin"]:
                os_info += f" (Shell: {shell})"

            return os_info
        except Exception as e:
            self.logger.warning(f"Failed to get OS info: {e}")
            return "Unknown OS"

    @staticmethod
    def _is_coding_task(step: str, user_prompt: str) -> bool:
        coding_keywords = [
            "write", "edit", "create", "modify", "implement", "add", "update",
            "change", "refactor", "fix", "delete", "remove", "code", "file",
            "function", "class", "method", "import", "module", "script",
            ".py", ".js", ".ts", ".jsx", ".tsx", ".css", ".html", ".json",
            ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
        ]
        combined = f"{step} {user_prompt}".lower()
        return any(kw in combined for kw in coding_keywords)


def get_five_phase_engine(config: Optional[Dict[str, Any]] = None) -> FivePhaseEngine:
    """Get Optimized 7-Phase Pipeline Engine (V3) instance"""
    return FivePhaseEngine(config)
