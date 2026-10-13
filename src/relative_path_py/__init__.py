"""relative_path_py — relative path resolution between two directories.

Public API:
    relative_to      — relative path string from a source dir to a target dir
    resolve_relative — alias kept for a friendlier call site

This package deliberately exports only the two names above. Importing * is
supported but unnecessary: there are exactly two functions.
"""

from .core import relative_to, resolve_relative

__all__ = ["relative_to", "resolve_relative"]
