# Complete Module Inventory
This inventory is generated from the Python source tree and documents every Python module, its purpose when available, and its top-level classes/functions. It is intended to let readers understand the repository contents without opening the source files.
## `Groq/groq_hello.py`
**Imports:** os, groq, groq_models
- `get_initial_selection()` — Prompt user to select initial provider (Ollama, Google, or Groq)
- `select_company()` — Let user select a company/model family
- `select_subfamily(company_key, company_data)` — Let user select a subfamily within the chosen company
- `select_model(subfamily_key, subfamily_data)` — Let user select a specific model within the subfamily
- `progressive_model_selection()` — Guide user through progressive model selection
- `ask_groq(message, model='llama-3.1-8b-instant')` — Send message to Groq API and return response

## `Groq/groq_models.py`
Groq Model Definitions for VEXIS-CLI-3 Integration Organized by company/model family with progressive selection support Based on official Groq documentation as of 2025
- `get_all_models()` — Get all available models as a flat list
- `get_production_models()` — Get production-ready models
- `get_preview_models()` — Get preview models
- `get_models_by_capability(capability)` — Get models that support a specific capability
- `get_model_info(model_name)` — Get detailed information about a specific model

## `Groq/provider.py`
Groq Provider Setup and Configuration Handles Groq API key prompting, model selection, and provider configuration
**Imports:** getpass, typing
- `prompt_for_groq_api_key()` — Prompt user for Groq API key and handle saving
- `select_groq_model()` — Prompt user to select Groq model using curses arrow keys
- `configure_groq_provider()` — Configure Groq provider with API key and model selection

## `agent_core.py`
**Imports:** os, yaml, datetime, subprocess
- `get_os_context()`
- `load_config()`
- `update_log(message)`
- `autonomous_loop()`

## `api/__init__.py`
VEXIS-CLI-3 Unified API Package
**Imports:** .base
- `create_client(provider: str, api_key: str, **kwargs)` — Convenience function to create a client by provider name.
- `get_available_providers()` — Get list of available provider names

## `api/amazon_client.py`
Amazon Bedrock LLM Client Adapter
**Imports:** os, time, typing, .base
### Class `AmazonLLMClient` (`BaseLLM`)
Amazon Bedrock LLM client using boto3.
Methods:
- `__init__(self, api_key: Optional[str]=None, **kwargs)`
- `provider_type(self)`
- `default_model(self)`
- `_initialize_client(self)`
- `_convert_config(self, config: Optional[GenerationConfig])`
- `generate(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `generate_stream(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `list_models(self)`


## `api/anthropic_client.py`
Anthropic Claude LLM Client Adapter
**Imports:** os, time, typing, .base
### Class `AnthropicLLMClient` (`BaseLLM`)
Anthropic Claude LLM client using the official Anthropic SDK.
Methods:
- `__init__(self, api_key: Optional[str]=None, **kwargs)`
- `provider_type(self)`
- `default_model(self)`
- `_initialize_client(self)`
- `_convert_config(self, config: Optional[GenerationConfig])`
- `generate(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `generate_stream(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `list_models(self)` — Return empty list - model validation happens at API call time
- `count_tokens(self, text: str, model: Optional[str]=None)`


## `api/base.py`
Base Abstract Class for LLM Providers
**Imports:** abc, dataclasses, typing, enum
### Class `ProviderType` (`Enum`)
Supported LLM provider types
### Class `ResponseFormat` (`Enum`)
Supported response formats
### Class `GenerationConfig` (`object`)
Unified generation configuration across all providers
### Class `LLMResponse` (`object`)
Unified response structure across all providers
### Class `ModelInfo` (`object`)
Model information structure
### Class `BaseLLM` (`ABC`)
Abstract Base Class for all LLM API clients.
Methods:
- `__init__(self, api_key: Optional[str]=None, **kwargs)` — Initialize the LLM client.
- `provider_type(self)` — Return the provider type enum
- `default_model(self)` — Return the default model identifier for this provider
- `_initialize_client(self)` — Initialize the provider-specific client
- `generate(self, prompt: str, config: Optional[GenerationConfig]=None, **kwargs)` — Generate a response from the LLM.
- `generate_stream(self, prompt: str, config: Optional[GenerationConfig]=None, **kwargs)` — Generate a streaming response from the LLM.
- `async generate_async(self, prompt: str, config: Optional[GenerationConfig]=None, **kwargs)` — Asynchronously generate a response from the LLM.
- `async generate_stream_async(self, prompt: str, config: Optional[GenerationConfig]=None, **kwargs)` — Asynchronously generate a streaming response.
- `list_models(self)` — List available models for this provider.
- `get_model_info(self, model_id: str)` — Get information about a specific model.
- `count_tokens(self, text: str, model: Optional[str]=None)` — Count tokens in the given text for a specific model.
- `is_available(self)` — Check if the provider is properly configured and available.
- `_ensure_initialized(self)` — Ensure the client is initialized

### Class `LLMFactory` (`object`)
Factory class for creating LLM clients based on provider type.
Methods:
- `register(cls, provider_type: ProviderType, provider_class: type)` — Register a provider class with the factory
- `create(cls, provider_type: ProviderType, api_key: Optional[str]=None, **kwargs)` — Create an LLM client for the specified provider.
- `available_providers(cls)` — Get list of registered provider types

- `_estimate_cost(provider: str, model: str, prompt_tokens: int, completion_tokens: int)` — Estimate cost for API usage based on provider and model.

## `api/cohere_client.py`
Cohere AI LLM Client Adapter
**Imports:** os, time, typing, .base
### Class `CohereLLMClient` (`BaseLLM`)
Cohere AI LLM client using the official Cohere SDK.
Methods:
- `__init__(self, api_key: Optional[str]=None, **kwargs)`
- `provider_type(self)`
- `default_model(self)`
- `_initialize_client(self)`
- `_convert_config(self, config: Optional[GenerationConfig])`
- `generate(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `generate_stream(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `list_models(self)`


## `api/deepseek_client.py`
DeepSeek LLM Client Adapter
**Imports:** os, time, typing, .base
### Class `DeepSeekLLMClient` (`BaseLLM`)
DeepSeek LLM client using the OpenAI-compatible API.
Methods:
- `__init__(self, api_key: Optional[str]=None, **kwargs)`
- `provider_type(self)`
- `default_model(self)`
- `_initialize_client(self)`
- `_convert_config(self, config: Optional[GenerationConfig])`
- `generate(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `generate_stream(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `list_models(self)`


## `api/google_client.py`
Google Gemini (DeepMind) LLM Client Adapter
**Imports:** os, time, typing, .base
### Class `GoogleLLMClient` (`BaseLLM`)
Google Gemini LLM client using the official google-genai SDK.
Methods:
- `__init__(self, api_key: Optional[str]=None, **kwargs)` — Initialize Google Gemini client.
- `provider_type(self)`
- `default_model(self)`
- `_initialize_client(self)` — Initialize the Google GenAI client
- `_convert_config(self, config: Optional[GenerationConfig])` — Convert unified GenerationConfig to Google-specific config.
- `generate(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)` — Generate a response using Google Gemini API.
- `generate_stream(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)` — Generate a streaming response.
- `async generate_async(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)` — Asynchronously generate a response.
- `async generate_stream_async(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)` — Asynchronously generate a streaming response.
- `list_models(self)` — List available Gemini models.
- `get_model_info(self, model_id: str)` — Get information about a specific model
- `count_tokens(self, text: str, model: Optional[str]=None)` — Count tokens in the given text.
- `is_available(self)` — Check if Google provider is available


## `api/groq_client.py`
Groq LLM Client Adapter
**Imports:** os, time, typing, .base
### Class `GroqLLMClient` (`BaseLLM`)
Groq LLM client using the OpenAI-compatible API.
Methods:
- `__init__(self, api_key: Optional[str]=None, **kwargs)`
- `provider_type(self)`
- `default_model(self)`
- `_initialize_client(self)`
- `_convert_config(self, config: Optional[GenerationConfig])`
- `generate(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `generate_stream(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `list_models(self)`


## `api/integration_example.py`
Integration Example: Using the Unified API in main.py
**Imports:** os, typing, api
- `simple_main_example()` — Simple example of using the unified API in a main script.
### Class `AIAssistant` (`object`)
Example class that uses the unified API.
Methods:
- `__init__(self, provider: str='google', api_key: Optional[str]=None)` — Initialize the AI Assistant.
- `ask(self, question: str, **kwargs)` — Ask a question and get a response.
- `stream_ask(self, question: str, **kwargs)` — Ask a question and stream the response.

- `integration_with_existing_config(config: Dict[str, Any])` — Example of integrating with existing VEXIS configuration.
- `compare_providers_example()` — Example: Compare responses from different providers.
- `error_handling_example()` — Example: Robust error handling with the unified API.
- `advanced_configuration_example()` — Example: Advanced configuration options.
- `integration_with_model_runner()` — Example: How to integrate with existing ModelRunner.

## `api/meta_client.py`
Meta Llama LLM Client Adapter
**Imports:** os, time, typing, .base
### Class `MetaLLMClient` (`BaseLLM`)
Meta Llama LLM client using the OpenAI-compatible Llama API.
Methods:
- `__init__(self, api_key: Optional[str]=None, **kwargs)`
- `provider_type(self)`
- `default_model(self)`
- `_initialize_client(self)`
- `_convert_config(self, config: Optional[GenerationConfig])`
- `generate(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `generate_stream(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `list_models(self)` — Return empty list - model validation happens at API call time


## `api/microsoft_client.py`
Microsoft Azure OpenAI LLM Client Adapter
**Imports:** os, time, typing, .base
### Class `MicrosoftLLMClient` (`BaseLLM`)
Microsoft Azure OpenAI client using the OpenAI SDK.
Methods:
- `__init__(self, api_key: Optional[str]=None, **kwargs)`
- `provider_type(self)`
- `default_model(self)`
- `_initialize_client(self)`
- `_convert_config(self, config: Optional[GenerationConfig])`
- `generate(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `generate_stream(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `list_models(self)` — Return empty list - model validation happens at API call time


## `api/minimax_client.py`
MiniMax LLM Client Adapter
**Imports:** os, time, typing, .base
### Class `MiniMaxLLMClient` (`BaseLLM`)
MiniMax LLM client using OpenAI-compatible SDK.
Methods:
- `__init__(self, api_key: Optional[str]=None, **kwargs)` — Initialize MiniMax client
- `provider_type(self)` — Return the provider type
- `default_model(self)` — Return the default model for MiniMax
- `_initialize_client(self)` — Initialize the OpenAI-compatible client for MiniMax
- `get_model_info(self, model: Optional[str]=None)` — Get information about a specific model
- `generate(self, prompt: str, config: Optional[GenerationConfig]=None, **kwargs)` — Generate a response from MiniMax model.
- `generate_stream(self, prompt: str, config: Optional[GenerationConfig]=None, **kwargs)` — Generate a streaming response from MiniMax model.
- `async generate_async(self, prompt: str, config: Optional[GenerationConfig]=None, **kwargs)` — Generate an asynchronous response from MiniMax model.
- `async generate_stream_async(self, prompt: str, config: Optional[GenerationConfig]=None, **kwargs)` — Asynchronously generate a streaming response from MiniMax model.
- `list_models(self)` — List available MiniMax models.


## `api/mistral_client.py`
Mistral AI LLM Client Adapter
**Imports:** os, time, typing, .base
### Class `MistralLLMClient` (`BaseLLM`)
Mistral AI LLM client using the official Mistral SDK.
Methods:
- `__init__(self, api_key: Optional[str]=None, **kwargs)`
- `provider_type(self)`
- `default_model(self)`
- `_initialize_client(self)`
- `_convert_config(self, config: Optional[GenerationConfig])`
- `generate(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `generate_stream(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `list_models(self)`


## `api/openai_client.py`
OpenAI LLM Client Adapter
**Imports:** os, time, typing, .base
### Class `OpenAILLMClient` (`BaseLLM`)
OpenAI LLM client using the official OpenAI Python SDK.
Methods:
- `__init__(self, api_key: Optional[str]=None, **kwargs)` — Initialize OpenAI client.
- `provider_type(self)`
- `default_model(self)`
- `_initialize_client(self)` — Initialize the OpenAI client
- `_is_reasoning_model(self, model: str)` — Check if model is a reasoning model (o3, o3-mini, etc.)
- `_build_messages(self, prompt: str, system_instruction: Optional[str]=None, **kwargs)` — Build the messages array for the chat completion API.
- `_build_params(self, model: str, messages: List[Dict[str, Any]], config: Optional[GenerationConfig], stream: bool=False)` — Build API parameters from unified config
- `generate(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)` — Generate a response using OpenAI API.
- `generate_stream(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)` — Generate a streaming response.
- `async generate_async(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)` — Asynchronously generate a response using OpenAI API.
- `async generate_stream_async(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)` — Asynchronously generate a streaming response.
- `list_models(self)` — List available OpenAI models.
- `get_model_info(self, model_id: str)` — Get information about a specific model
- `count_tokens(self, text: str, model: Optional[str]=None)` — Count tokens using tiktoken if available.
- `is_available(self)` — Check if OpenAI provider is available


## `api/together_client.py`
Together AI LLM Client Adapter
**Imports:** os, time, typing, .base
### Class `TogetherLLMClient` (`BaseLLM`)
Together AI LLM client using the OpenAI-compatible API.
Methods:
- `__init__(self, api_key: Optional[str]=None, **kwargs)`
- `provider_type(self)`
- `default_model(self)`
- `_initialize_client(self)`
- `_convert_config(self, config: Optional[GenerationConfig])`
- `generate(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `generate_stream(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `list_models(self)`


## `api/usage_example.py`
Usage Examples for VEXIS Unified API
**Imports:** os, api
- `example_basic_generation()` — Example: Basic text generation with different providers
- `example_with_configuration()` — Example: Using generation configuration
- `example_streaming()` — Example: Streaming response
- `example_async_usage()` — Example: Async usage
- `example_list_models()` — Example: List available models
- `example_model_info()` — Example: Get specific model information
- `example_count_tokens()` — Example: Count tokens
- `example_factory_pattern()` — Example: Using the factory pattern directly
- `example_vision_input()` — Example: Vision/multimodal input (for supported models)
- `example_error_handling()` — Example: Proper error handling
- `example_json_mode()` — Example: JSON response format
- `example_provider_comparison()` — Example: Compare responses from different providers

## `api/xai_client.py`
xAI Grok LLM Client Adapter
**Imports:** os, time, typing, .base
### Class `XAILLMClient` (`BaseLLM`)
xAI Grok LLM client using the OpenAI-compatible API.
Methods:
- `__init__(self, api_key: Optional[str]=None, **kwargs)`
- `provider_type(self)`
- `default_model(self)`
- `_initialize_client(self)`
- `_convert_config(self, config: Optional[GenerationConfig])`
- `generate(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `generate_stream(self, prompt: str, config: Optional[GenerationConfig]=None, model: Optional[str]=None, **kwargs)`
- `list_models(self)` — Return empty list - model validation happens at API call time


## `api/zhipuai_client.py`
ZhipuAI (Z.AI) LLM Client Adapter
**Imports:** os, time, typing, .base
### Class `ZhipuAILLMClient` (`BaseLLM`)
ZhipuAI (Z.AI) LLM client using OpenAI-compatible SDK.
Methods:
- `__init__(self, api_key: Optional[str]=None, **kwargs)` — Initialize ZhipuAI client
- `provider_type(self)` — Return the provider type
- `default_model(self)` — Return the default model for ZhipuAI
- `_initialize_client(self)` — Initialize the OpenAI-compatible client for ZhipuAI
- `get_model_info(self, model: Optional[str]=None)` — Get information about a specific model
- `generate(self, prompt: str, config: Optional[GenerationConfig]=None, **kwargs)` — Generate a response from ZhipuAI model.
- `generate_stream(self, prompt: str, config: Optional[GenerationConfig]=None, **kwargs)` — Generate a streaming response from ZhipuAI model.
- `async generate_async(self, prompt: str, config: Optional[GenerationConfig]=None, **kwargs)` — Generate an asynchronous response from ZhipuAI model.
- `async generate_stream_async(self, prompt: str, config: Optional[GenerationConfig]=None, **kwargs)` — Asynchronously generate a streaming response from ZhipuAI model.
- `list_models(self)` — List available ZhipuAI models.


## `check_environment.py`
Standalone Environment Check Script for VEXIS-CLI Usage: python3 check_environment.py [--fix]
**Imports:** sys, os, ai_agent.utils.environment_detector
- `main()`

## `check_models.py`
Model Availability Checker for VEXIS-CLI Checks if required models are available and provides helpful guidance
**Imports:** subprocess, sys, json, typing, pathlib
### Class `ModelChecker` (`object`)
Check availability of AI models
Methods:
- `__init__(self)`
- `_check_ollama_installation(self)` — Check if Ollama is installed
- `_get_available_models(self)` — Get list of available Ollama models
- `check_model(self, model_name: str)` — Check if a specific model is available
- `_get_model_suggestions(self, model_name: str)` — Get suggestions for missing models
- `get_status_report(self)` — Get comprehensive status report

- `main()` — Main function for standalone usage

## `example_usage.py`
Example usage of the hierarchical Ollama model selection
- `example_usage()` — Example of how to use the hierarchical model selection

## `manage_sdks.py`
VEXIS-CLI SDK Management Tool
**Imports:** sys, argparse, pathlib
- `show_status()` — Show SDK installation status for all providers
- `install_sdks(providers=None, interactive=True)` — Install missing SDKs
- `test_providers()` — Test provider initialization after SDK installation
- `main()` — Main CLI interface

## `run.py`
Ultimate Zero-Configuration AI Agent Runner Usage: python3 run.py "your instruction here"
**Imports:** sys, os, subprocess, platform, shutil, pathlib, typing
- `_get_api_key_for_provider(provider: Optional[str])` — Return the active API key for a provider without prompting the user.
- `_restore_restart_settings_from_env()` — Hydrate in-memory settings from /restart environment overrides.
- `restart_with_current_settings(selected_mode: str, selected_provider: Optional[str], selected_model: Optional[str], debug_mode: bool=False, max_iterations: Optional[int]=None)` — Replace the current process while preserving runtime provider/model/API settings.
- `is_in_virtual_environment()` — Check if currently running in a virtual environment
- `get_venv_python_path()` — Get the Python executable path in the virtual environment
- `check_venv_prerequisites()` — Check if virtual environment creation prerequisites are met
- `create_virtual_environment()` — Create a virtual environment with robust error handling
- `restart_in_venv()` — Restart the current script in the virtual environment with robust error handling
- `install_dependencies()` — Install all dependencies in the virtual environment with enhanced error handling
- `bootstrap_environment()` — Bootstrap the environment - create venv and install dependencies
- `show_help()` — Show help message
- `check_ollama_login_with_fallback()` — Check Ollama login with version-aware fallback
- `run_environment_check(fix_mode=False)` — Run environment detection and optionally fix issues
- `update_ollama()` — Update Ollama to latest version
- `prompt_for_google_api_key()` — Prompt user for Google API key and handle saving
- `select_google_model()` — Prompt user to select Google model using curses arrow keys
- `show_config_summary(provider: str, model: str=None)` — Display a clean configuration summary
- `format_model_display_name(provider: str, model: str)` — Format model names for better display
- `configure_google_provider()` — Configure Google provider with API key and model selection
- `ensure_ollama_model_available(model_name: str)` — Ensure the specified Ollama model is available locally, pull if necessary
- `configure_ollama_provider()` — Configure Ollama provider with model selection
- `select_execution_mode()` — Select execution mode (Normal or Telegram) using curses arrow keys
- `select_model_provider(_recursion_depth: int=0)` — Main configuration screen for model provider selection using curses arrow keys
- `configure_generic_provider(provider_name)` — Generic configuration for cloud providers with arrow key model selection
- `get_custom_model_name()` — Get custom model name from user for OpenRouter
- `select_model_with_arrows(provider_name: str, models: list)` — Select model using arrow keys in a curses menu with categorization
- `select_openai_model_with_categories(models: list)` — Select OpenAI model using categorized menu
- `get_model_description(model: str)` — Get description for a specific model
- `show_models_in_category(category_name: str, models: list, category_icon: str)` — Show models within a specific category with sub-categorization
- `show_models_with_subcategories(category_name: str, models: list, category_icon: str)` — Show models with subcategories for Legacy Models
- `show_o_series_subcategories(models: list)` — Show O Series models subdivided by generation
- `show_gpt_series_subcategories(models: list)` — Show GPT Series models subdivided by generation
- `get_valid_api_key(prompt)` — Get and validate API key from user input
- `main()` — Main entry point

## `src/ai_agent/__init__.py`
VEXIS-CLI-3 - Optimized 5-Phase AI Agent System for Terminal Automation
**Imports:** .core_processing.five_phase_engine, .platform_abstraction.platform_detector, .external_integration.vision_api_client, .external_integration.model_runner
No top-level classes or functions; this module consists of constants, package exports, script logic, or registration side effects.

## `src/ai_agent/core_processing/__init__.py`
Core Processing Layer for AI Agent System 5-Phase Architecture: Command Suggestion → Extraction → Execution → Evaluation → Summary
**Imports:** .command_parser, .five_phase_engine
No top-level classes or functions; this module consists of constants, package exports, script logic, or registration side effects.

## `src/ai_agent/core_processing/command_output.py`
Command Output System for CLI Execution Engine Handles reasoning output and command formatting according to specifications: 1. Output reasoning first 2. Output specific target for command execution 3. Output CLI command (second-to-last line) 4. Output save command (final line)
**Imports:** time, typing, dataclasses, ..utils.logger, .terminal_history
### Class `CommandOutput` (`object`)
Structure for formatted command output
### Class `CommandOutputFormatter` (`object`)
Formats command output according to specifications: 1. Reasoning about the action 2. Specific target for command execution 3. CLI command (second-to-last line) 4. Terminal log display (final line)
Methods:
- `__init__(self)`
- `format_command_output(self, reasoning: str, target: str, command: str, terminal_content: str, coordinates: Optional[Tuple[float, float]]=None, **kwargs)` — Format command output according to specifications
- `format_failure_output(self, reasoning: str, target: str, command: str, error_message: str, coordinates: Optional[Tuple[float, float]]=None, **kwargs)` — Format a failure output with reasoning and target
- `format_extraction_output(self, reasoning: str, target: str, extracted_info: Dict[str, Any], terminal_content: Optional[str]=None, **kwargs)` — Format an extraction output with reasoning and target

- `get_command_formatter()` — Get global command formatter instance
- `format_command_output(reasoning: str, target: str, command: str, terminal_content: str, **kwargs)` — Global function to format any command with reasoning and target

## `src/ai_agent/core_processing/command_parser.py`
Command Parser for CLI AI Agent System CLI Architecture: Standard Linux/Unix Command Processing
**Imports:** re, subprocess, typing, dataclasses, enum, ..external_integration.model_runner
### Class `CommandParsingError` (`Exception`)
Simple command parsing error
### Class `ValidationError` (`Exception`)
Simple validation error
### Class `CommandType` (`Enum`)
Command set for CLI Architecture
### Class `ParsedCommand` (`object`)
Parsed command structure
### Class `CommandParser` (`object`)
Command parser for CLI Architecture with standard Linux/Unix command processing
Methods:
- `__init__(self)`
- `_initialize_cli_command_patterns(self)` — Initialize CLI command patterns
- `parse_command(self, command_text: str, previous_output: Optional[str]=None, context: Optional[Dict[str, Any]]=None)` — Parse command text into structured command
- `_clean_command_text(self, command_text: str)` — Clean and normalize command text
- `_parse_with_patterns(self, command_text: str)` — Parse command using regex patterns
- `_create_command_from_match(self, command_type: CommandType, match: re.Match, raw_text: str)` — Create parsed command from regex match


## `src/ai_agent/core_processing/five_phase_engine.py`
Optimized 6-Phase Pipeline Execution Engine for VEXIS-CLI V3
**Imports:** os, re, time, platform, threading, typing, dataclasses, enum, pathlib, ..external_integration.model_runner, ..external_integration.telegram_bot, ..utils.exceptions, ..utils.logger, .terminal_history
### Class `PipelineCancelledError` (`Exception`)
Raised when a newer user request cancels the active pipeline.
### Class `PipelinePhase` (`Enum`)
Optimized 6-Phase Pipeline phases for V3
### Class `PipelineContext` (`object`)
Context for tracking Optimized 5-Phase Pipeline execution (V3)
### Class `FivePhaseEngine` (`object`)
Optimized 6-Phase Pipeline Execution Engine (V3)
Methods:
- `__init__(self, provider: str=None, model: str=None, config: Optional[Dict[str, Any]]=None, telegram_bot: Optional[TelegramBotManager]=None)`
- `request_cancel(self)` — Request cancellation of the active pipeline and foreground command.
- `execute_instruction(self, user_prompt: str, conversation_history: Optional[ConversationHistory]=None, telegram_mode: bool=False, telegram_user_id: Optional[int]=None, cancel_event: Optional[threading.Event]=None)` — Execute user instruction through the Optimized 6-Phase Pipeline (V3)
- `_raise_if_cancelled(self, context: PipelineContext)`
- `_run_phase1(self, context: PipelineContext)` — Phase 1: Initial Planning
- `_run_phase2(self, context: PipelineContext)` — Phase 2: Action Generation
- `_run_phase3(self, context: PipelineContext)` — Phase 3: Execution
- `_run_phase4(self, context: PipelineContext)` — Phase 4: Dynamic Update & Progress Reporting (Most Critical Phase)
- `_run_phase5(self, context: PipelineContext)` — Phase 5: Verification
- `_run_phase6(self, context: PipelineContext)` — Phase 6: Summarization
- `_parse_vexis_commands(self, text: str)` — Parse VEXIS commands from LLM output.
- `_send_telegram_message_sync(self, user_id: int, message: str)`
- `_send_phase_error_telegram(self, context: PipelineContext, phase_num: str, phase_name: str)`
- `_send_timeout_telegram(self, context: PipelineContext, elapsed: float)`
- `_extract_code_block(self, text: str)` — Extract code block from text using regex (100% programmatic, zero LLM).
- `_has_code_block(self, text: str)` — Check if text contains a code block
- `_remove_code_blocks(self, text: str)` — Remove code blocks from text, keeping only plain text.
- `_parse_commands(self, code_block: str)` — Parse commands from a code block (programmatic, zero LLM).
- `cleanup(self)`
- `__del__(self)`
- `_get_os_info(self)` — Get OS information for CLI context

- `get_five_phase_engine(config: Optional[Dict[str, Any]]=None)` — Get Optimized 5-Phase Pipeline Engine (V3) instance

## `src/ai_agent/core_processing/save_command.py`
Save Command Implementation for Phase 2: Execution Engine Implements the save() command system for work logging and reflection
**Imports:** json, time, typing, dataclasses, pathlib, enum, ..utils.logger, ..utils.exceptions
### Class `SaveContentType` (`Enum`)
Types of save content
### Class `SaveEntry` (`object`)
Individual save entry with work log information
### Class `WorkLog` (`object`)
Complete work log for a session
### Class `SaveCommand` (`object`)
save command Implementation for Phase 2: Execution Engine Implements the save() command system for work logging and reflection
Methods:
- `__init__(self, session_id: Optional[str]=None, log_dir: str='./work_logs')`
- `save(self, content: str, **kwargs)` — Main save command implementation
- `get_previous_save_content(self)` — Get content of immediately preceding save for reflection
- `get_previous_save_entry(self)` — Get complete entry of immediately preceding save
- `get_recent_saves(self, count: int=5)` — Get recent save entries for reflection
- `has_failures(self)` — Check if there are any failure entries in the work log
- `get_failure_coordinates(self)` — Get list of coordinates that failed to prevent repeated clicking
- `get_extracted_information(self)` — Get all extracted information from work log
- `_persist_work_log(self)` — Persist work log to disk
- `end_session(self)` — End the current session and finalize work log
- `load_session(self, session_id: str)` — Load a previous session for reflection

- `get_save_command()` — Get global save command instance
- `save(content: str, **kwargs)` — Global save function for easy use

## `src/ai_agent/core_processing/task_robustness_manager.py`
Task Robustness Manager for AI Agent System Ensures tasks execute completely through all steps without premature termination
**Imports:** time, typing, dataclasses, enum, ..utils.logger, ..utils.exceptions
### Class `TaskCompletionStatus` (`Enum`)
Task completion status levels
### Class `TaskProgress` (`object`)
Task progress tracking
### Class `RobustnessConfig` (`object`)
Configuration for robustness settings
### Class `TaskRobustnessManager` (`object`)
Manages task execution robustness to ensure complete step execution
Methods:
- `__init__(self, config: Optional[RobustnessConfig]=None)`
- `start_task_execution(self, task_description: str, estimated_steps: int=5)` — Initialize tracking for a new task execution
- `update_task_progress(self, task_id: str, command_description: str, completion_indicators: List[str]=None, missing_indicators: List[str]=None)` — Update progress for an active task
- `should_allow_task_completion(self, task_id: str, command_text: str)` — Determine if a task should be allowed to complete
- `_is_task_genuinely_complete(self, progress: TaskProgress, command_text: str)` — Analyze if a task is genuinely complete based on multiple indicators
- `_calculate_confidence_score(self, progress: TaskProgress)` — Calculate confidence score for task completion
- `get_task_status(self, task_id: str)` — Get current status of a task
- `should_continue_task_execution(self, task_id: str, command_count: int)` — Determine if task execution should continue
- `end_task_execution(self, task_id: str, final_status: TaskCompletionStatus)` — End task execution and return summary
- `get_active_task_summary(self)` — Get summary of all active tasks

- `get_task_robustness_manager(config: Optional[RobustnessConfig]=None)` — Get global task robustness manager instance

## `src/ai_agent/core_processing/terminal_history.py`
Terminal History System for CLI AI Agent System Replaces the Save command with terminal log display and history preservation OS-independent implementation with comprehensive error handling
**Imports:** json, time, os, subprocess, threading, shlex, platform, stat, signal, typing, dataclasses, pathlib, enum, contextlib, ..utils.logger, ..utils.exceptions
### Class `TerminalEntryType` (`Enum`)
Types of terminal entries
### Class `TerminalEntry` (`object`)
Individual terminal entry with command execution information
Methods:
- `to_dict(self)` — Convert to dictionary with proper serialization
- `from_dict(cls, data: Dict[str, Any])` — Create from dictionary with proper deserialization

### Class `TerminalSession` (`object`)
Complete terminal session for a work session
Methods:
- `to_dict(self)` — Convert to dictionary with proper serialization
- `from_dict(cls, data: Dict[str, Any])` — Create from dictionary with proper deserialization

### Class `TerminalHistory` (`object`)
Terminal History System that replaces Save command functionality Preserves terminal history and displays command outputs instead of Save content OS-independent implementation with comprehensive error handling
Methods:
- `__init__(self, session_id: Optional[str]=None, history_dir: Optional[Union[str, Path]]=None)` — Initialize terminal history system
- `_detect_shell(self)` — Detect the current shell for command execution
- `_ensure_history_directory(self)` — Ensure history directory exists with proper permissions
- `execute_command(self, command: str, timeout: Optional[int]=None)` — Execute a CLI command and preserve its output in history
- `get_recent_output(self, count: int=10)` — Get recent terminal entries (commands, outputs, and errors) for context
- `get_command_history(self, count: int=10)` — Get recent command entries
- `get_current_working_directory(self)` — Get current working directory as Path object
- `_execute_subprocess_command(self, command: str, timeout: int)` — Execute command using subprocess with platform-specific handling (shell=False for security)
- `_handle_cd_command(self, command: str, start_time: float)` — Handle cd commands without using subprocess to maintain proper directory state
- `_handle_cd_dash_command(self, command: str, start_time: float)` — Handle cd - command (go to previous directory)
- `_handle_cd_home_command(self, command: str, start_time: float)` — Handle cd command with no arguments (go to home directory)
- `display_terminal_log(self, max_entries: int=20)` — Generate formatted terminal log display showing only commands and their outputs
- `get_last_command_output(self)` — Get the output of the most recent command
- `_persist_history(self)` — Persist terminal history to disk with comprehensive error handling
- `end_session(self)` — End the current session and finalize history
- `clear_session(self)` — Clear the current terminal session (reset terminal logs)
- `load_session(self, session_id: str)` — Load a previous session for context
- `list_sessions(self)` — List all available session IDs
- `cleanup_old_sessions(self, max_sessions: int=100)` — Clean up old session files, keeping only the most recent ones
- `temporary_directory(self, target_dir: Optional[Union[str, Path]]=None)` — Context manager for temporarily changing directory
- `cancel_current_command(self)` — Terminate the currently running foreground command batch, if any.
- `execute_commands_batch(self, commands: List[str], timeout: Optional[int]=None, cancel_event=None)` — Execute multiple commands in a single batch using the same terminal session.
- `_execute_batch_subprocess(self, commands: List[str], timeout: int, cancel_event=None)` — Execute multiple commands in a single subprocess batch with inactivity-based timeout.
- `_is_background_command(self, command: str)` — Return True when a command explicitly requests background execution.
- `_detach_background_command(self, command: str)` — Detach an explicit background command so it survives batch shell exit.
- `_terminate_process_tree(self, process)` — Terminate the batch process and its foreground children.

- `get_terminal_history()` — Get global terminal history instance
- `execute_command(command: str, timeout: Optional[int]=None)` — Global function to execute command and preserve history
- `display_terminal_log(max_entries: int=20)` — Global function to display terminal log
- `get_last_command_output()` — Global function to get last command output

## `src/ai_agent/external_integration/__init__.py`
External Integration Layer for AI Agent System Vision API client and model runner for AI communication
**Imports:** .ollama_provider, .model_runner
No top-level classes or functions; this module consists of constants, package exports, script logic, or registration side effects.

## `src/ai_agent/external_integration/google_provider.py`
Google API Provider for VEXIS-1.1 AI Agent Handles communication with Google Gemini API
**Imports:** base64, io, json, time, uuid, typing, dataclasses, .vision_api_client, ..utils.exceptions, ..utils.logger
### Class `GoogleProvider` (`BaseAPIProvider`)
Google Gemini API provider
Methods:
- `__init__(self, config: Dict[str, Any])`
- `name(self)`
- `default_model(self)`
- `analyze_image(self, request: APIRequest)` — Analyze image using Google Gemini API
- `_calculate_cost(self, model: str, tokens: Optional[int]=None)` — Calculate cost for Google Gemini API


## `src/ai_agent/external_integration/model_runner.py`
Model Runner for VEXIS-CLI V3 AI Agent System Optimized 5-Phase Architecture: Initial Planning -> Action Generation -> Execution -> Dynamic Update -> Summarization Multi-Provider Support: 13+ AI providers available
**Imports:** time, typing, dataclasses, enum, .multi_provider_vision_client, ..utils.exceptions, ..utils.logger, ..utils.config
### Class `TaskType` (`Enum`)
Task types for V3 Optimized 5-Phase Architecture
### Class `ModelRequest` (`object`)
Model request structure
### Class `ModelResponse` (`object`)
Model response structure
### Class `PromptTemplate` (`object`)
Prompt template manager for V3 Optimized 5-Phase Architecture
Methods:
- `__init__(self)`
- `_load_templates(self)` — Load prompt templates for V3 Optimized 5-Phase Architecture
- `get_template(self, task_type: TaskType)` — Get template for task type

### Class `ModelRunner` (`object`)
V3 Optimized 5-Phase Architecture Model Runner
Methods:
- `__init__(self, provider: str=None, model: str=None, config: Optional[Dict[str, Any]]=None, auto_install_sdks: bool=False)`
- `run_model(self, request: ModelRequest)` — Run AI model for V3 Optimized 5-Phase Architecture with retry on validation failure
- `_validate_request(self, request: ModelRequest)` — Validate model request
- `_format_prompt(self, request: ModelRequest)` — Format prompt based on task type and context
- `_validate_output_format(self, content: str, task_type: TaskType)` — Validate that the output matches the expected format for the task type (V3)
- `_get_system_instructions(self, task_type: TaskType)` — Get system instructions for V3 Optimized 5-Phase Architecture
- `install_missing_sdks(self, providers: Optional[List[str]]=None, interactive: bool=True)` — Install missing SDKs for specified providers
- `show_sdk_status(self, providers: Optional[List[str]]=None)` — Show SDK installation status

- `get_model_runner(provider: str=None, model: str=None)` — Get model runner instance with optional provider and model

## `src/ai_agent/external_integration/multi_provider_vision_client.py`
Multi-Provider Vision API Client for AI Agent System Supports 13+ AI providers while maintaining current architecture
**Imports:** io, time, typing, dataclasses, enum, ..utils.exceptions, ..utils.logger, ..utils.config, .ollama_provider, .openrouter_provider
### Class `APIProvider` (`Enum`)
Supported API providers - Extended to 13+ providers
### Class `APIResponse` (`object`)
API response structure
### Class `APIRequest` (`object`)
API request structure
### Class `MultiProviderVisionAPIClient` (`object`)
Multi-provider Vision API Client
Methods:
- `__init__(self, config: Optional[Dict[str, Any]]=None, auto_install_sdks: bool=False)`
- `_initialize_api_clients(self)` — Initialize all available API clients with API keys from settings
- `_offer_sdk_installation(self, provider: str)` — Offer to install SDK for a missing provider - disabled to avoid noise
- `generate_response(self, request: APIRequest)` — Generate response using specified or preferred provider
- `_handle_ollama_request(self, request: APIRequest, start_time: float)` — Handle Ollama requests
- `_handle_openrouter_request(self, request: APIRequest, start_time: float)` — Handle OpenRouter requests
- `_handle_api_request(self, request: APIRequest, provider: str, start_time: float)` — Handle multi-provider API requests
- `_prepare_vision_prompt(self, request: APIRequest)` — Prepare prompt for vision models
- `get_available_providers(self)` — Get list of actually available providers (with SDK dependencies installed)
- `install_missing_sdks(self, providers: Optional[List[str]]=None, interactive: bool=True)` — Install missing SDKs for specified providers or all providers
- `show_sdk_status(self, providers: Optional[List[str]]=None)` — Show SDK installation status
- `get_provider_models(self, provider: str)` — Get available models for a provider

- `create_vision_api_client(config: Optional[Dict[str, Any]]=None, auto_install_sdks: bool=False)` — Create a vision API client instance

## `src/ai_agent/external_integration/ollama_provider.py`
Simplified Ollama Provider for VEXIS-CLI Direct API calls to Ollama - no magic, no auto-fixes
**Imports:** requests, json, typing, dataclasses, ..utils.logger
### Class `OllamaResponse` (`object`)
Simple Ollama response
### Class `SimpleOllamaProvider` (`object`)
Simple Ollama provider that just calls the API. No auto-signin, no complex error handling.
Methods:
- `__init__(self, endpoint: str='http://localhost:11434', timeout: int=120)`
- `chat(self, prompt: str, model: Optional[str]=None, temperature: float=1.0, max_tokens: int=5000, system_instructions: Optional[str]=None)` — Send a chat request to Ollama.
- `_get_cloud_alternatives(self, cloud_model: str)` — Get local model alternatives for cloud models
- `is_available(self)` — Check if Ollama is running


## `src/ai_agent/external_integration/openrouter_provider.py`
OpenRouter API Provider for VEXIS-CLI-3 AI Agent Handles communication with OpenRouter API - provides access to 300+ AI models
**Imports:** base64, io, json, time, uuid, typing, dataclasses, ..utils.exceptions, ..utils.logger
### Class `OpenRouterResponse` (`object`)
OpenRouter response structure
### Class `OpenRouterProvider` (`object`)
OpenRouter API provider - access to 300+ AI models
Methods:
- `__init__(self, config: Dict[str, Any])`
- `_get_api_key(self)` — Get API key from config or settings manager
- `name(self)`
- `default_model(self)`
- `get_available_models(self)` — Get list of available models
- `chat(self, prompt: str, model: Optional[str]=None, temperature: float=1.0, max_tokens: int=5000, system_instructions: Optional[str]=None, image_data: Optional[bytes]=None, image_format: str='PNG')` — Send a chat request to OpenRouter
- `analyze_image(self, request)` — Analyze image using OpenRouter API - compatibility wrapper
- `_calculate_cost(self, model: str, tokens: Optional[int]=None)` — Calculate cost for OpenRouter API
- `validate_model(self, model: str)` — Validate if model name is supported
- `get_model_info(self, model: str)` — Get information about a specific model
- `_estimate_context_window(self, model: str)` — Estimate context window for model


## `src/ai_agent/external_integration/telegram_bot.py`
Telegram Bot Integration for VEXIS-CLI-3 AI Agent Handles Telegram bot communication and message management
**Imports:** asyncio, inspect, threading, time, typing, dataclasses, enum, json, pathlib, functools, ..utils.logger, ..utils.config
- `retry_on_network_error(max_retries: int=3, initial_delay: float=1.0, backoff_factor: float=2.0)` — Decorator to retry network operations with exponential backoff.
### Class `TelegramMode` (`Enum`)
Telegram bot mode
### Class `ConversationHistory` (`object`)
Conversation history for Telegram mode
Methods:
- `add_message(self, role: str, content: str)` — Add a message to the conversation history
- `add_completed_task(self, task_prompt: str, steps: List[str], summary: str='')` — Record a completed task with its step list.
- `get_history(self)` — Get the conversation history
- `clear(self)` — Clear the conversation history
- `format_for_prompt(self)` — Format conversation history for inclusion in prompts.

### Class `QueuedTelegramMessage` (`object`)
Telegram message waiting to be sent from the queue processor.
### Class `RunningTelegramTask` (`object`)
A Telegram pipeline task plus the cancellation event passed to it.
### Class `TelegramBotManager` (`object`)
Manages Telegram bot integration for AI agent
Methods:
- `__init__(self, bot_token: str, allowed_user_ids: Optional[List[int]]=None, max_history_length: int=50, terminal_history=None)`
- `set_message_callback(self, callback: Callable[[str, int], str])` — Set the callback function for processing messages
- `set_restart_callback(self, callback: Callable[[int], None])` — Set the callback function used by the /restart command.
- `get_conversation_history(self, user_id: int)` — Get or create conversation history for a user
- `clear_conversation_history(self, user_id: int)` — Clear conversation history for a user
- `async start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE)` — Handle /start command
- `async reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE)` — Handle /reset command
- `async restart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE)` — Handle /restart command
- `async help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE)` — Handle /help command
- `async _cancel_user_task(self, user_id: int)` — Signal any running task for the specified user to stop.
- `async _process_message_async(self, user_message: str, user_id: int, processing_msg, history, cancel_event: threading.Event)` — Process message asynchronously with cancellation support.
- `async handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE)` — Handle incoming messages without letting earlier background work block the bot.
- `async _handle_message_task(self, user_id: int, user_message: str, processing_msg, history, cancel_event: threading.Event)` — Actual message processing task that can be cancelled
- `_is_user_allowed(self, user_id: int)` — Check if user is allowed to use the bot
- `_truncate_message(self, message: str, max_length: int=4000)` — Truncate message if it exceeds max length, adding [omitted] in the middle.
- `async send_message(self, chat_id: int, message: str)` — Send a message to a specific chat
- `queue_message(self, chat_id: int, message: str)` — Queue a message to be sent from the async event loop.
- `async process_message_queue(self)` — Process currently-sendable queued messages once and return.
- `_pop_sendable_messages(self)` — Pop messages that are due to be sent, leaving delayed retries queued.
- `async _send_queued_message(self, queued_message: QueuedTelegramMessage)` — Send a queued message once, re-queueing with a bounded retry budget.
- `_start_queue_processor(self)` — Start background thread to process message queue
- `_stop_queue_processor(self)` — Stop background queue processor
- `start_bot(self)` — Start the Telegram bot (blocking)
- `async _stop_application(self)` — Internal method to stop the application from async context.
- `stop_bot(self)` — Stop the Telegram bot gracefully

- `create_telegram_bot(config_path: Optional[str]=None, terminal_history=None)` — Create a Telegram bot manager from configuration

## `src/ai_agent/external_integration/vision_api_client.py`
Vision API Client for AI Agent System Simplified: Ollama Cloud Models only
**Imports:** io, time, typing, dataclasses, enum, ..utils.exceptions, ..utils.logger, ..utils.config, .ollama_provider
### Class `APIProvider` (`Enum`)
Supported API providers
### Class `APIResponse` (`object`)
API response structure
### Class `APIRequest` (`object`)
API request structure
### Class `VisionAPIClient` (`object`)
Vision API client with Ollama and Google support
Methods:
- `__init__(self, config: Optional[Dict[str, Any]]=None)`
- `analyze_image(self, request: APIRequest)` — Analyze image using the specified or current provider
- `_call_ollama(self, request: APIRequest)` — Call Ollama provider
- `_call_google(self, request: APIRequest)` — Call Google provider
- `_validate_request(self, request: APIRequest)` — Validate API request
- `get_available_providers(self)` — Get list of available providers
- `is_ollama_available(self)` — Check if Ollama is available


## `src/ai_agent/platform_abstraction/__init__.py`
Platform Abstraction Layer for CLI AI Agent System Cross-platform detection and system information
**Imports:** .platform_detector
No top-level classes or functions; this module consists of constants, package exports, script logic, or registration side effects.

## `src/ai_agent/platform_abstraction/platform_detector.py`
Platform detection and system information Zero-defect policy: comprehensive platform detection with fallbacks
**Imports:** platform, sys, os, subprocess, typing, dataclasses, ..utils.exceptions, ..utils.logger
### Class `SystemInfo` (`object`)
System information structure
### Class `PlatformDetector` (`object`)
Comprehensive platform detection with fallback mechanisms
Methods:
- `__init__(self)`
- `detect_system(self)` — Detect complete system information
- `_perform_detection(self)` — Perform comprehensive system detection
- `_detect_os(self)` — Detect operating system and version
- `_detect_architecture(self)` — Detect system architecture
- `_detect_platform(self)` — Detect platform type
- `_detect_python_version(self)` — Detect Python version
- `_detect_screen_resolution(self)` — Detect screen resolution
- `_detect_screen_resolution_macos(self)` — Detect screen resolution on macOS
- `_detect_screen_resolution_windows(self)` — Detect screen resolution on Windows
- `_detect_screen_resolution_linux(self)` — Detect screen resolution on Linux
- `_detect_scale_factor(self)` — Detect display scale factor
- `_detect_scale_factor_macos(self)` — Detect scale factor on macOS
- `_detect_scale_factor_windows(self)` — Detect scale factor on Windows
- `_detect_scale_factor_linux(self)` — Detect scale factor on Linux
- `_detect_display_count(self)` — Detect number of displays
- `_detect_display_count_macos(self)` — Detect display count on macOS
- `_detect_display_count_windows(self)` — Detect display count on Windows
- `_detect_display_count_linux(self)` — Detect display count on Linux
- `_detect_headless(self)` — Detect if running in headless mode
- `_detect_container(self)` — Detect if running in a container
- `_detect_virtual_machine(self)` — Detect if running in a virtual machine
- `get_platform_specific_config(self)` — Get platform-specific configuration

- `get_platform_detector()` — Get global platform detector instance
- `get_system_info()` — Get system information

## `src/ai_agent/plugins/__init__.py`
Plugin System for VEXIS-CLI Extensible architecture using pluggy
**Imports:** pluggy
### Class `VexisHooks` (`object`)
Hook specifications for VEXIS-CLI plugins
Methods:
- `vexis_initialize(self, config: dict)` — Called when VEXIS initializes
- `vexis_pre_execute(self, command: str, context: dict)` — Called before executing a terminal command
- `vexis_post_execute(self, command: str, result: dict, context: dict)` — Called after executing a terminal command
- `vexis_pre_phase(self, phase: str, context: dict)` — Called before starting a pipeline phase
- `vexis_post_phase(self, phase: str, result: dict, context: dict)` — Called after completing a pipeline phase
- `vexis_pre_request(self, request: dict, provider: str, model: str)` — Called before making an API request
- `vexis_post_response(self, response: dict, provider: str, model: str)` — Called after receiving an API response
- `vexis_on_error(self, error: Exception, context: dict)` — Called when an error occurs
- `vexis_get_commands(self)` — Return custom CLI commands to register
- `vexis_get_providers(self)` — Return custom AI providers to register

### Class `PluginManager` (`object`)
Manages plugin lifecycle and hook execution
Methods:
- `__init__(self)`
- `register_plugin(self, plugin)` — Register a plugin module or class
- `unregister_plugin(self, plugin)` — Unregister a plugin
- `discover_plugins(self, entry_points_group: str='vexis.plugins')` — Discover and load plugins from entry points
- `get_hook_caller(self)` — Get the hook caller for invoking hooks
- `list_plugins(self)` — List registered plugins

- `get_plugin_manager()` — Get or create global plugin manager
- `initialize_plugins(config: dict=None)` — Initialize and discover plugins

## `src/ai_agent/plugins/example_plugin.py`
Example plugin demonstrating the VEXIS plugin system
**Imports:** .
### Class `ExamplePlugin` (`object`)
Example plugin that logs all commands and responses
Methods:
- `__init__(self)`
- `vexis_initialize(self, config: dict)` — Called when VEXIS initializes
- `vexis_pre_execute(self, command: str, context: dict)` — Log commands before execution
- `vexis_post_execute(self, command: str, result: dict, context: dict)` — Log results after execution
- `vexis_pre_phase(self, phase: str, context: dict)` — Log phase start
- `vexis_on_error(self, error: Exception, context: dict)` — Log errors
- `vexis_get_commands(self)` — Register custom commands
- `show_stats(self)` — Show plugin statistics


## `src/ai_agent/user_interface/__init__.py`
User Interface Layer for AI Agent System 5-Phase Architecture: Five-phase application entry point
**Imports:** .five_phase_app
No top-level classes or functions; this module consists of constants, package exports, script logic, or registration side effects.

## `src/ai_agent/user_interface/five_phase_app.py`
Optimized 5-Phase Pipeline Application Entry Point for VEXIS-CLI V3 Implements the lean 5-phase architecture: Initial Planning -> Action Generation -> Execution -> Dynamic Update -> Summarization
**Imports:** sys, argparse, time, signal, typing, pathlib, ..core_processing.five_phase_engine, ..utils.exceptions, ..utils.logger, ..utils.config
### Class `FivePhaseAIAgent` (`object`)
Optimized 5-Phase Pipeline AI Agent (V3) implementing the lean architecture
Methods:
- `__init__(self, provider: str=None, model: str=None, config_path: Optional[str]=None, telegram_bot=None)`
- `_build_engine_config(self)` — Build engine config from config.yaml
- `_apply_runtime_options(self, options: Dict[str, Any])` — Apply CLI/runtime options to the already-created engine.
- `run(self, instruction: str, options: Dict[str, Any], conversation_history=None, cancel_event=None)` — Run AI Agent with instruction using Optimized 5-Phase Pipeline (V3)
- `_print_results(self, context, instruction: str, success: bool)` — Print execution results to console
- `_save_results(self, context, output_file: str)` — Save execution results to file
- `_signal_handler(self, signum, frame)` — Handle shutdown signals
- `shutdown(self)` — Shutdown AI Agent

- `create_five_phase_argument_parser()` — Create V3 Optimized 5-Phase command line argument parser
- `validate_arguments(args: argparse.Namespace)` — Validate command line arguments
- `main()` — Main entry point for V3 Optimized 5-Phase Pipeline AI Agent

## `src/ai_agent/utils/__init__.py`
Utility functions for AI Agent System
**Imports:** .logger, .config, .exceptions, .dependency_checker
No top-level classes or functions; this module consists of constants, package exports, script logic, or registration side effects.

## `src/ai_agent/utils/config.py`
Configuration management for AI Agent System Zero-defect policy: comprehensive configuration with validation
**Imports:** os, yaml, json, typing, pathlib, dataclasses, .exceptions
- `_get_ollama_model_from_settings()` — Get the Ollama model from settings manager, with fallback to default
### Class `LoggingConfig` (`object`)
Logging configuration
### Class `APIConfig` (`object`)
API configuration
### Class `SecurityConfig` (`object`)
Security configuration
### Class `PerformanceConfig` (`object`)
Performance configuration
### Class `EngineConfig` (`object`)
Five-phase engine configuration
### Class `TelegramConfig` (`object`)
Telegram bot configuration
### Class `ExecutionConfig` (`object`)
Execution mode configuration
### Class `CacheConfig` (`object`)
Cache configuration
### Class `CostConfig` (`object`)
Cost management configuration
### Class `UserConfig` (`object`)
User preferences configuration
### Class `Config` (`object`)
Main configuration class
Methods:
- `get(self, key: str, default: Any=None)` — Get configuration value by dot notation key

### Class `ConfigManager` (`object`)
Configuration manager with validation and environment support
Methods:
- `__init__(self, config_path: Optional[Union[str, Path]]=None)`
- `load_config(self)` — Load configuration from file and environment
- `_load_raw_config(self)` — Load raw configuration from file
- `_merge_config(self, base: Dict[str, Any], override: Dict[str, Any])` — Recursively merge configuration dictionaries
- `_load_from_environment(self)` — Load configuration from environment variables
- `_create_config_from_raw(self)` — Create Config object from raw configuration
- `_validate_config(self)` — Validate configuration
- `save_config(self, config_path: Optional[Union[str, Path]]=None)` — Save configuration is disabled - settings are not persisted
- `get(self, key: str, default: Any=None)` — Get configuration value by dot notation key
- `set(self, key: str, value: Any)` — Set configuration value by dot notation key

- `load_config(config_path: Optional[Union[str, Path]]=None, force_reload: bool=False)` — Load configuration (singleton pattern)
- `get_config_manager()` — Get global config manager instance
- `save_config(config_path: Optional[Union[str, Path]]=None)` — Save configuration is disabled - settings are not persisted

## `src/ai_agent/utils/cost_manager.py`
Cost Manager for VEXIS-CLI Tracks and manages API usage costs with budget controls
**Imports:** time, json, typing, dataclasses, pathlib, threading, enum, .logger
### Class `BudgetAlertLevel` (`Enum`)
Budget alert levels
### Class `ModelPricing` (`object`)
Pricing information for a model
### Class `UsageRecord` (`object`)
Single usage record
### Class `BudgetConfig` (`object`)
Budget configuration
### Class `CostStats` (`object`)
Cost statistics
### Class `CostManager` (`object`)
Manages API usage costs and budget enforcement
Methods:
- `__init__(self, config: Optional[BudgetConfig]=None, persist_path: Optional[str]=None)`
- `estimate_cost(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int)` — Estimate cost for a request
- `record_usage(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int, task_type: str='unknown')` — Record actual usage and update statistics
- `check_budget(self, estimated_cost: float)` — Check if request is within budget
- `get_cheaper_alternative(self, provider: str, model: str, max_quality_degradation: str='minimal')` — Suggest a cheaper alternative model
- `get_budget_status(self)` — Get current budget status
- `get_usage_report(self, days: int=7)` — Get usage report for the last N days
- `_get_pricing(self, provider: str, model: str)` — Get pricing for a model
- `_check_quality_compatibility(self, original: str, alternative: str, max_degradation: str)` — Check if alternative model meets quality requirements
- `_check_budget_alerts(self)` — Check and log budget alerts
- `_get_alert_level(self, daily_spent: float, monthly_spent: float)` — Determine alert level based on spending
- `_save_to_disk(self)` — Persist cost data to disk
- `_load_from_disk(self)` — Load persisted cost data

- `get_cost_manager(daily_budget: Optional[float]=None, monthly_budget: Optional[float]=None)` — Get global cost manager instance
- `estimate_request_cost(provider: str, model: str, prompt_tokens: int, completion_tokens: int)` — Convenience function to estimate cost

## `src/ai_agent/utils/curses_menu.py`
Curses-based Arrow Key Menu System Proper arrow key navigation without number fallbacks Works in any terminal that supports curses
**Imports:** curses, os, typing, .model_definitions
### Class `CursesMenu` (`object`)
Curses-based interactive menu with arrow key navigation
Methods:
- `__init__(self, title: str, description: str='')`
- `add_item(self, display_name: str, description: str, value: Any, icon: str='📋')` — Add an item to the menu
- `run(self, stdscr)` — Run the menu and return selected value
- `show(self)` — Show the menu (entry point)

### Class `CursesHierarchicalMenu` (`object`)
Curses-based hierarchical menu for model selection - single session
Methods:
- `__init__(self)`
- `run(self, stdscr)` — Run hierarchical selection in single curses session
- `_get_custom_model_input(self, stdscr)` — Get custom model name input from user
- `_show_family_selection(self, stdscr)` — Show family selection screen
- `_show_subfamily_selection(self, stdscr, family_key: str)` — Show subfamily selection screen
- `_show_model_selection(self, stdscr, family_key: str, subfamily_key: str)` — Show model selection screen
- `show(self)` — Show the hierarchical menu

- `get_curses_menu(title: str, description: str='')` — Get a curses-based menu
- `get_curses_hierarchical_menu()` — Get a curses-based hierarchical menu
- `success_message(message: str)` — Display success message
- `error_message(message: str)` — Display error message
- `warning_message(message: str)` — Display warning message
- `test_curses_menu()` — Test the curses menu

## `src/ai_agent/utils/dependency_checker.py`
Dependency Checker and Auto-Installer Ensures all required dependencies are available before running the AI Agent
**Imports:** sys, subprocess, platform, importlib, os, time, socket, typing, pathlib
### Class `DependencyChecker` (`object`)
Comprehensive dependency checking and auto-installation system
Methods:
- `__init__(self, project_root: Path)`
- `check_python_version(self)` — Check if Python version meets requirements
- `check_pip_version(self)` — Check if pip is available and reasonably up-to-date
- `upgrade_pip(self)` — Upgrade pip to latest version
- `check_network_connectivity(self)` — Check if network connectivity is available with multiple fallbacks
- `check_virtual_env(self)` — Check if running in virtual environment
- `get_venv_python_executable(self)` — Get the Python executable path for the virtual environment
- `get_venv_pip_executable(self)` — Get the pip executable path for the virtual environment
- `create_virtual_environment(self, force: bool=False)` — Create a virtual environment if not in one
- `check_import(self, module_name: str)` — Check if a module can be imported
- `get_package_version(self, module_name: str)` — Get version of an installed package
- `check_core_dependencies(self)` — Check all core dependencies
- `check_platform_dependencies(self)` — Check platform-specific dependencies
- `install_package(self, package: str, retries: int=3, use_venv: bool=True)` — Install a package using pip with enhanced retry mechanism - VENV ONLY MODE
- `install_requirements_file(self, retries: int=2, use_venv: bool=True)` — Install all dependencies from requirements.txt with retry - VENV ONLY MODE
- `install_project(self, retries: int=2, use_venv: bool=True)` — Install the project in editable mode with retry - VENV ONLY MODE
- `check_system_dependencies(self)` — Check system-level dependencies
- `auto_install_missing(self, missing_deps: List[str])` — Attempt to auto-install missing dependencies with enhanced error handling
- `_install_dependencies(self, missing_deps: List[str], dep_dict: Dict[str, str], optional: bool=False)` — Helper method to install a list of dependencies
- `run_full_check(self, auto_install: bool=True)` — Run comprehensive dependency check

- `check_dependencies(project_root: Path, auto_install: bool=True)` — Convenience function to check dependencies

## `src/ai_agent/utils/environment_detector.py`
Environment Detection and Adaptive Execution System for VEXIS-CLI-3.0 Gathers system data and adapts execution based on the environment
**Imports:** subprocess, platform, json, os, sys, re, typing, dataclasses, pathlib
### Class `EnvironmentInfo` (`object`)
Comprehensive environment information
### Class `EnvironmentDetector` (`object`)
Detects and analyzes the runtime environment
Methods:
- `__init__(self)`
- `detect_all(self)` — Run all detection commands and return comprehensive info
- `_detect_os_system(self)` — Detect operating system
- `_detect_os_release(self)` — Detect OS release
- `_detect_os_version(self)` — Detect OS version
- `_detect_os_machine(self)` — Detect machine architecture
- `_detect_python_version(self)` — Detect Python version
- `_detect_python_executable(self)` — Detect Python executable path
- `_detect_venv_module(self)` — Check if venv module is available
- `_detect_ollama_available(self)` — Check if Ollama is installed and available
- `_detect_ollama_version(self)` — Detect Ollama version
- `_detect_ollama_has_signin(self)` — Check if Ollama supports signin command
- `_detect_ollama_has_whoami(self)` — Check if Ollama supports whoami command
- `_detect_ollama_models(self)` — Detect installed Ollama models
- `_detect_cloud_models(self)` — Detect cloud models in installed list
- `_detect_local_models(self)` — Detect local models (non-cloud)
- `_detect_needs_ollama_update(self)` — Check if Ollama needs update for cloud model support
- `_detect_can_use_cloud_models(self)` — Check if cloud models can be used
- `_detect_recommended_provider(self)` — Determine recommended AI provider based on environment
- `_detect_docker(self)` — Check if Docker is available
- `_detect_git(self)` — Check if Git is available
- `_detect_curl(self)` — Check if curl is available
- `_detect_ollama_com_connectivity(self)` — Check connectivity to ollama.com
- `_detect_pypi_connectivity(self)` — Check connectivity to PyPI

### Class `AdaptiveExecutor` (`object`)
Executes commands adaptively based on environment
Methods:
- `__init__(self, env_info: EnvironmentInfo)`
- `create_execution_plan(self)` — Create a plan of action based on environment
- `execute_plan(self, interactive: bool=True)` — Execute the prepared plan
- `get_recommendations(self)` — Get recommendations based on environment

- `detect_and_plan()` — Main entry point: detect environment and create execution plan
- `main()` — Main entry point for standalone execution

## `src/ai_agent/utils/exceptions.py`
Exception classes for AI Agent System Enhanced exceptions with categorization for 5-Phase Architecture
**Imports:** enum, typing, dataclasses
### Class `ErrorCategory` (`Enum`)
Error categories for intelligent error handling and retry strategies
### Class `ErrorContext` (`object`)
Context information for error handling
Methods:
- `__post_init__(self)`

### Class `AIAgentException` (`Exception`)
Base exception for AI Agent system with categorization support
Methods:
- `__init__(self, message: str, context: Optional[ErrorContext]=None, **kwargs)`
- `is_retryable(self)` — Check if this error is retryable
- `get_retry_delay(self)` — Get recommended retry delay in seconds

### Class `APIError` (`AIAgentException`)
API-related error with automatic categorization
Methods:
- `__init__(self, message: str, status_code: Optional[int]=None, **kwargs)`

### Class `ValidationError` (`AIAgentException`)
Validation error - not retryable
Methods:
- `__init__(self, message: str, field: Optional[str]=None, value: Any=None, **kwargs)`

### Class `ConfigurationError` (`AIAgentException`)
Configuration error - not retryable
Methods:
- `__init__(self, message: str, **kwargs)`

### Class `PlatformError` (`AIAgentException`)
Platform-related error
Methods:
- `__init__(self, message: str, **kwargs)`

### Class `ScreenshotError` (`AIAgentException`)
Screenshot-related error
### Class `ExecutionError` (`AIAgentException`)
Execution error - may be retryable depending on command
Methods:
- `__init__(self, message: str, command: Optional[str]=None, exit_code: Optional[int]=None, **kwargs)`

### Class `TaskGenerationError` (`AIAgentException`)
Task generation error - retryable
Methods:
- `__init__(self, message: str, instruction: Optional[str]=None, **kwargs)`

### Class `CommandParsingError` (`AIAgentException`)
Command parsing error - not retryable (usually code issue)
Methods:
- `__init__(self, message: str, **kwargs)`

### Class `VerificationError` (`AIAgentException`)
Task verification error
Methods:
- `__init__(self, message: str, task: Optional[str]=None, **kwargs)`

### Class `TimeoutError` (`AIAgentException`)
Timeout error - retryable with backoff
Methods:
- `__init__(self, message: str, timeout_seconds: Optional[float]=None, **kwargs)`

### Class `ResourceExhaustedError` (`AIAgentException`)
Resource exhausted error - retryable with longer backoff
Methods:
- `__init__(self, message: str, resource_type: Optional[str]=None, **kwargs)`

### Class `ErrorHandler` (`object`)
Centralized error handling with retry logic
Methods:
- `classify_error(error: Exception, provider: Optional[str]=None, phase: Optional[str]=None)` — Classify an exception and return error context
- `should_retry(error: Exception, attempt: int)` — Determine if error should be retried based on attempt count
- `get_retry_delay(error: Exception, attempt: int)` — Calculate retry delay with exponential backoff


## `src/ai_agent/utils/interactive_menu.py`
Interactive menu system with arrow key navigation and colored output
**Imports:** sys, tty, termios, typing, rich.console, rich.panel, rich.text, rich.align
### Class `Colors` (`object`)
ANSI color codes for terminal output
### Class `MenuItem` (`object`)
Represents a single menu item
Methods:
- `__init__(self, title: str, description: str='', value: str=None, icon: str='')`

### Class `InteractiveMenu` (`object`)
Interactive menu with arrow key navigation using Rich for smooth display
Methods:
- `__init__(self, title: str, subtitle: str='')`
- `add_item(self, title: str, description: str='', value: str=None, icon: str='')` — Add a menu item
- `set_current_selection(self, value: str)` — Set the current/preferred value
- `_get_key(self)` — Get a single keypress with improved arrow key handling
- `_render_menu(self)` — Render the menu using Rich components
- `_print_menu_simple(self)` — Print the menu using simple print statements with improved highlighting
- `show(self)` — Display the interactive menu and return selected value

- `confirm_dialog(message: str, default: bool=False)` — Show a confirmation dialog
- `info_message(message: str, color: str=Colors.BRIGHT_CYAN)` — Display an info message with color
- `success_message(message: str)` — Display a success message
- `error_message(message: str)` — Display an error message
- `warning_message(message: str)` — Display a warning message

## `src/ai_agent/utils/logger.py`
Comprehensive logging system for AI Agent Zero-defect policy: detailed logging with structured output
**Imports:** sys, logging, structlog, typing, pathlib, datetime, json, traceback, .exceptions
### Class `JSONFormatter` (`logging.Formatter`)
JSON formatter for structured logging
Methods:
- `format(self, record: logging.LogRecord)`

### Class `AIAgentLogger` (`object`)
Enhanced logger for AI Agent with comprehensive features
Methods:
- `__init__(self, name: str, log_level: str='INFO', log_file: Optional[str]=None, enable_json: bool=False, enable_console: bool=True)`
- `_setup_handlers(self)` — Setup logging handlers
- `_setup_structlog(self)` — Setup structlog processor
- `debug(self, message: str, **kwargs)` — Log debug message
- `info(self, message: str, **kwargs)` — Log info message
- `warning(self, message: str, **kwargs)` — Log warning message
- `error(self, message: str, **kwargs)` — Log error message
- `critical(self, message: str, **kwargs)` — Log critical message
- `exception(self, message: str, **kwargs)` — Log exception with traceback
- `log_command(self, command: str, success: bool, duration: Optional[float]=None, error: Optional[str]=None, **kwargs)` — Log command execution
- `log_screenshot(self, screenshot_path: str, resolution: str, capture_method: str, success: bool, **kwargs)` — Log screenshot capture
- `log_api_call(self, endpoint: str, method: str, status_code: Optional[int]=None, duration: Optional[float]=None, error: Optional[str]=None, **kwargs)` — Log API call
- `log_task_step(self, task_id: str, step: int, total_steps: int, action: str, success: bool, **kwargs)` — Log task step
- `log_error_with_context(self, error: Exception, context: Optional[Dict[str, Any]]=None)` — Log error with full context
- `log_command_generation(self, task_description: str, command: str, success: bool, model: str, latency: Optional[float]=None, **kwargs)` — Log command generation from AI
- `log_task_execution(self, task_index: int, task_description: str, success: bool, commands_executed: int, duration: Optional[float]=None, **kwargs)` — Log task execution completion

- `get_logger(name: Optional[str]=None, log_level: Optional[str]=None, log_file: Optional[str]=None, enable_json: Optional[bool]=None, enable_console: Optional[bool]=None)` — Get or create logger instance
- `setup_logging(log_level: str='INFO', log_file: Optional[str]=None, enable_json: bool=False, enable_console: bool=True)` — Setup global logging configuration
### Class `LogContext` (`object`)
Context manager for adding logging context
Methods:
- `__init__(self, logger: AIAgentLogger, **context)`
- `__enter__(self)`
- `__exit__(self, exc_type, exc_val, exc_tb)`


## `src/ai_agent/utils/model_definitions.py`
Unified Model Definitions for VEXIS-CLI-3 Ollama Integration Verified against official Ollama library as of 2025 Single source of truth for all model classifications - WITH ICONS
- `get_model_families()` — Get model families sorted by priority
- `get_subfamilies(family_key)` — Get subfamilies for a specific model family
- `get_models_in_subfamily(family_key, subfamily_key)` — Get models in a specific subfamily
- `get_model_hierarchy_path(model_name)` — Get hierarchy path for a specific model
- `get_predefined_models()` — Get predefined models with descriptions

## `src/ai_agent/utils/ollama_error_handler.py`
Enhanced Ollama Error Handler for VEXIS-CLI-3.0 Provides user-friendly guidance for common Ollama issues including: - Permission errors - Model name errors   - Sign-in issues - Network connectivity problems - Installation issues
**Imports:** subprocess, os, platform, re, typing, dataclasses
### Class `OllamaError` (`object`)
Structured Ollama error information
### Class `OllamaErrorHandler` (`object`)
Enhanced error handler for Ollama with user-friendly guidance
Methods:
- `__init__(self)`
- `analyze_error(self, error_message: str, context: Optional[Dict[str, Any]]=None)` — Analyze an error message and return structured error information with user guidance
- `_handle_permission_error(self, error_message: str, context: Dict[str, Any])` — Handle permission-related errors
- `_handle_signin_error(self, error_message: str, context: Dict[str, Any])` — Handle Ollama signin errors
- `_handle_cloud_auth_error(self, error_message: str, context: Dict[str, Any])` — Handle cloud model authentication errors (401 unauthorized)
- `_handle_model_not_found(self, error_message: str, context: Dict[str, Any])` — Handle model not found errors
- `_handle_pull_error(self, error_message: str, context: Dict[str, Any])` — Handle model download/pull errors
- `_handle_connection_error(self, error_message: str, context: Dict[str, Any])` — Handle connection errors
- `_handle_timeout_error(self, error_message: str, context: Dict[str, Any])` — Handle timeout errors
- `_handle_installation_error(self, error_message: str, context: Dict[str, Any])` — Handle installation errors
- `_handle_version_error(self, error_message: str, context: Dict[str, Any])` — Handle version-related errors
- `_handle_browser_error(self, error_message: str, context: Dict[str, Any])` — Handle browser opening errors
- `_handle_generic_error(self, error_message: str, context: Dict[str, Any])` — Handle generic/unknown errors
- `format_error_for_display(self, error: OllamaError)` — Format error for user-friendly display
- `should_retry(self, error: OllamaError)` — Determine if the operation should be retried
- `get_severity(self, error: OllamaError)` — Get error severity for logging/alerting purposes

- `get_ollama_error_handler()` — Get global Ollama error handler instance
- `handle_ollama_error(error_message: str, context: Optional[Dict[str, Any]]=None, display_to_user: bool=True)` — Handle an Ollama error with user-friendly guidance

## `src/ai_agent/utils/ollama_manager.py`
Ollama Model Manager for VEXIS-1.1 AI Agent Handles model validation, installation, and management
**Imports:** subprocess, json, time, typing, ..utils.logger, .model_definitions, .ollama_error_handler
### Class `OllamaManager` (`object`)
Manages Ollama models with validation and installation
Methods:
- `get_model_families(self)` — Get available model families with names and descriptions
- `__init__(self)`
- `check_ollama_available(self)` — Check if Ollama is available and running
- `get_installed_models(self)` — Get list of installed models
- `is_model_installed(self, model_name: str)` — Check if a specific model is installed
- `validate_model(self, model_name: str)` — Validate if a model name exists and is available
- `install_model(self, model_name: str)` — Install a model if not already installed
- `get_subfamilies(self, family_key: str)` — Get subfamilies for a specific model family
- `get_models_in_subfamily(self, family_key: str, subfamily_key: str)` — Get models in a specific subfamily
- `display_model_families(self)` — Display available model families using curses-based arrow key menu
- `_test_cursor_positioning(self)` — Test if cursor positioning works in current terminal
- `_fallback_model_families(self)` — Fallback method using original number-based selection
- `display_subfamilies(self, family_key: str)` — Display subfamilies using curses-based arrow key menu
- `_fallback_subfamilies(self, family_key: str)` — Fallback method using original number-based selection
- `display_models_in_subfamily(self, family_key: str, subfamily_key: str)` — Display models using curses-based arrow key menu
- `_fallback_models_in_subfamily(self, family_key: str, subfamily_key: str)` — Fallback method using original number-based selection
- `demo_hierarchical_selection(self)` — Demo method to show how hierarchical selection works
- `interactive_model_selection(self)` — Interactive hierarchical model selection
- `get_model_hierarchy_path(self, model_name: str)` — Get the hierarchy path for a specific model
- `get_predefined_models(self)` — Get predefined models with descriptions
- `suggest_model_installation(self, model_name: str)` — Prompt user to install a model if not installed

- `get_ollama_manager()` — Get global ollama manager instance

## `src/ai_agent/utils/ollama_model_selector.py`
Ollama Model Selection UI for VEXIS-1.1 AI Agent Using curses-based arrow key navigation
**Imports:** typing
- `select_ollama_model()` — Interactive hierarchical menu for selecting Ollama models using arrow keys

## `src/ai_agent/utils/prompt_cache.py`
Prompt Cache System for VEXIS-CLI Caches LLM responses to reduce API calls and improve response times
**Imports:** hashlib, time, json, os, typing, dataclasses, pathlib, threading, .logger
### Class `CacheEntry` (`object`)
Cache entry with metadata
Methods:
- `is_expired(self)` — Check if cache entry has expired
- `touch(self)` — Update access metadata

### Class `CacheStats` (`object`)
Cache statistics
### Class `PromptCache` (`object`)
LRU Cache for LLM prompt responses
Methods:
- `__init__(self, max_size: int=1000, default_ttl: int=3600, persist_to_disk: bool=True, cache_dir: Optional[str]=None)`
- `_generate_key(self, prompt: str, model: str, provider: str, task_type: str, temperature: float=1.0, max_tokens: int=5000)` — Generate cache key from prompt parameters
- `get(self, prompt: str, model: str, provider: str, task_type: str, temperature: float=1.0, max_tokens: int=5000)` — Get cached response if available and not expired
- `put(self, prompt: str, response: str, model: str, provider: str, task_type: str, temperature: float=1.0, max_tokens: int=5000, ttl: Optional[int]=None)` — Store response in cache
- `_evict_lru(self)` — Evict least recently used entry
- `_update_hit_rate(self)` — Update cache hit rate statistic
- `invalidate(self, model: Optional[str]=None, provider: Optional[str]=None, older_than: Optional[float]=None)` — Invalidate cache entries matching criteria
- `clear(self)` — Clear all cache entries
- `get_stats(self)` — Get cache statistics
- `_save_to_disk(self)` — Save cache to disk
- `_load_from_disk(self)` — Load cache from disk

- `get_prompt_cache(max_size: int=1000, default_ttl: int=3600, persist_to_disk: bool=True)` — Get global prompt cache instance
- `invalidate_cache_for_provider(provider: str)` — Invalidate all cache entries for a specific provider
- `invalidate_cache_for_model(model: str)` — Invalidate all cache entries for a specific model
- `get_cache_stats()` — Get cache statistics

## `src/ai_agent/utils/provider_fallback.py`
Provider Fallback Manager for VEXIS-CLI Manages automatic failover between multiple AI providers for high availability
**Imports:** time, random, typing, dataclasses, enum, .exceptions, .logger
### Class `ProviderStatus` (`Enum`)
Status of a provider
### Class `ProviderHealth` (`object`)
Health metrics for a provider
Methods:
- `success_rate(self)` — Calculate success rate
- `is_circuit_open(self)` — Check if circuit breaker is open

### Class `FallbackConfig` (`object`)
Configuration for fallback behavior
### Class `ProviderFallbackManager` (`object`)
Manages provider fallback for high availability
Methods:
- `__init__(self, config: Optional[FallbackConfig]=None)`
- `get_next_available_provider(self, preferred_provider: str, excluded: Optional[List[str]]=None)` — Get the next available provider with fallback support
- `execute_with_fallback(self, preferred_provider: str, preferred_model: str, execute_func, *args, **kwargs)` — Execute a function with automatic fallback on failure
- `_get_health(self, provider: str)` — Get health record for a provider
- `_record_success(self, provider: str, latency: float)` — Record a successful request
- `_record_failure(self, provider: str, latency: float)` — Record a failed request
- `_get_default_model(self, provider: str)` — Get default model for a provider
- `get_health_report(self)` — Get health report for all providers

- `get_fallback_manager(config: Optional[FallbackConfig]=None)` — Get global fallback manager instance

## `src/ai_agent/utils/sdk_installer.py`
Automatic SDK Installer for VEXIS-CLI
**Imports:** subprocess, sys, importlib, typing, .logger
### Class `SDKInstaller` (`object`)
Handles automatic installation of missing SDK dependencies
Methods:
- `__init__(self, auto_install: bool=False)`
- `check_sdk_availability(self, provider: str)` — Check if a provider's SDK is available
- `get_missing_sdks(self, providers: List[str])` — Get information about missing SDKs for given providers
- `install_sdk(self, provider: str, interactive: bool=True)` — Install SDK for a specific provider with enhanced error handling
- `install_missing_sdks(self, providers: List[str], interactive: bool=True)` — Install missing SDKs for multiple providers
- `get_installation_commands(self, providers: List[str])` — Get installation commands for missing SDKs
- `show_provider_status(self, providers: List[str])` — Show installation status for providers

- `create_installer(auto_install: bool=False)` — Create an SDK installer instance

## `src/ai_agent/utils/security.py`
Security Utilities for VEXIS-CLI Enhanced security features including sandboxing and sensitive data masking Configuration via config.yaml or environment variables
**Imports:** re, os, subprocess, tempfile, shutil, typing, dataclasses, pathlib, .logger, .config
### Class `SecurityCheckResult` (`object`)
Result of security check
### Class `SensitiveDataMasker` (`object`)
Masks sensitive data in logs and output
Methods:
- `__init__(self)`
- `mask(self, text: str)` — Mask sensitive data in text
- `mask_dict(self, data: Dict)` — Recursively mask sensitive data in dictionary

### Class `CommandSecurityChecker` (`object`)
Security checker for terminal commands (configurable)
Methods:
- `__init__(self, config: Optional[SecurityConfig]=None)`
- `check_command(self, command: str)` — Check if a command is safe to execute based on configuration
- `check_commands(self, commands: List[str])` — Check multiple commands

### Class `SandboxManager` (`object`)
Manages sandboxed execution environment
Methods:
- `__init__(self)`
- `_detect_sandbox_tool(self)` — Detect available sandboxing tool
- `create_temp_workspace(self)` — Create temporary workspace for sandboxed execution
- `wrap_command(self, command: str, workspace: Optional[Path]=None)` — Wrap command with sandbox restrictions
- `cleanup(self)` — Clean up temporary workspace

### Class `SecurityManager` (`object`)
Main security manager combining all security features
Methods:
- `__init__(self, config: Optional[SecurityConfig]=None, enable_sandbox: bool=True, auto_mask_logs: bool=True)`
- `validate_and_prepare(self, commands: List[str])` — Validate commands and prepare them for execution
- `mask_for_logging(self, text: str)` — Mask sensitive data before logging
- `cleanup(self)` — Cleanup security resources

- `get_security_config_from_env()` — Load security configuration from environment variables
- `get_security_manager(config: Optional[SecurityConfig]=None, enable_sandbox: bool=True, auto_mask_logs: bool=True)` — Get global security manager instance
- `mask_sensitive_data(text: str)` — Convenience function to mask sensitive data
- `check_command_safety(command: str, config: Optional[SecurityConfig]=None)` — Check command safety with optional config
- `create_secure_config(enable_blocking: bool=False, enable_confirmation: bool=False, enable_sudo_warning: bool=False, enable_shell_pipe_warning: bool=False, enable_sandbox: bool=True)` — Create a security configuration programmatically

## `src/ai_agent/utils/settings_manager.py`
Settings Manager for VEXIS-1.1 AI Agent Handles API key storage and model configuration
**Imports:** json, os, pathlib, typing, dataclasses, ..utils.logger
### Class `APISettings` (`object`)
API settings data structure
### Class `SettingsManager` (`object`)
Manages application settings and API keys (in-memory only)
Methods:
- `__init__(self)`
- `_load_settings(self)` — Initialize with default settings (no file loading)
- `_save_settings(self)` — Settings are no longer persisted - in-memory only
- `get_settings(self)` — Get current settings
- `set_google_api_key(self, api_key: str)` — Set Google API key
- `set_groq_api_key(self, api_key: str)` — Set Groq API key
- `set_openai_api_key(self, api_key: str)` — Set OpenAI API key
- `get_google_api_key(self)` — Get Google API key
- `get_groq_api_key(self)` — Get Groq API key
- `get_preferred_provider(self)` — Get preferred provider
- `has_google_api_key(self)` — Check if Google API key is available
- `has_groq_api_key(self)` — Check if Groq API key is available
- `clear_google_api_key(self)` — Clear Google API key
- `clear_groq_api_key(self)` — Clear Groq API key
- `get_openai_api_key(self)` — Get OpenAI API key
- `has_openai_api_key(self)` — Check if OpenAI API key is available
- `set_anthropic_api_key(self, api_key: str)` — Set Anthropic API key
- `get_anthropic_api_key(self)` — Get Anthropic API key
- `has_anthropic_api_key(self)` — Check if Anthropic API key is available
- `clear_anthropic_api_key(self)` — Clear Anthropic API key
- `set_anthropic_model(self, model: str)` — Set Anthropic model
- `get_anthropic_model(self)` — Get Anthropic model
- `set_google_model(self, model: str)` — Set Google model
- `set_groq_model(self, model: str)` — Set Groq model
- `set_openai_model(self, model: str)` — Set OpenAI model
- `get_google_model(self)` — Get Google model
- `get_groq_model(self)` — Get Groq model
- `get_openai_model(self)` — Get OpenAI model
- `set_ollama_model(self, model: str)` — Set Ollama model
- `get_ollama_model(self)` — Get Ollama model
- `set_xai_api_key(self, api_key: str)`
- `get_xai_api_key(self)`
- `has_xai_api_key(self)`
- `set_xai_model(self, model: str)`
- `get_xai_model(self)`
- `set_meta_api_key(self, api_key: str)`
- `get_meta_api_key(self)`
- `has_meta_api_key(self)`
- `set_meta_model(self, model: str)`
- `get_meta_model(self)`
- `set_mistral_api_key(self, api_key: str)`
- `get_mistral_api_key(self)`
- `has_mistral_api_key(self)`
- `set_mistral_model(self, model: str)`
- `get_mistral_model(self)`
- `set_microsoft_api_key(self, api_key: str)`
- `get_microsoft_api_key(self)`
- `has_microsoft_api_key(self)`
- `set_microsoft_model(self, model: str)`
- `get_microsoft_model(self)`
- `set_amazon_credentials(self, access_key: str, secret_key: str)`
- `get_amazon_access_key(self)`
- `get_amazon_secret_key(self)`
- `has_amazon_credentials(self)`
- `set_amazon_model(self, model: str)`
- `get_amazon_model(self)`
- `set_cohere_api_key(self, api_key: str)`
- `get_cohere_api_key(self)`
- `has_cohere_api_key(self)`
- `set_cohere_model(self, model: str)`
- `get_cohere_model(self)`
- `set_deepseek_api_key(self, api_key: str)`
- `get_deepseek_api_key(self)`
- `has_deepseek_api_key(self)`
- `set_deepseek_model(self, model: str)`
- `get_deepseek_model(self)`
- `set_together_api_key(self, api_key: str)`
- `get_together_api_key(self)`
- `has_together_api_key(self)`
- `set_together_model(self, model: str)`
- `get_together_model(self)`
- `set_minimax_api_key(self, api_key: str)`
- `get_minimax_api_key(self)`
- `has_minimax_api_key(self)`
- `set_minimax_model(self, model: str)`
- `get_minimax_model(self)`
- `set_zhipuai_api_key(self, api_key: str)`
- `get_zhipuai_api_key(self)`
- `has_zhipuai_api_key(self)`
- `set_zhipuai_model(self, model: str)`
- `get_zhipuai_model(self)`
- `set_preferred_provider(self, provider: str)` — Set preferred provider
- `set_openrouter_api_key(self, api_key: str)` — Set OpenRouter API key
- `get_openrouter_api_key(self)` — Get OpenRouter API key
- `has_openrouter_api_key(self)` — Check if OpenRouter API key is available
- `clear_openrouter_api_key(self)` — Clear OpenRouter API key
- `set_openrouter_model(self, model: str)` — Set OpenRouter model
- `get_openrouter_model(self)` — Get OpenRouter model
- `set_api_key(self, provider: str, api_key: str)` — Generic API key setter for any provider
- `set_model(self, provider: str, model: str)` — Generic model setter for any provider
- `get_api_key(self, provider: str)` — Generic API key getter for any provider
- `get_model(self, provider: str)` — Generic model getter for any provider

- `get_settings_manager()` — Get global settings manager instance

## `src/ai_agent/utils/structured_logger.py`
Structured Logging for VEXIS-CLI JSON-formatted logs for better observability and log analysis
**Imports:** json, logging, sys, datetime, typing, pathlib, logging.handlers
### Class `StructuredLogFormatter` (`logging.Formatter`)
JSON formatter for structured logging
Methods:
- `__init__(self, indent: Optional[int]=None)`
- `format(self, record: logging.LogRecord)` — Format log record as JSON

### Class `StructuredLogger` (`object`)
Structured logger wrapper providing both console and JSON file output
Methods:
- `__init__(self, name: str='vexis', log_level: int=logging.INFO, log_dir: Optional[str]=None, json_output: bool=True, console_output: bool=True, max_file_size: int=10 * 1024 * 1024, backup_count: int=5)`
- `debug(self, message: str, **kwargs)` — Log debug message with structured context
- `info(self, message: str, **kwargs)` — Log info message with structured context
- `warning(self, message: str, **kwargs)` — Log warning message with structured context
- `error(self, message: str, **kwargs)` — Log error message with structured context
- `critical(self, message: str, **kwargs)` — Log critical message with structured context
- `_log(self, level: int, message: str, **kwargs)` — Internal log method with context

### Class `TelemetryCollector` (`object`)
Collects and exports telemetry data for observability
Methods:
- `__init__(self, export_interval: int=60)`
- `increment_counter(self, name: str, value: int=1, labels: Optional[Dict]=None)` — Increment a counter metric
- `set_gauge(self, name: str, value: float, labels: Optional[Dict]=None)` — Set a gauge metric
- `record_histogram(self, name: str, value: float, labels: Optional[Dict]=None)` — Record a histogram observation
- `get_metrics(self)` — Get current metrics snapshot
- `export_metrics(self)` — Export metrics as JSON string
- `reset(self)` — Reset all metrics

- `get_structured_logger(name: str='vexis', log_level: int=logging.INFO, log_dir: Optional[str]=None, json_output: bool=True)` — Get or create global structured logger
- `get_telemetry()` — Get global telemetry collector
- `configure_logging(level: str='INFO', json_output: bool=True, log_dir: Optional[str]=None)` — Configure structured logging for the application
- `log_execution_metric(metric_name: str, value: float, provider: str, model: str, phase: Optional[str]=None)` — Log an execution metric with structured context

## `src/ai_agent/utils/yellow_selection/__init__.py`
Yellow Selection System - Unified Menu Technology Clean, consistent yellow highlighting for all selection interfaces
**Imports:** .clean_interactive_menu, .clean_hierarchical_selector, .fallback_interactive_menu, .main
No top-level classes or functions; this module consists of constants, package exports, script logic, or registration side effects.

## `src/ai_agent/utils/yellow_selection/clean_hierarchical_selector.py`
Clean Hierarchical Model Selector Updates existing display without creating new content below
**Imports:** typing
### Class `CleanHierarchicalSelector` (`object`)
Clean hierarchical selector that updates display in-place
Methods:
- `__init__(self)` — Initialize clean selector
- `display_model_families(self)` — Display model families with clean updates
- `display_subfamilies(self, family_key: str)` — Display subfamilies with clean updates
- `display_models_in_subfamily(self, family_key: str, subfamily_key: str)` — Display models with clean updates
- `show_final_selection(self, family_key: str, subfamily_key: str, model_key: str)` — Display final selection
- `interactive_model_selection(self)` — Clean hierarchical model selection with in-place updates

- `get_clean_selector()` — Get clean hierarchical selector instance

## `src/ai_agent/utils/yellow_selection/clean_interactive_menu.py`
Clean Interactive Menu - No Log Creation Updates existing display without creating new content below
**Imports:** sys, os, typing
### Class `Colors` (`object`)
Color constants from reproducible configuration
Methods:
- `__init__(self)`

### Class `CleanInteractiveMenu` (`object`)
Clean menu that updates display without creating new content
Methods:
- `__init__(self, title: str, description: str)`
- `add_item(self, display_name: str, description: str, value: Any, icon: str='📋')`
- `clear_screen(self)` — Clear screen only once
- `display_header(self)` — Display header only once
- `display_footer(self)` — Display footer only once
- `update_display(self)` — Update only the menu items, no new content
- `get_key(self)` — Get key press with universal arrow key detection
- `_universal_get_key(self)` — Universal key detection that works anywhere
- `_fallback_input(self)` — Fallback to regular input() method
- `show(self)` — Show clean interactive menu with improved display handling
- `fallback_selection(self)` — Fallback to numbered selection with clean display

- `success_message(message: str)`
- `error_message(message: str)`
- `warning_message(message: str)`

## `src/ai_agent/utils/yellow_selection/config.py`
Yellow Selection System Configuration Reproducible settings for consistent behavior across platforms
- `get_config()` — Get the yellow selection configuration
- `get_colors()` — Get color definitions
- `get_navigation_config()` — Get navigation configuration
- `get_display_config()` — Get display configuration
- `is_reproducible_mode()` — Check if reproducible mode is enabled

## `src/ai_agent/utils/yellow_selection/fallback_interactive_menu.py`
Fallback Menu System - Compatible with terminals that don't support cursor positioning Uses screen clearing instead of in-place updates for maximum compatibility
**Imports:** sys, os, typing
### Class `Colors` (`object`)
Color constants from reproducible configuration
Methods:
- `__init__(self)`

### Class `FallbackInteractiveMenu` (`object`)
Fallback menu that uses screen clearing for maximum compatibility
Methods:
- `__init__(self, title: str, description: str)`
- `add_item(self, display_name: str, description: str, value: Any, icon: str='📋')`
- `get_key(self)` — Get key press with universal arrow key detection
- `_universal_get_key(self)` — Universal key detection that works anywhere
- `_fallback_input(self)` — Fallback to regular input() method
- `display_menu(self)` — Display the complete menu with current selection highlighted
- `show(self)` — Show interactive menu with fallback display updates
- `fallback_selection(self)` — Fallback to numbered selection with clean display

- `success_message(message: str)`
- `error_message(message: str)`
- `warning_message(message: str)`

## `src/ai_agent/utils/yellow_selection/main.py`
Yellow Selection System - Main Entry Point Central access point for all yellow selection functionality
- `get_yellow_menu(title: str, description: str, use_fallback: bool=False)` — Get a yellow-highlighted interactive menu
- `get_yellow_selector(use_fallback: bool=False)` — Get the yellow hierarchical selector
- `show_yellow_selection_demo()` — Demonstrate the yellow selection system
- `create_provider_menu()` — Create a provider selection menu with yellow highlighting
- `create_model_menu()` — Create a model selection menu with yellow highlighting

## `system_check.py`
Comprehensive System Check for VEXIS-CLI Validates all components and provides detailed diagnostics
**Imports:** subprocess, sys, os, importlib.util, pathlib, typing
### Class `SystemChecker` (`object`)
Comprehensive system validation
Methods:
- `__init__(self)`
- `log(self, status: str, message: str, details: str='')` — Log a check result
- `check_python_version(self)` — Check Python version compatibility
- `check_virtual_environment(self)` — Check if running in virtual environment
- `check_dependencies(self)` — Check Python dependencies
- `check_ollama_installation(self)` — Check Ollama installation and status
- `check_project_structure(self)` — Check project structure
- `check_configuration(self)` — Check configuration files
- `check_import_structure(self)` — Check if core modules can be imported
- `check_permissions(self)` — Check file permissions
- `run_all_checks(self)` — Run all system checks
- `print_summary(self)` — Print check summary

- `main()` — Main function

## `test_cloud_models.py`
Test script for cloud model error handling
**Imports:** sys, os, ai_agent.external_integration.ollama_provider
- `test_cloud_model_errors()` — Test cloud model error handling

## `test_concise_prompts.py`
Simple test for the improved concise prompts
**Imports:** sys, ai_agent.external_integration.model_runner
- `test_concise_prompts()` — Test the new concise prompts

## `test_fix.py`
Test script to verify the fix
**Imports:** sys, pathlib
No top-level classes or functions; this module consists of constants, package exports, script logic, or registration side effects.

## `test_improved_prompts.py`
Test script for improved VEXIS-CLI prompts Validates that the enhanced prompt engineering improvements work correctly
**Imports:** sys, os, ai_agent.external_integration.model_runner
- `test_task_generation_prompt()` — Test the improved TASK_GENERATION prompt
- `test_command_parsing_prompt()` — Test the improved COMMAND_PARSING prompt
- `test_system_instructions()` — Test system instructions for both task types
- `main()` — Run all tests

## `test_kg_command.py`
Test script for /KG (Keep Going) command functionality
**Imports:** sys, os, pathlib
- `test_kg_command_implementation()` — Test that /KG command components are properly implemented

## `tests/conftest.py`
Pytest configuration and shared fixtures
**Imports:** pytest, tempfile, pathlib, unittest.mock
- `temp_directory()` — Provide a temporary directory for tests
- `mock_model_response()` — Provide a mock model response
- `mock_api_error()` — Provide a mock API error
- `sample_user_prompt()` — Provide a sample user prompt
- `sample_terminal_log()` — Provide a sample terminal log
- `reset_singletons()` — Reset singleton instances before each test to ensure isolation

## `tests/unit/__init__.py`
Unit tests for VEXIS-CLI
No top-level classes or functions; this module consists of constants, package exports, script logic, or registration side effects.

## `tests/unit/test_cost_manager.py`
Unit tests for cost manager
**Imports:** pytest, tempfile, pathlib, src.ai_agent.utils.cost_manager
### Class `TestCostEstimation` (`object`)
Test cost estimation
Methods:
- `test_estimate_openai_gpt5(self)` — Test cost estimation for GPT-5
- `test_estimate_google_gemini(self)` — Test cost estimation for Gemini
- `test_estimate_local_ollama(self)` — Test cost estimation for Ollama (free)

### Class `TestBudgetChecking` (`object`)
Test budget enforcement
Methods:
- `test_daily_budget_enforcement(self)` — Test daily budget enforcement
- `test_per_request_budget(self)` — Test per-request budget enforcement

### Class `TestCheaperAlternatives` (`object`)
Test cheaper alternative suggestions
Methods:
- `test_suggest_cheaper_alternative(self)` — Test finding cheaper alternative

### Class `TestBudgetAlerts` (`object`)
Test budget alert levels
Methods:
- `test_warning_alert_level(self)` — Test warning level at 80%
- `test_critical_alert_level(self)` — Test critical level at 95%

### Class `TestUsageTracking` (`object`)
Test usage tracking and statistics
Methods:
- `test_record_usage_updates_stats(self)` — Test that recording usage updates statistics
- `test_provider_cost_tracking(self)` — Test per-provider cost tracking

### Class `TestPersistence` (`object`)
Test cost data persistence
Methods:
- `test_save_and_load(self)` — Test that costs are persisted and loaded correctly


## `tests/unit/test_exceptions.py`
Unit tests for enhanced exception handling
**Imports:** pytest, src.ai_agent.utils.exceptions
### Class `TestErrorCategory` (`object`)
Test error category definitions
Methods:
- `test_category_values(self)` — Test that all categories have correct string values

### Class `TestAPIError` (`object`)
Test APIError with automatic categorization
Methods:
- `test_auth_error_categorization(self)` — Test 401/403 errors are categorized as authentication
- `test_rate_limit_categorization(self)` — Test 429 errors are categorized as rate limit
- `test_server_error_categorization(self)` — Test 5xx errors are categorized as external and retryable
- `test_validation_error_categorization(self)` — Test 4xx errors (except 429) are validation errors

### Class `TestErrorHandler` (`object`)
Test centralized error handling
Methods:
- `test_should_retry_for_retryable_error(self)` — Test that retryable errors are retried within limit
- `test_should_not_retry_for_non_retryable_error(self)` — Test that non-retryable errors are never retried
- `test_retry_delay_with_exponential_backoff(self)` — Test exponential backoff calculation
- `test_rate_limit_delay_is_longer(self)` — Test rate limit errors have longer delays

### Class `TestExecutionError` (`object`)
Test ExecutionError categorization based on exit code
Methods:
- `test_sigint_not_retryable(self)` — Test SIGINT (130) is not retryable
- `test_other_signals_are_retryable(self)` — Test other signal terminations are retryable
- `test_regular_exit_code_retryable(self)` — Test regular exit codes are retryable

### Class `TestSpecializedErrors` (`object`)
Test other specialized error types
Methods:
- `test_timeout_error_is_retryable(self)` — Test timeout errors are retryable
- `test_resource_exhausted_is_retryable(self)` — Test resource exhausted errors are retryable with longer backoff
- `test_validation_error_is_not_retryable(self)` — Test validation errors are never retryable


## `tests/unit/test_plugins.py`
Unit tests for plugin system
**Imports:** pytest, src.ai_agent.plugins
### Class `TestPluginManager` (`object`)
Test plugin manager functionality
Methods:
- `test_create_plugin_manager(self)` — Test plugin manager creation
- `test_register_plugin(self)` — Test registering a plugin
- `test_unregister_plugin(self)` — Test unregistering a plugin

### Class `TestHookExecution` (`object`)
Test hook execution
Methods:
- `test_initialize_hook(self)` — Test initialize hook is called
- `test_pre_execute_hook_modifies_command(self)` — Test pre_execute hook can modify command
- `test_multiple_plugins_same_hook(self)` — Test multiple plugins can implement same hook
- `test_error_hook_can_handle_error(self)` — Test error hook can indicate error was handled

### Class `TestCustomCommands` (`object`)
Test custom command registration
Methods:
- `test_get_commands_hook(self)` — Test plugins can register custom commands

### Class `TestGlobalPluginManager` (`object`)
Test global plugin manager singleton
Methods:
- `test_global_manager_is_singleton(self)` — Test that global manager is a singleton


## `tests/unit/test_security.py`
Unit tests for security utilities
**Imports:** os, pytest, src.ai_agent.utils.security
### Class `TestSensitiveDataMasker` (`object`)
Test sensitive data masking
Methods:
- `test_mask_api_key(self)` — Test API key masking
- `test_mask_password(self)` — Test password masking
- `test_mask_token(self)` — Test token masking
- `test_mask_aws_key(self)` — Test AWS access key masking
- `test_mask_github_token(self)` — Test GitHub token masking
- `test_multiple_secrets_in_text(self)` — Test masking multiple secrets in single text
- `test_no_false_positives(self)` — Test that normal text is not masked

### Class `TestSecurityConfig` (`object`)
Test security configuration
Methods:
- `test_default_config_allows_all(self)` — Test that default config allows all commands
- `test_create_secure_config_strict(self)` — Test creating strict security config
- `test_create_secure_config_permissive(self)` — Test creating permissive (default) security config

### Class `TestEnvironmentVariableConfig` (`object`)
Test loading configuration from environment variables
Methods:
- `test_env_var_blocking_enabled(self, monkeypatch)` — Test VEXIS_ENABLE_COMMAND_BLOCKING=true
- `test_env_var_confirmation_enabled(self, monkeypatch)` — Test VEXIS_ENABLE_CONFIRMATION_PROMPTS=1
- `test_env_var_sudo_warning(self, monkeypatch)` — Test VEXIS_ENABLE_SUDO_WARNING=yes
- `test_env_var_shell_pipe_warning(self, monkeypatch)` — Test VEXIS_ENABLE_SHELL_PIPE_WARNING=on
- `test_env_var_sandbox_disabled(self, monkeypatch)` — Test VEXIS_ENABLE_SANDBOX=false
- `test_env_var_defaults_when_not_set(self, monkeypatch)` — Test defaults when env vars are not set

### Class `TestCommandSecurityChecker` (`object`)
Test command security checking with configurable settings
Methods:
- `test_all_commands_allowed_by_default(self)` — Test that default config (no blocking) allows all commands
- `test_blocking_enabled_blocks_dangerous_commands(self)` — Test that enabling blocking actually blocks dangerous commands
- `test_confirmation_enabled_requires_confirmation(self)` — Test that enabling confirmation requires confirmation for risky commands
- `test_sudo_warning_enabled(self)` — Test that sudo warning is shown when enabled
- `test_shell_pipe_warning_enabled(self)` — Test that shell pipe warning is shown when enabled
- `test_safe_command_always_allowed(self)` — Test safe commands are always allowed regardless of config
- `test_empty_command_blocked(self)` — Test empty command is always blocked (not a safety issue)

### Class `TestSecurityCheckResult` (`object`)
Test security check result dataclass
Methods:
- `test_result_structure(self)` — Test result has expected fields
- `test_masked_output_contains_redacted(self)` — Test masked output contains [REDACTED] for sensitive commands


## `tests/unit/test_task_lifecycle.py`
Tests for task lifecycle and long-running command handling.
**Imports:** os, time, ai_agent.core_processing.terminal_history, ai_agent.user_interface.five_phase_app, ai_agent.utils.config
- `test_background_batch_command_is_detached_and_survives_shell_exit(tmp_path)`
- `test_foreground_batch_command_respects_timeout(tmp_path)`
- `test_execution_config_timeout_values_are_loaded_from_example_config()`
- `test_runtime_options_are_applied_to_engine(monkeypatch)`

## `tests/unit/test_telegram_queue.py`
Tests for Telegram queue resilience.
**Imports:** asyncio, threading, time, unittest.mock, ai_agent.external_integration.telegram_bot
- `test_process_message_queue_drops_after_bounded_retries()`
- `test_process_message_queue_skips_delayed_retries_without_blocking()`
- `test_handle_message_cancels_overlapping_user_task_and_starts_latest()`
- `test_restart_command_acknowledges_and_invokes_restart_callback()`

