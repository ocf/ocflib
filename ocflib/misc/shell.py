"""Misc utilities for helping with shell commands."""
import getpass
import os
import subprocess
import tempfile

from colorama import Back
from colorama import Fore

# shlex.quote is new in Python 3.3
try:  # pragma: no cover
    from shlex import quote as escape_arg  # noqa
except ImportError:  # pragma: no cover
    from pipes import quote as escape_arg  # noqa


def get_editor():
    """Returns the user's preferred editor, or nano."""
    return os.environ.get('VISUAL') or os.environ.get('EDITOR') or 'nano'


def edit_file(template):
    """Open a file for the user to edit.

    Similar to `git commit`, opens a file and waits for the user to save it.
    The content is returned.

    :param template: string template of the file
    """
    with tempfile.NamedTemporaryFile() as tmp:
        with open(tmp.name, 'w') as f:
            f.write(template)

        # We need to close the file and reopen it later in case the editor
        # overwrites the old file with a new file descriptor.
        subprocess.check_call([get_editor(), tmp.name])
        with open(tmp.name) as f:
            return f.read()


def prompt_for_new_password(
    prompt='Enter password: ',
    prompt_confirm='Confirm password: ',
    validator=bool,
):
    """Prompt the user to enter a new password.

    :param prompt: prompt to display
    :param prompt_confirm: prompt to display for confirming password
    :param validator: function that accepts a password and raises a ValueError
                      if something is wrong with it
    :return: the new password
    """
    def get_pass(prompt):
        # TODO: echo asterisks as the user types to avoid confusion
        return getpass.getpass(prompt)

    while True:  # ask until verified password
        while True:  # ask until password verified
            new_password = get_pass(prompt)

            try:
                validator(new_password)
            except ValueError as ex:
                print(red('[ERROR]') + ' Password failed some requirements:')
                print(' - {error}'.format(error=ex))
            else:
                break

        if new_password == get_pass(green('[OK]') + ' ' + prompt_confirm):
            break
        else:
            print(red('[ERROR]') + " Passwords didn't match, try again?")

    return new_password


# terminal text color wrappers;
# this is pretty ugly, but defining them manually lets us avoid hacking flake8
def _wrap_colorama(color, reset):
    """Create functions like red('hello') and bg_red('hello') for wrapping
    strings in ASNI color escapes.

    >>> red('hello')
    '\x1b[31mhello\x1b[39m'
    """
    def wrapper(string):
        return '{color}{string}{reset}'.format(
            color=color,
            string=string,
            reset=reset,
        )
    return wrapper


COLORS = [
    'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'
]

black = _wrap_colorama(Fore.BLACK, Fore.RESET)
bg_black = _wrap_colorama(Back.BLACK, Back.RESET)

red = _wrap_colorama(Fore.RED, Fore.RESET)
bg_red = _wrap_colorama(Back.RED, Back.RESET)

green = _wrap_colorama(Fore.GREEN, Fore.RESET)
bg_green = _wrap_colorama(Back.GREEN, Back.RESET)

yellow = _wrap_colorama(Fore.YELLOW, Fore.RESET)
bg_yellow = _wrap_colorama(Back.YELLOW, Back.RESET)

blue = _wrap_colorama(Fore.BLUE, Fore.RESET)
bg_blue = _wrap_colorama(Back.BLUE, Back.RESET)

magenta = _wrap_colorama(Fore.MAGENTA, Fore.RESET)
bg_magenta = _wrap_colorama(Back.MAGENTA, Back.RESET)

cyan = _wrap_colorama(Fore.CYAN, Fore.RESET)
bg_cyan = _wrap_colorama(Back.CYAN, Back.RESET)

white = _wrap_colorama(Fore.WHITE, Fore.RESET)
bg_white = _wrap_colorama(Back.WHITE, Back.RESET)

bold = _wrap_colorama('\033[1m', '\033[0m')
