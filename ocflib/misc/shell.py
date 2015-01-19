"""Misc utilities for helping with shell commands."""

# shlex.quote is new in Python 3.3
try:
    from shlex import quote as escape_arg  # noqa
except ImportError:
    from pipes import quote as escape_arg  # noqa
