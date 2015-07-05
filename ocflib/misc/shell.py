"""Misc utilities for helping with shell commands."""
# shlex.quote is new in Python 3.3
try:  # pragma: no cover
    from shlex import quote as escape_arg  # noqa
except ImportError:  # pragma: no cover
    from pipes import quote as escape_arg  # noqa
