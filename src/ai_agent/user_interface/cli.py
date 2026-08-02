"""
VEXIS-CLI-3 -- modern, Typer-based command-line interface.

This is the *user-facing* layer. It depends only on the peripheral
subsystems (``ai_agent.config``) and the stable ``FivePhaseAIAgent`` entry
point -- it never reaches into core engine internals, preserving a clean
separation of concerns.

Commands
--------
* ``vexis run "<instruction>"``      Execute the agent (drives the core engine).
* ``vexis config show``           Pretty-print the active configuration.
* ``vexis config validate``       Validate configuration and exit.
* ``vexis providers``             List providers, auth status and defaults.
* ``vexis models list``           List available models / capabilities.
* ``vexis version``               Version and environment information.
"""
from __future__ import annotations

import platform
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ai_agent.config import (
    AppConfig,
    ConfigLoader,
    get_app_config,
    get_model_settings,
    get_provider_registry,
    get_secret_store,
)
from ai_agent.utils.logger import get_logger, setup_logging

VERSION = "3.0.0"

app = typer.Typer(
    name="vexis",
    help="VEXIS-CLI-3 -- multi-provider AI agent CLI",
    rich_markup_mode="rich",
    add_completion=True,
)
console = Console()

config_app = typer.Typer(help="Inspect and validate configuration.")
models_app = typer.Typer(help="List and inspect available models.")
app.add_typer(config_app, name="config")
app.add_typer(models_app, name="models")


def _err(msg: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {msg}")


def _version_info() -> Dict[str, str]:
    import pydantic
    import typer as _t

    return {
        "vexis": VERSION,
        "python": platform.python_version(),
        "pydantic": pydantic.VERSION,
        "typer": getattr(_t, "__version__", "unknown"),
        "platform": f"{platform.system()} {platform.machine()}",
    }


# --------------------------------------------------------------------------- #
# Top-level commands                                                          #
# --------------------------------------------------------------------------- #

@app.command()
def version() -> None:
    """Show version and environment information."""
    info = _version_info()
    table = Table(show_header=False, box=None, padding=(0, 2))
    for k, v in info.items():
        table.add_row(f"[cyan]{k}[/cyan]", str(v))
    console.print(Panel(table, title="[bold]VEXIS-CLI-3[/bold]", border_style="cyan"))


@app.command()
def providers() -> None:
    """List configured providers, auth status and default models."""
    registry = get_provider_registry()
    secrets = get_secret_store()
    table = Table(title="Providers", border_style="cyan")
    table.add_column("Provider", style="bold")
    table.add_column("Auth")
    table.add_column("Default model")
    table.add_column("Vision")
    table.add_column("Stream")
    table.add_column("Credential")
    for spec in sorted(registry.all(), key=lambda s: s.name.value):
        ok = secrets.has(spec.name.value)
        cred = "[green]set[/green]" if ok else "[dim]unset[/dim]"
        table.add_row(
            spec.name.value,
            spec.auth_scheme.value,
            spec.default_model or "-",
            "yes" if spec.supports_vision else "-",
            "yes" if spec.supports_streaming else "-",
            cred,
        )
    console.print(table)
    console.print("[dim]Credentials are resolved from env / .env / keyring and never printed.[/dim]")


@app.command()
def run(
    instruction: str = typer.Argument(..., help="Natural-language instruction for the agent."),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Provider to use (overrides config)."),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use (overrides config)."),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to a config file."),
    max_iterations: int = typer.Option(10, "--max-iterations", help="Max Phase 2-4 iterations."),
    command_timeout: int = typer.Option(600, "--command-timeout", help="Per-command timeout (s)."),
    task_timeout: int = typer.Option(5400, "--task-timeout", help="Per-task timeout (s)."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write results to a JSON file."),
    log_file: Optional[Path] = typer.Option(None, "--log-file", help="Write logs to this file."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable DEBUG logging."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-error output."),
    validate_only: bool = typer.Option(False, "--validate-only", help="Validate configuration and exit."),
) -> None:
    """Run the VEXIS agent against an instruction (drives the core engine)."""
    # -- validate-only shortcut ------------------------------------------- #
    if validate_only:
        try:
            ConfigLoader(str(config) if config else None).validate()
        except Exception as e:  # noqa: BLE001
            _err(f"Configuration validation failed: {e}")
            raise typer.Exit(code=1)
        console.print("[green]Configuration validation passed[/green]")
        raise typer.Exit(code=0)

    if not instruction or not instruction.strip():
        _err("Instruction cannot be empty.")
        raise typer.Exit(code=1)

    # -- initialize core agent (lazy import keeps other commands light) -- #
    try:
        from ai_agent.user_interface.five_phase_app import FivePhaseAIAgent

        agent = FivePhaseAIAgent(
            provider=provider,
            model=model,
            config_path=str(config) if config else None,
        )
    except Exception as e:  # noqa: BLE001
        _err(f"Failed to initialize AI Agent: {e}")
        raise typer.Exit(code=1)

    options: Dict[str, object] = {
        "verbose": verbose,
        "quiet": quiet,
        "output": str(output) if output else None,
        "log_file": str(log_file) if log_file else None,
        "max_iterations": max_iterations,
        "command_timeout": command_timeout,
        "task_timeout": task_timeout,
    }

    if verbose:
        setup_logging(log_level="DEBUG")
    elif log_file:
        setup_logging(log_file=str(log_file))

    start = time.time()
    try:
        exit_code = agent.run(instruction, options)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        raise typer.Exit(code=1)
    elapsed = time.time() - start

    if not quiet:
        console.print(f"\nTotal execution time: [cyan]{elapsed:.2f}[/cyan] seconds")
        console.print(f"Exit code: [bold]{exit_code}[/bold]")
    raise typer.Exit(code=int(exit_code) if exit_code is not None else 0)


# --------------------------------------------------------------------------- #
# ``config`` sub-commands                                                      #
# --------------------------------------------------------------------------- #

@config_app.command("show")
def config_show(
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
) -> None:
    """Pretty-print the active (validated) configuration."""
    try:
        cfg: AppConfig = ConfigLoader(str(config) if config else None).load()
    except Exception as e:  # noqa: BLE001
        _err(f"Failed to load configuration: {e}")
        raise typer.Exit(code=1)

    secrets = get_secret_store()
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[cyan]preferred_provider[/cyan]", cfg.preferred_provider_str)
    table.add_row("[cyan]local_model[/cyan]", cfg.api.local_model)
    table.add_row("[cyan]local_endpoint[/cyan]", cfg.api.local_endpoint)
    table.add_row("[cyan]api.timeout[/cyan]", str(cfg.api.timeout))
    table.add_row("[cyan]api.max_retries[/cyan]", str(cfg.api.max_retries))
    table.add_row(
        "[cyan]compression[/cyan]",
        f"{'on' if cfg.api.compression_enabled else 'off'} "
        f"(thr={cfg.api.compression_threshold}, "
        f"target={cfg.api.compression_target_ratio}%)",
    )
    table.add_row("[cyan]logging.level[/cyan]", cfg.logging.level)
    table.add_row("[cyan]execution.mode[/cyan]", cfg.execution.mode)
    console.print(Panel(table, title="[bold]VEXIS Configuration[/bold]", border_style="cyan"))

    # Per-provider credential status (redacted)
    registry = get_provider_registry()
    cred_table = Table(title="Provider credentials", border_style="cyan")
    cred_table.add_column("Provider")
    cred_table.add_column("Status")
    cred_table.add_column("Default model")
    for spec in sorted(registry.all(), key=lambda s: s.name.value):
        if spec.auth_scheme.value == "none":
            status = "[dim]n/a (local)[/dim]"
        elif secrets.has(spec.name.value):
            status = "[green]configured[/green]"
        else:
            status = "[yellow]missing[/yellow]"
        cred_table.add_row(spec.name.value, status, spec.default_model or "-")
    console.print(cred_table)


@config_app.command("validate")
def config_validate(
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
) -> None:
    """Validate the configuration file and exit."""
    try:
        ConfigLoader(str(config) if config else None).validate()
    except Exception as e:  # noqa: BLE001
        _err(f"Configuration validation failed: {e}")
        raise typer.Exit(code=1)
    console.print("[green]Configuration validation passed[/green]")
    raise typer.Exit(code=0)


# --------------------------------------------------------------------------- #
# ``models`` sub-commands                                                       #
# --------------------------------------------------------------------------- #

@models_app.command("list")
def models_list(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Filter by provider."),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file whose model overrides to show."),
) -> None:
    """List available providers' models and capabilities."""
    from ai_agent.config import ConfigLoader, get_app_config, get_model_settings

    app = ConfigLoader(str(config)).load() if config else get_app_config()
    registry = get_provider_registry()
    ms = get_model_settings(app)
    specs = registry.all()
    if provider:
        spec = registry.get(provider)
        if spec is None:
            _err(f"Unknown provider: {provider}")
            raise typer.Exit(code=1)
        specs = [spec]

    table = Table(title="Models", border_style="cyan")
    table.add_column("Provider")
    table.add_column("Default model")
    table.add_column("Vision")
    table.add_column("Stream")
    for spec in sorted(specs, key=lambda s: s.name.value):
        table.add_row(
            spec.name.value,
            ms.default_model_for(spec.name.value) or "-",
            "yes" if spec.supports_vision else "-",
            "yes" if spec.supports_streaming else "-",
        )
    console.print(table)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
