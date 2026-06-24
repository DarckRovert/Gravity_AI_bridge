"""
╔══════════════════════════════════════════════════════════════════════════════╗
║               GRAVITY AI - CORE BASE PLUGIN / INTEGRATION                    ║
║             Standard Life-Cycle Interface for Third-Party Plugins            ║
╚══════════════════════════════════════════════════════════════════════════════╗
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class GravityIntegration(ABC):
    """
    Abstract Base Class for all external modules, APIs, or integrations.
    All plugins moved to /integrations should inherit from this.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the technical identifier name of the plugin."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Returns a user-friendly description of what this integration does."""
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """
        Executes startup logic for the integration.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """
        Executes cleanup and termination tasks.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Returns structured health and status metrics.
        Example: {"status": "healthy", "details": {...}}
        """
        pass
