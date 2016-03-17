import mock
import pytest
from colorama import Back
from colorama import Fore

import ocflib.misc.shell
from ocflib.misc.shell import get_editor


def test_shell_quote():
    assert ocflib.misc.shell.escape_arg


@pytest.mark.parametrize('color', ocflib.misc.shell.COLORS)
def test_color_wrappers_with_tty(color):
    with mock.patch('sys.stdout.isatty', return_value=True):
        fore = getattr(ocflib.misc.shell, color)
        assert fore('hi') == fore('hi', tty_only=True) == getattr(Fore, color.upper()) + 'hi' + Fore.RESET

        bg = getattr(ocflib.misc.shell, 'bg_' + color)
        assert bg('hi') == bg('hi', tty_only=True) == getattr(Back, color.upper()) + 'hi' + Back.RESET


@pytest.mark.parametrize('color', ocflib.misc.shell.COLORS)
def test_color_wrappers_without_tty(color):
    with mock.patch('sys.stdout.isatty', return_value=False):
        fore = getattr(ocflib.misc.shell, color)
        assert fore('hi') == 'hi'

        bg = getattr(ocflib.misc.shell, 'bg_' + color)
        assert bg('hi') == 'hi'


@pytest.mark.parametrize('env,expected', [
    ({}, 'nano'),
    ({'VISUAL': 'vi'}, 'vi'),
    ({'VISUAL': 'vi', 'EDITOR': 'nano'}, 'vi'),
    ({'EDITOR': 'emacs'}, 'emacs'),
])
def test_get_editor(env, expected):
    with mock.patch('os.environ', env):
        assert get_editor() == expected
