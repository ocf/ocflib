"""Misc utilities for helping with shell commands."""
from colorama import Fore, Back

# shlex.quote is new in Python 3.3
try:  # pragma: no cover
    from shlex import quote as escape_arg  # noqa
except ImportError:  # pragma: no cover
    from pipes import quote as escape_arg  # noqa


def _wrap_colorama(color, reset):
    """Create functions like red('hello') and bg_red('hello') for wrapping
    strings in ASNI color escapes. This is pretty hacky.

    >>> red('hello')
    '\x1b[31mhello\x1b[39m'
    """
    def wrapper(string):
        return color + string + reset
    return wrapper


COLORS = [
    'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'
]
for color in COLORS:
    locals()[color] = _wrap_colorama(getattr(Fore, color.upper()), Fore.RESET)
    locals()['bg_' + color] = (
        _wrap_colorama(getattr(Back, color.upper()), Back.RESET)
    )
