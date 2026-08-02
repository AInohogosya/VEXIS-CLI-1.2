"""
Probe Registry for Verification-First Execution

Manages the registration and lookup of verification probes.
Provides a clean API for adding, removing, and querying probes.
"""

import threading
from typing import Dict, List, Optional, Type

from ...utils.logger import get_logger
from .probes import Probe, FileExistenceProbe, SyntaxCheckProbe, CommandParseProbe


class ProbeRegistry:
    """
    Thread-safe registry for verification probes.

    Probes are registered by name and can be looked up by:
    - Exact name
    - Command pattern (which probes apply to a given command)
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern to ensure one global registry"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.logger = get_logger("verification.registry")
        self._probes: Dict[str, Probe] = {}
        self._initialized = True

        self._register_defaults()

    def _register_defaults(self):
        """Register the default set of probes"""
        self.register(FileExistenceProbe())
        self.register(SyntaxCheckProbe())
        self.register(CommandParseProbe())
        self.logger.info("Default probes registered", probe_count=len(self._probes))

    def register(self, probe: Probe) -> None:
        """
        Register a probe instance.

        Args:
            probe: The probe instance to register

        Raises:
            ValueError: If a probe with the same name is already registered
        """
        if probe.name in self._probes:
            self.logger.warning(
                f"Overwriting existing probe: {probe.name}",
                old_probe=self._probes[probe.name].__class__.__name__,
                new_probe=probe.__class__.__name__,
            )

        self._probes[probe.name] = probe
        self.logger.debug(f"Registered probe: {probe.name}", description=probe.description)

    def unregister(self, name: str) -> Optional[Probe]:
        """
        Remove a probe from the registry.

        Args:
            name: Name of the probe to remove

        Returns:
            The removed probe, or None if not found
        """
        probe = self._probes.pop(name, None)
        if probe:
            self.logger.debug(f"Unregistered probe: {name}")
        return probe

    def get(self, name: str) -> Optional[Probe]:
        """
        Get a probe by name.

        Args:
            name: Name of the probe

        Returns:
            The probe instance, or None if not found
        """
        return self._probes.get(name)

    def get_all(self) -> List[Probe]:
        """
        Get all registered probes.

        Returns:
            List of all registered probe instances
        """
        return list(self._probes.values())

    def get_applicable(self, command: str) -> List[Probe]:
        """
        Get all probes that apply to the given command.

        Args:
            command: The command to check

        Returns:
            List of probes that should run for this command
        """
        applicable = []
        for probe in self._probes.values():
            try:
                if probe.applies_to(command):
                    applicable.append(probe)
            except Exception as e:
                self.logger.error(
                    f"Error checking if probe {probe.name} applies to command: {e}",
                    command=command,
                )
        return applicable

    def list_probes(self) -> List[Dict[str, str]]:
        """
        List all registered probes with their metadata.

        Returns:
            List of dicts with probe info
        """
        return [
            {
                "name": probe.name,
                "description": probe.description,
                "class": probe.__class__.__name__,
            }
            for probe in self._probes.values()
        ]

    def clear(self) -> None:
        """Remove all probes (useful for testing)"""
        self._probes.clear()
        self.logger.debug("Cleared all probes")

    def reset(self) -> None:
        """Reset to default probes"""
        self._probes.clear()
        self._register_defaults()

    @property
    def count(self) -> int:
        """Number of registered probes"""
        return len(self._probes)

    def __contains__(self, name: str) -> bool:
        return name in self._probes

    def __len__(self) -> int:
        return len(self._probes)

    def __repr__(self) -> str:
        probes = ", ".join(self._probes.keys())
        return f"ProbeRegistry(probes=[{probes}])"
