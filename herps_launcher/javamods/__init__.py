"""Passive Java mod analysis and local data-tier port-pack integration.

This package never starts a JVM, a mod build, an oracle, or a game.
"""

from .adapter import PortPackAdapter

__all__ = ["PortPackAdapter"]
