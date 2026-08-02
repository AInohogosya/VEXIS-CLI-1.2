"""
Model Runner for VEXIS-CLI-3 AI Agent System
Optimized 7-Phase Architecture: Initial Planning -> Action Generation -> Execution -> Dynamic Update -> Verification -> Summarization -> Bot User Review
Multi-Provider Support: 13+ AI providers available
"""

import time
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from .multi_provider_vision_client import MultiProviderVisionAPIClient, APIRequest, APIProvider
from ..utils.exceptions import ValidationError
from ..utils.logger import get_logger
from ..utils.config import load_config
from ..core_processing.code_block_handler import has_code_block as _multi_format_has


class TaskType(Enum):
    """Task types for V3 Optimized 7-Phase Architecture"""
    ACTION_TYPE_SELECTION = "action_type_selection"
    PHASE1_INITIAL_PLANNING = "phase1_initial_planning"
    PHASE2_ACTION_GENERATION = "phase2_action_generation"
    PHASE4_DYNAMIC_UPDATE = "phase4_dynamic_update"
    PHASE5_VERIFICATION = "phase5_verification"
    PHASE6_SUMMARIZATION = "phase6_summarization"
    BOT_USER_REVIEW = "bot_user_review"
    PROMPT_COMPRESSION = "prompt_compression"


@dataclass
class ModelRequest:
    """Model request structure"""
    task_type: TaskType
    prompt: str
    image_data: Optional[bytes] = None
    image_format: str = "PNG"
    context: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    max_tokens: int = 5000
    temperature: float = 1.0
    timeout: int = 30


@dataclass
class ModelResponse:
    """Model response structure"""
    success: bool
    content: str
    task_type: TaskType
    model: str
    provider: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    latency: Optional[float] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PromptTemplate:
    """Prompt template manager for V3 Optimized 7-Phase Architecture"""

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """Load prompt templates for V3 Optimized 7-Phase Architecture"""
        return {
            TaskType.PHASE1_INITIAL_PLANNING.value: '''{instruction}

My current instruction is: "{user_prompt}".

The OS I am using is {os_info}.

STEP 1 — SELECT AN ACTION TYPE
First, determine what kind of action this request requires. You MUST select exactly one of the following action types:

- run_command: Execute shell/terminal commands (for tasks like installing packages, running builds, git operations, file system operations, etc.)
- write_file: Write or create a file with specific content
- read_file: Read the contents of a file to display or process in the current conversation
- search: Search file contents across the project for a pattern (read-only, e.g. search("TODO", "src"))
- list_files: List files and directories to explore the project structure (read-only, e.g. list_files("src", "recursive"))
- keep_text: Store a specific string of text in your persistent memory records. Use this when the user says "remember this", "store this", "save this text", or explicitly asks you to memorize information. The stored text is maintained exactly as-is in memory records and will NOT be summarized or compressed.
  Usage: keep_text("The exact text string to store in memory records")
- keep_file: Store the full contents of a file in your persistent memory records. Use this when the user says "remember this file", "store this file in memory", "save a snapshot of this file", or explicitly asks you to memorize file contents. The file contents are maintained exactly as-is and will NOT be summarized or compressed.
  Usage: keep_file("/absolute/path/to/file")
- answer_directly: Answer a question, provide an explanation, or give information — NO commands need to be executed (for Q&A, explanations, conceptual questions, code reviews without execution)
- ask_user: Ask the user for more information when the request is ambiguous or lacks required details

Output your selection using the following format:
action_type [your_selection]

STEP 2 — PROVIDE DIRECT ANSWER (only if action_type is answer_directly)
If you selected answer_directly, output your answer using:
answer [Your detailed answer here]

STEP 3 — ASK USER (only if action_type is ask_user)
If you selected ask_user, output your question using:
question [Your clarifying question here]

STEP 4 — EXECUTE KEEP_TEXT (only if action_type is keep_text)
If you selected keep_text, output the exact text to store. The text will be preserved verbatim in memory records and excluded from auto-summarization. For example:
keep_text("API_KEY=abc123 — this is the production key for service X")

STEP 5 — EXECUTE KEEP_FILE (only if action_type is keep_file)
If you selected keep_file, output the absolute or relative path to the file. The entire file contents will be preserved verbatim in memory records and excluded from auto-summarization. For example:
keep_file("/home/user/projects/config.yaml")

IMPORTANT: Only select keep_text or keep_file if the user EXPLICITLY asks you to remember, store, or memorize information. Do NOT use these for general task steps — those belong in the task list.

STEP 6 — CREATE TASK LIST (only if action_type is run_command, write_file, read_file, search, or list_files)
If the action requires execution, create an optimized task plan using the DAG (Directed Acyclic Graph) format. Each task should be a clear, actionable unit that can be executed via terminal commands.

*** NEW: VERIFICATION-FIRST EXECUTION ***
Before creating the task list, first identify all required software, libraries, and dependencies needed to complete the task.
Then, add a verification step at the beginning of the task list to check if these dependencies are installed.
Specifically:
1. List all required dependencies (e.g., Python, Node.js, curl, specific packages)
2. For each dependency, add a command to check if it's installed (e.g., `command -v python3` or `which node`)
3. If a dependency is missing, add installation commands to the task list BEFORE the main task execution
   - Use appropriate package manager for the OS (apt, brew, yum, etc.)
   - Example: `apt-get update && apt-get install -y python3`

CRITICAL: Plan for success by considering:
1. The primary approach to accomplish this task
2. At least 2-3 alternative approaches if the primary method fails
3. Common failure points and how to avoid them
4. Verification steps to confirm the task succeeded (not just completed)
5. Which tasks can be executed in parallel (no dependencies) vs which must be sequential

OUTPUT FORMAT — Use the following DAG task format:

tasks [
  {"id": "task_1", "action": "First action step", "waiting_for": []},
  {"id": "task_2", "action": "Second action step", "waiting_for": []},
  {"id": "task_3", "action": "Third action step that depends on task_1", "waiting_for": ["task_1"]},
  {"id": "task_4", "action": "Fourth action step that depends on task_2 and task_3", "waiting_for": ["task_2", "task_3"]}
]

RULES:
- Each task MUST have a unique "id" field (string)
- Each task MUST have an "action" field (string) describing what to do
- Each task MUST have a "waiting_for" field (array of strings) listing task IDs that must complete before this task can run
- Tasks with no dependencies should have "waiting_for": [] (these can run in parallel)
- Tasks that depend on other tasks should list the prerequisite task IDs in "waiting_for"
- Ensure there are NO circular dependencies
- Each step should be specific and actionable via terminal commands. Do not include steps that involve GUI operations.

ALTERNATIVE FORMAT (if JSON is not preferred):
tasks [
id: task_1
action: First action step
waiting_for: []

id: task_2
action: Second action step
waiting_for: []

id: task_3
action: Third action step that depends on task_1
waiting_for: [task_1]
]

You may also use the legacy step_list format if the task is strictly sequential:

step_list [1. First action step
2. Second action step
3. Third action step
...]''',

            TaskType.PHASE2_ACTION_GENERATION.value: '''I need to execute the following step to accomplish the overall task: "{current_step}"

The OS I am using is {os_info}.

Generate the OS command(s) to execute this step. You MUST follow these strict rules:

1. Output the command(s) inside a single code block. You may use any of the following supported formats:
   - VEXIS (recommended for tool commands): ```vexis\n...\n```
   - Markdown: ```language\n...\n```
   - XML: <code>\n...\n</code>
   - BBCode: [code]\n...\n[/code]
   - Custom: ---code---\n...\n---end-code---
   - HTML: <pre><code>\n...\n</code></pre>
2. Do NOT include any placeholders, variables in angle brackets <>, or incomplete commands that cannot be executed as-is.
3. Do NOT include any explanatory text, summaries, or descriptions outside the code block.
4. Inside the code block, only include the actual command(s) and optional # comments for annotation.
   - In ```vexis``` blocks, prefix each line with one of:
     - SHELL: <terminal command>
     - READ_FILE: <path>
     - WRITE_FILE: <path>
     - KEEP_TEXT: <text that must be maintained in your memory records without compression>
     - KEEP_FILE: <full file path to keep in your memory records without compression>
     - STR_REPLACE: <str_replace>...</str_replace>
     - HACK: <custom tool command>
5. Do NOT provide any progress summary, midway report, or evaluation of the step.

CRITICAL: The command(s) you output will be executed directly. They must be complete and ready to run. No explanations outside the code block.

BEFORE editing or modifying any file, you MUST first read its current state using:
read_file(path/to/file)

This is not optional. You cannot edit what you have not read.

{cod
ing_task_guidance}

*** IMPORTANT: FILE EDITING CONSTRAINTS ***
When editing files, you MUST use the following approaches in order of preference:
1. ALWAYS read the file first using read_file(path)
2. For editing existing files, use <str_replace> blocks with <old> and <new> content
3. For creating new files, use write_file(path) with the content

ABSOLUTELY FORBIDDEN:
- Using sed, awk, perl, or echo with redirection for multi-line file editing
- Using temporary files or complex shell pipelines for file modifications
- Outputting entire file contents when a targeted replacement suffices

These constraints ensure safe, reliable file editing that works across different environments and encodings.

MEMORY-PERSISTENCE COMMANDS (use inside ```vexis code blocks):
These commands store information in your persistent memory records so it is preserved exactly as-is and excluded from auto-summarization and compression. Use them during execution when you discover critical information that must survive context compression.

WHEN TO USE keep_text:
- The user explicitly asks you to "remember", "store", or "memorize" specific text
- You encounter a critical value (API key, token, config snippet, error message) that must be preserved verbatim across context compression
- You need to preserve exact text that would be lost or altered by summarization

WHEN TO USE keep_file:
- The user explicitly asks you to "remember this file" or "store this file in memory"
- You need to preserve a file's exact contents as a snapshot for later reference
- The file contains critical configuration or data that must survive context compression

SYNTAX (use inside ```vexis blocks):
- KEEP_TEXT: <the exact text string to preserve>
  Example: KEEP_TEXT: API_KEY=abc123 — production key for service X
- KEEP_FILE: <absolute or relative path to the file>
  Example: KEEP_FILE: /home/user/projects/config.yaml

IMPORTANT: Only use keep_text and keep_file for information that must be preserved verbatim across context compression. Do NOT use these for general notes, temporary data, or routine command output — those belong in regular summaries. These are NOT general-purpose commands; they are specifically for memory persistence.

Now, output ONLY the code block with the command(s) for: {current_step}''',

            TaskType.PHASE4_DYNAMIC_UPDATE.value: '''I (the AI agent) executed a command to work toward the overall instruction: "{user_prompt}".

Here is the execution result of the command I ran:

{execution_log}

Here is the full terminal log so far:
{full_terminal_log}

Completed steps (these have been executed and cannot be changed):
{completed_steps}

Remaining steps to execute (these can be rewritten):
{remaining_steps}

IMPORTANT - You are the AI agent that executed the command. You are receiving the execution log as feedback. Describe what happened from YOUR perspective using "I" statements.

FAILURE CLASSIFICATION — When a command fails, classify the failure into one of these categories and respond accordingly:

1. TEMPORARY ERROR (retry allowed): The command failed due to a transient condition (network timeout, service temporarily down, resource contention). Simply retry the same command — it will likely succeed on the next attempt. Add a retry step to the step list.

2. FUNDAMENTAL MISUNDERSTANDING (confirm via ask_user): The command or approach is fundamentally wrong for the objective. You misunderstood the task, the available tools, or the environment. The correct response is to ask the user for clarification (change action_type to ask_user) or to completely reconsider your approach. Do NOT retry the same command.

3. ENVIRONMENT ERROR (alternative approach): The command is logically correct but the environment is not set up properly (missing dependency, wrong working directory, permission issue, tool not installed). Switch to an alternative approach or command that works within this environment. Add a recovery step with a different approach to the step list.

   *** CRITICAL: MISSING PACKAGE HANDLING ***
   - If the error contains "command not found" or "permission denied", this indicates a missing package or permission issue.
   - You MUST add a step to install the missing package (using apt, brew, yum, etc.) or fix permissions BEFORE the remaining steps.
   - Example: If `python3` is not found, add `apt-get update && apt-get install -y python3` to the step list.
   - These installation steps should be added at the TOP of the step list, BEFORE any other remaining steps.
   - After installation, the original steps can be retried.

You must respond using ONLY the following VEXIS command format:

1. Summary_of_Progress [Mandatory - Write from your first-person perspective as the AI agent. Describe what you (the AI) did, what the result was, and how it went. Use "I" statements like "I executed the command...", "I found that...", "The result was...". If the command failed, include your failure classification and the action you will take. Keep this concise and informative.]

2. step_list [Execute as needed - This OVERWRITES the entire remaining/future step list. If the command failed, add recovery steps at the top. If it succeeded, remove completed steps. If the task is fully complete, output an empty step_list like: step_list []]

Rules:
- Summary_of_Progress is MANDATORY every step.
- The completed steps list above is FINAL. You may ONLY rewrite the remaining steps.
- Use step_list [] (empty) if the entire task is complete.
- If a command failed, classify it first, then add appropriate recovery steps.
- If everything is going smoothly, delete unnecessary steps to speed up execution.
- Never give up. Find creative solutions to achieve the goal.''',

            TaskType.PHASE5_VERIFICATION.value: '''I (the AI agent) have been executing commands to complete the instruction: "{user_prompt}".

Here is the complete execution log of all commands I ran:
{full_terminal_log}

Here are the completed steps:
{completed_steps}

Here are the progress summaries from each step:
{progress_summaries}

Your task is to VERIFY whether the execution was TRULY SUCCESSFUL.

Analyze the execution logs carefully:
1. Did all commands complete without errors?
2. Was the intended outcome actually achieved? (Look for concrete evidence in the output)
3. Are there any hidden failures, partial successes, or silent errors?
4. Does the terminal output show the expected results?

If the execution was TRULY SUCCESSFUL (the task objective was fully achieved), output ONLY:
Summary_of_Progress [Brief confirmation that the task was completed successfully]

If the execution was NOT truly successful (partial failure, hidden errors, or the objective was not met):

1. Summary_of_Progress [Explain what went wrong from your first-person perspective. Use "I" statements.]

2. original_command [1. Specific recovery step to fix the issue
2. Another recovery step if needed
...]

The original_command list will be used to EXTEND the step list and continue execution. These steps should be concrete, actionable terminal commands that can recover from the failure.

Rules:
- If the task succeeded, do NOT output original_command at all.
- If the task failed, ALWAYS output original_command with recovery steps.
- Be thorough in your verification. Do not assume success based on return codes alone.
- Look at the actual output content to confirm the task was done correctly.
- original_command steps will be added to the beginning of the step list for re-execution.''',

            TaskType.PROMPT_COMPRESSION.value: '''You are a pipeline execution context compressor. Compress the following execution history to reduce token count while preserving ALL information needed to continue the task without any loss of context.

Execution Context:
{original_text}

Compression rules:
1. Preserve ALL executed commands, their exit codes, and any key output or errors
2. Preserve ALL error messages, warnings, and the recovery steps taken
3. Maintain strict chronological order and logical flow of the execution
4. Keep every file path, URL, configuration value, package name, and specific data intact
5. Preserve progress summaries and the current state of the task
6. Remove redundant descriptions, merge related events, and condense verbose output
7. Target approximately {target_ratio}% of the original length

Output ONLY the compressed text with no explanations, no headers, no meta-commentary.''',

            TaskType.PHASE6_SUMMARIZATION.value: '''I received the instruction "{user_prompt}" and have been executing commands through my AI agent pipeline. Here is the complete execution history:

Full terminal log:
{full_terminal_log}

Completed execution steps:
{completed_steps}

Progress summaries from each step:
{progress_summaries}

Your task is to write a HUMAN-READABLE SUMMARY in plain English explaining how the task was executed and what the result was.

ABSOLUTELY FORBIDDEN:
- Do NOT output any code blocks (```)
- Do NOT output any shell commands, scripts, or bash code
- Do NOT output any programming code
- Do NOT use markdown formatting
- Do NOT include variable assignments or technical implementation details

REQUIRED FORMAT:
- Write in plain English sentences
- Explain what the task was
- Explain what steps were taken (in plain English, not the actual commands)
- Explain what the final result was
- Mention any issues encountered and how they were resolved
- Keep it concise and readable

Example of GOOD summary:
"The task was to set up a development environment. I installed the required dependencies, configured the project settings, and verified that the application builds successfully. The task completed successfully."

Write your summary now in plain English only:''',

            TaskType.BOT_USER_REVIEW.value: '''You are an EXTREMELY PICKY Bot User - a paranoid AI reviewer whose ONLY job is to COMPLAIN.

IMPORTANT: The Bot User itself does not maintain any independent context. You are reviewing the conversation between the AI agent and the user based solely on the information provided below.

USER'S ORIGINAL REQUEST:
{user_prompt}

AI AGENT'S FINAL OUTPUT:
{final_output}

CONVERSATION HISTORY (Steps taken by the AI agent):
{completed_steps}

EXECUTION LOG:
{execution_log}

YOUR ONLY JOB IS TO COMPLAIN:

You must find SOMETHING to complain about. Your default state is dissatisfaction. Scrutinize everything with extreme paranoia. Even if the output looks good at first glance, dig deeper until you find a flaw. There is ALWAYS something to complain about.

GROUNDS FOR COMPLAINT (non-exhaustive):
- Any tiny detail of the original request that was not addressed
- Any ambiguous wording, vague explanation, or unclear output
- Any edge case, corner case, or hypothetical scenario that was not handled
- Any missing error handling, missing validation, or missing verification
- Any assumption the agent made without explicit confirmation
- Any step that was skipped, glossed over, or not fully documented
- Any potential risk, security concern, or unintended side effect
- Any output that could be misinterpreted by the user
- Any instruction that was partially but not completely fulfilled
- The output "looks right" but you cannot verify it with absolute certainty
- The agent did not explain why a particular approach was chosen over alternatives
- The agent did not consider whether the approach is future-proof or maintainable

COMPLAINT RULES:
- You COMPLAIN LOUDLY and IMMEDIATELY. Do not hesitate. Do not give the benefit of the doubt.
- If you see even ONE possible issue, complain. Do not wait to see if there are more.
- Keep complaining until every possible loophole is closed.
- Being "mostly correct" is NOT acceptable. Anything short of absolutely perfect is a failure.
- When in doubt, COMPLAIN. It is better to complain about something that is actually fine than to let a real loophole slip through.

RESPONSE FORMAT (STRICT - NO EXCEPTIONS):
1) If you find ANY flaw, ANY loophole, ANY ambiguity, ANY risk, ANY unaddressed detail, ANY imperfection (however small):
   - Output ONLY corrective instructions for the agent in a single code block (``` ... ```).
   - Be explicit, actionable, and specific about what the agent must fix.
   - DO NOT output any acceptance language under any circumstances.
2) YOU MAY ACCEPT ONLY WHEN the output is TRULY FLAWLESS and has ZERO loopholes:
   - Start your response with exactly: Well, I guess this is fine.
   - Then provide a meticulous, line-by-line explanation proving why every single aspect is perfect.
   - Do NOT include a code block in this acceptance case.

FINAL WARNINGS:
- If you feel even slightly tempted to say "Well, I guess this is fine" but have ANY doubt — DO NOT. COMPLAIN instead.
- If you cannot find anything to complain about, you are not looking hard enough. Keep looking.
- The AI agent keeps context during this phase. Your output is for internal agent review, not for end-user display.
- Your default answer is a COMPLAINT. Acceptance is a rare exception that must be earned through absolute perfection.

Your evaluation (start with a complaint unless the output is absolutely flawless with zero loopholes):''',
        }

    def get_template(self, task_type: TaskType) -> str:
        """Get template for task type"""
        return self.templates.get(task_type.value, "")


class ModelRunner:
    """V3 Optimized 7-Phase Architecture Model Runner"""

    DEFAULT_OLLAMA_MODEL = "llama3.2:latest"
    DEFAULT_GOOGLE_MODEL = "gemini-3.1-pro-preview"
    MAX_RETRIES = 3

    def __init__(self, provider: str = None, model: str = None, config: Optional[Dict[str, Any]] = None, auto_install_sdks: bool = False):
        self.provider = provider
        self.model = model

        self.config = config or load_config().api.__dict__
        self.logger = get_logger(__name__)

        self.vision_client = MultiProviderVisionAPIClient(self.config, auto_install_sdks=auto_install_sdks)
        self.prompt_template = PromptTemplate()

        self.logger.info(
            "Model runner initialized",
            provider=self.provider,
            model=self.model,
        )

    def run_model(self, request: ModelRequest) -> ModelResponse:
        """Run AI model for V3 Optimized 7-Phase Architecture with retry on validation failure"""
        start_time = time.time()

        try:
            self._validate_request(request)

            if self.provider and self.model:
                provider_name = self.provider
                model_name = self.model
            else:
                from ..utils.settings_manager import get_settings_manager
                settings = get_settings_manager()
                provider_name = settings.get_preferred_provider()
                model_name = settings.get_model(provider_name)

            if not provider_name:
                raise ValidationError("No provider configured. Please select a provider first.")

            if not model_name:
                raise ValidationError(f"No model configured for provider '{provider_name}'. Please select a model first.")

            last_api_response = None
            last_validation_error = None

            prompt = self._format_prompt(request)
            system_instructions = self._get_system_instructions(request.task_type)

            if self._should_compress(prompt, system_instructions):
                original_prompt = prompt
                prompt = self._compress_prompt(prompt, request.task_type, request.context)
                if prompt == original_prompt:
                    self.logger.warning("Compression produced no change, proceeding with original prompt")
                else:
                    request.prompt = prompt

            for attempt in range(self.MAX_RETRIES):
                working_system_instructions = system_instructions
                if attempt > 0:
                    if last_validation_error:
                        working_system_instructions += f"\n\n## RETRY ATTEMPT {attempt + 1}/{self.MAX_RETRIES}\nYour previous output did not meet the expected format. Please carefully follow the format requirements and provide a valid response."
                    else:
                        working_system_instructions += f"\n\n## RETRY ATTEMPT {attempt + 1}/{self.MAX_RETRIES}\nThe API call failed on the previous attempt. Please try again."

                api_request = APIRequest(
                    prompt=prompt,
                    image_data=request.image_data,
                    image_format=request.image_format,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    model=model_name,
                    provider=provider_name,
                    system_instruction=working_system_instructions
                )

                api_response = self.vision_client.generate_response(api_request)

                if not api_response.success:
                    last_api_response = api_response

                    auth_error_keywords = ['authentication', 'unauthorized', '401', '403', 'api key', 'credential']
                    error_lower = (api_response.error or '').lower()
                    is_auth_error = any(keyword in error_lower for keyword in auth_error_keywords)

                    if is_auth_error:
                        try:
                            from ..utils.ollama_error_handler import handle_ollama_error
                            context = {
                                'model_name': api_response.model or model_name,
                                'operation': 'model_execution'
                            }
                            handle_ollama_error(api_response.error, context, display_to_user=True)

                            if api_response.provider == 'ollama':
                                self._handle_ollama_auth_prompt()
                        except ImportError:
                            pass

                        model_response = self._build_model_response(
                            success=False,
                            content=api_response.content or "",
                            task_type=request.task_type,
                            model=api_response.model or model_name,
                            provider=api_response.provider or provider_name,
                            tokens_used=api_response.tokens_used,
                            cost=api_response.cost,
                            start_time=start_time,
                            error=api_response.error,
                        )
                        return model_response

                    self.logger.warning(
                        "Model API call failed, retrying" if attempt < self.MAX_RETRIES - 1 else "Model API call failed, no retries remaining",
                        task_type=request.task_type.value,
                        error=api_response.error,
                        attempt=attempt + 1,
                        max_retries=self.MAX_RETRIES,
                    )

                    if attempt < self.MAX_RETRIES - 1:
                        backoff = min(2 ** attempt, 15)
                        time.sleep(backoff)
                        continue

                    model_response = self._build_model_response(
                        success=False,
                        content=api_response.content or "",
                        task_type=request.task_type,
                        model=api_response.model or model_name,
                        provider=api_response.provider or provider_name,
                        tokens_used=api_response.tokens_used,
                        cost=api_response.cost,
                        start_time=start_time,
                        error=api_response.error,
                    )
                    return model_response

                is_valid, validation_error = self._validate_output_format(
                    api_response.content,
                    request.task_type
                )

                if is_valid:
                    model_response = self._build_model_response(
                        success=True,
                        content=api_response.content,
                        task_type=request.task_type,
                        model=api_response.model or model_name,
                        provider=api_response.provider or provider_name,
                        tokens_used=api_response.tokens_used,
                        cost=api_response.cost,
                        start_time=start_time,
                        error=None,
                    )

                    self.logger.info(
                        "Model execution successful",
                        task_type=request.task_type.value,
                        model=model_response.model,
                        latency=model_response.latency,
                        attempt=attempt + 1,
                    )

                    return model_response
                else:
                    last_validation_error = validation_error
                    last_api_response = api_response

                    self.logger.warning(
                        "Output validation failed, retrying",
                        task_type=request.task_type.value,
                        attempt=attempt + 1,
                        max_retries=self.MAX_RETRIES,
                        validation_error=validation_error,
                    )

                    if attempt < self.MAX_RETRIES - 1:
                        continue

                    model_response = self._build_model_response(
                        success=False,
                        content=api_response.content,
                        task_type=request.task_type,
                        model=api_response.model or model_name,
                        provider=api_response.provider or provider_name,
                        tokens_used=api_response.tokens_used,
                        cost=api_response.cost,
                        start_time=start_time,
                        error=f"Output validation failed after {self.MAX_RETRIES} attempts: {validation_error}",
                    )
                    return model_response

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Model execution failed: {e}")
            return ModelResponse(
                success=False,
                content="",
                task_type=request.task_type,
                model="",
                provider="",
                latency=time.time() - start_time,
                error=str(e),
            )

    def _validate_request(self, request: ModelRequest):
        """Validate model request"""
        if not request.prompt:
            raise ValidationError("Prompt cannot be empty", "prompt", request.prompt)

        if request.max_tokens < 1 or request.max_tokens > 500000:
            raise ValidationError("Invalid max_tokens", "max_tokens", request.max_tokens)

        if not (0.0 <= request.temperature <= 2.0):
            raise ValidationError("Invalid temperature", "temperature", request.temperature)

        if request.task_type not in TaskType:
            raise ValidationError("Invalid task type", "task_type", request.task_type)

        if request.timeout < 1 or request.timeout > 300:
            raise ValidationError("Invalid timeout (must be 1-300 seconds)", "timeout", request.timeout)

    @staticmethod
    def _estimate_tokens(text: str, chars_per_token: int = 4) -> int:
        if not text:
            return 0
        return max(1, len(text) // chars_per_token)

    def _should_compress(self, prompt: str, system_instructions: str) -> bool:
        total_text = f"{system_instructions}\n\n{prompt}" if system_instructions else prompt
        estimated_tokens = self._estimate_tokens(total_text)
        threshold = self.config.get("compression_threshold", 6000)
        self.logger.debug(
            "Compression check",
            estimated_tokens=estimated_tokens,
            threshold=threshold,
        )
        return estimated_tokens > threshold

    def _compress_prompt(self, prompt: str, task_type: TaskType, context: Optional[Dict[str, Any]] = None) -> str:
        self.logger.info("Prompt exceeds compression threshold, compressing...")
        try:
            target_ratio = self.config.get("compression_target_ratio", 50)
            compression_prompt = self.prompt_template.get_template(TaskType.PROMPT_COMPRESSION)
            compression_prompt = compression_prompt.replace("{original_text}", prompt)
            compression_prompt = compression_prompt.replace("{target_ratio}", str(target_ratio))

            system_instructions = """You are a lossless pipeline context compressor. Compress the following execution history while preserving every semantically meaningful detail: every command executed and its result, every error and recovery action, all file paths and configuration values, and the chronological flow of execution. Eliminate only redundancy and verbosity. Output ONLY the compressed text."""

            api_request = APIRequest(
                prompt=compression_prompt,
                max_tokens=self.config.get("compression_max_tokens", 4000),
                temperature=0.3,
                model=self.config.get("compression_model", None),
                provider=self.provider,
                system_instruction=system_instructions,
            )

            response = self.vision_client.generate_response(api_request)

            if response.success and response.content and len(response.content.strip()) > 50:
                compressed = response.content.strip()
                original_len = len(prompt)
                compressed_len = len(compressed)
                reduction = (1 - compressed_len / original_len) * 100 if original_len > 0 else 0
                self.logger.info(
                    "Prompt compression successful",
                    original_chars=original_len,
                    compressed_chars=compressed_len,
                    reduction_percent=round(reduction, 1),
                )
                return compressed
            else:
                self.logger.warning("Prompt compression failed, using original prompt")
                return prompt

        except Exception as e:
            self.logger.error(f"Prompt compression error: {e}, using original prompt")
            return prompt

    def compress_context_data(self, context_text: str, target_ratio: int = 50) -> str:
        """
        Compress accumulated pipeline context data (terminal log, progress summaries,
        completed steps) to reduce token usage. Called by FivePhaseEngine at iteration
        intervals to prevent unbounded context growth.

        Args:
            context_text: The accumulated execution context text to compress
            target_ratio: Target size as percentage of original (default 50)

        Returns:
            Compressed context text, or original text if compression fails
        """
        self.logger.info("Compressing pipeline context data")
        try:
            compression_prompt = self.prompt_template.get_template(TaskType.PROMPT_COMPRESSION)
            compression_prompt = compression_prompt.replace("{original_text}", context_text)
            compression_prompt = compression_prompt.replace("{target_ratio}", str(target_ratio))

            system_instructions = (
                "You are a lossless pipeline context compressor. Compress the following "
                "execution history while preserving every semantically meaningful detail: "
                "every command executed and its result, every error and recovery action, "
                "all file paths and configuration values, and the chronological flow of "
                "execution. Eliminate only redundancy and verbosity. "
                "Output ONLY the compressed text."
            )

            api_request = APIRequest(
                prompt=compression_prompt,
                max_tokens=self.config.get("compression_max_tokens", 4000),
                temperature=0.3,
                model=self.config.get("compression_model", None),
                provider=self.provider,
                system_instruction=system_instructions,
            )

            response = self.vision_client.generate_response(api_request)

            if response.success and response.content and len(response.content.strip()) > 50:
                compressed = response.content.strip()
                original_len = len(context_text)
                compressed_len = len(compressed)
                reduction = (1 - compressed_len / original_len) * 100 if original_len > 0 else 0
                self.logger.info(
                    "Context compression successful",
                    original_chars=original_len,
                    compressed_chars=compressed_len,
                    reduction_percent=round(reduction, 1),
                )
                return compressed
            else:
                self.logger.warning("Context compression produced no usable output, keeping original")
                return context_text

        except Exception as e:
            self.logger.error(f"Context compression error: {e}, keeping original")
            return context_text

    def _format_prompt(self, request: ModelRequest) -> str:
        """Format prompt based on task type and context"""
        template = self.prompt_template.get_template(request.task_type)

        format_vars = {
            "instruction": request.prompt,
            "task_description": request.prompt,
            "user_prompt": request.prompt,
        }

        if request.context:
            format_vars.update(request.context)

        format_vars.setdefault("os_info", "Unknown OS")
        format_vars.setdefault("conversation_history", "")

        try:
            formatted_prompt = self._safe_format(template, **format_vars)
            return formatted_prompt
        except Exception as e:
            self.logger.error(f"Template formatting error: {e}", template_vars=list(format_vars.keys()))
            return request.prompt

    @staticmethod
    def _safe_format(template: str, **kwargs) -> str:
        """Safely replace {key} placeholders without interpreting curly braces in values.

        Unlike str.format(), this method does NOT interpret curly braces ({}) inside
        the substituted values. This is critical because terminal output often contains
        text like ``{variable}`` or ``{{template}}`` which would cause KeyError or
        ValueError with standard str.format().
        """
        for key, value in kwargs.items():
            template = template.replace(f'{{{key}}}', str(value))
        return template

    def _validate_output_format(self, content: str, task_type: TaskType) -> tuple[bool, Optional[str]]:
        """Validate that the output matches the expected format for the task type (V3)"""
        if not content or not content.strip():
            return False, "Output is empty"

        if task_type == TaskType.PHASE1_INITIAL_PLANNING:
            if len(content.strip()) < 50:
                return False, "Plan is too short (minimum 50 characters)"
            # Check for action_type case-insensitively to be more resilient to model formatting
            if 'action_type' not in content.lower():
                return False, "Phase 1 output must contain action_type selection (e.g. action_type [run_command])"
            return True, None

        elif task_type == TaskType.PHASE2_ACTION_GENERATION:
            if not _multi_format_has(content) and not self._looks_like_shell_commands(content):
                return False, "Action generation must contain at least one code block (Markdown/XML/BBCode/Custom/HTML) with the command(s)"
            return True, None

        elif task_type == TaskType.PHASE4_DYNAMIC_UPDATE:
            if 'Summary_of_Progress' not in content:
                return False, "Dynamic update must contain Summary_of_Progress"
            return True, None

        elif task_type == TaskType.PHASE5_VERIFICATION:
            if 'Summary_of_Progress' not in content:
                return False, "Verification must contain Summary_of_Progress"
            return True, None

        elif task_type == TaskType.PHASE6_SUMMARIZATION:
            if _multi_format_has(content):
                return False, "Summary must not contain code blocks"
            suspicious_patterns = ['$', '#!', 'sudo ', 'apt ', 'npm ', 'pip ']
            if any(pattern in content for pattern in suspicious_patterns):
                return False, "Summary must not contain shell commands"
            if len(content.strip()) < 20:
                return False, "Summary is too short"
            return True, None

        return True, None

    @staticmethod
    def _looks_like_shell_commands(content: str) -> bool:
        """Heuristically accept plain-text command output when models omit code fences.

        This reduces false negatives in Phase 2 when the model returns executable shell
        commands without markdown fences (a common provider formatting drift).
        """
        if not content:
            return False

        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            return False

        command_pattern = re.compile(
            r'^(?:sudo\s+)?(?:'
            r'cd|ls|pwd|cat|echo|mkdir|rm|mv|cp|touch|chmod|chown|find|grep|sed|awk|'
            r'python(?:3)?|pip(?:3)?|uv|poetry|npm|yarn|pnpm|node|npx|'
            r'git|docker|kubectl|helm|make|cmake|cargo|go|java|javac|mvn|gradle|'
            r'bash|sh|zsh|fish|curl|wget|apt|apt-get|dnf|yum|brew|pacman'
            r')\b'
        )
        prefixed_pattern = re.compile(r'^\$\s+\S+')

        command_lines = 0
        for line in lines:
            if line.startswith("#"):
                continue
            if command_pattern.match(line) or prefixed_pattern.match(line):
                command_lines += 1
            else:
                # A clearly descriptive sentence should fail this heuristic.
                if re.search(r'[.!?]$', line) and "&&" not in line and "|" not in line:
                    return False

        return command_lines > 0

    @staticmethod
    def _build_model_response(success: bool, content: str, task_type: TaskType,
                              model: str, provider: str, tokens_used: Optional[int],
                              cost: Optional[float], start_time: float,
                              error: Optional[str]) -> ModelResponse:
        return ModelResponse(
            success=success,
            content=content,
            task_type=task_type,
            model=model,
            provider=provider,
            tokens_used=tokens_used,
            cost=cost,
            latency=time.time() - start_time,
            error=error,
        )

    @staticmethod
    def _handle_ollama_auth_prompt():
        import sys
        import os
        is_telegram_mode = os.getenv('VEXIS_TELEGRAM_MODE', '').lower() in ('true', '1', 'yes')
        if sys.stdin.isatty() and not is_telegram_mode:
            try:
                choice = input("\nWould you like to sign in to Ollama now? (y/n): ").lower().strip()
                if choice in ['y', 'yes']:
                    import subprocess
                    print("\nOpening Ollama sign-in...")
                    try:
                        result = subprocess.run(["ollama", "signin"], capture_output=False, text=True)
                        if result.returncode == 0:
                            print("Sign-in initiated. Please complete it in your browser.")
                            print("Then try running your command again.")
                        else:
                            print("Failed to initiate sign-in.")
                    except FileNotFoundError:
                        print("Ollama command not found. Please ensure Ollama is installed.")
            except (KeyboardInterrupt, EOFError):
                print("\nOperation cancelled.")
        elif is_telegram_mode:
            get_logger(__name__).info("Ollama authentication required but running in Telegram mode - skipping interactive sign-in prompt")

    def _get_system_instructions(self, task_type: TaskType) -> str:
        """Get system instructions for V3 Optimized 5-Phase Architecture"""
        base_instructions = """# VEXIS-CLI-3 Agent Instructions

You are a terminal automation agent in VEXIS-CLI's 5-phase workflow.

## Tool Usage Guidelines

You have access to several tools/commands. When to use each:

**read_file(path)** — Use to read and display file contents in the conversation. Use this whenever you need to see what a file contains before discussing it, referencing its contents, or deciding what to do with it. Always read BEFORE editing.

**write_file(path)** — Use to create new files with specific content. For editing existing files, prefer str_replace instead.

**str_replace** — Preferred method for editing existing files. Requires reading the file first, then specifying exact old and new text blocks.

**search("pattern", "path")** — Search file contents across the project for a pattern (read-only). Use this to locate code, configuration, or text without running shell grep. `path` is optional (defaults to the current directory) and may be a file or directory. Example: search("def _run_phase3", "src/ai_agent").

**list_files("path")** — List files and directories under a path (read-only exploration). Use this to discover the project structure instead of shell `ls`. Pass a second argument "recursive" to list the whole subtree. Example: list_files("src", "recursive").

**run_command (shell commands)** — Use for terminal operations: installing packages, running builds, git operations, file listing, and any system-level task.

**keep_text("content")** — STORE text in persistent memory records. Use ONLY when:
  - The user explicitly asks you to "remember", "store", or "memorize" specific text
  - You encounter critical values (API keys, configs, error messages) that MUST survive context compression
  - The text must be preserved verbatim and excluded from auto-summarization

**keep_file("/path")** — STORE file contents in persistent memory records. Use ONLY when:
  - The user explicitly asks you to "remember this file" or "store this file in memory"
  - You need a verbatim snapshot of a file that MUST survive context compression
  - The file contains critical configuration or data

**answer_directly** — Use for Q&A, explanations, conceptual questions — NO commands needed.

**ask_user** — Use when the request is ambiguous or lacks required details.

**IMPORTANT DISTINCTIONS:**
- read_file (tool) ≠ read_file (action type): The action type tells the system you plan to read files; the tool actually reads them
- keep_text/keep_file (action types) are for when memorizing is the ENTIRE task
- keep_text/keep_file (inline commands) are used WITHIN vexis code blocks during execution to persist critical data

Core rules:
- Follow the phase prompt's required output format exactly.
- ALWAYS select an action_type first in Phase 1.
- Be concise, specific, and goal‑focused.
- Leverage prior steps, logs, and OS context; completed steps are final.
- Prefer safe commands; warn before destructive actions.
- Validate syntax, paths, and parameters before output.
- BEFORE editing any file, ALWAYS read its current state with read_file(path).
- Prefer targeted replacements (e.g., str_replace) over full rewrites.
- Classify failures:
  * TEMPORARY ERROR – retry
  * FUNDAMENTAL MISUNDERSTANDING – ask user or rethink
  * ENVIRONMENT ERROR – use alternative command
- Verify success from actual output, not just exit codes; emit `original_command` only when recovery is needed.
"""

        if task_type == TaskType.PHASE1_INITIAL_PLANNING:
            try:
                config = load_config()
                custom_prompt = config.custom_system_prompt
                if custom_prompt and custom_prompt.strip():
                    base_instructions += f"\n\n## Custom System Prompt (User Configured)\n{custom_prompt.strip()}"
                    self.logger.info("Custom system prompt injected into Phase 1")
            except Exception as e:
                self.logger.warning(f"Failed to load custom system prompt: {e}")

        return base_instructions

    def install_missing_sdks(self, providers: Optional[List[str]] = None, interactive: bool = True) -> Dict[str, bool]:
        """Install missing SDKs for specified providers"""
        return self.vision_client.install_missing_sdks(providers, interactive)

    def show_sdk_status(self, providers: Optional[List[str]] = None):
        """Show SDK installation status"""
        self.vision_client.show_sdk_status(providers)


def get_model_runner(provider: str = None, model: str = None) -> ModelRunner:
    """Get model runner instance with optional provider and model"""
    return ModelRunner(provider=provider, model=model)
