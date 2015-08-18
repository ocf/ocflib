import mock
import pytest
from colorama import Back
from colorama import Fore

import ocflib.misc.shell
from ocflib.misc.shell import get_editor


def test_shell_quote():
    assert ocflib.misc.shell.escape_arg


def test_color_wrappers():
    for color in ocflib.misc.shell.COLORS:
        fore = getattr(ocflib.misc.shell, color)
        assert fore('hi') == getattr(Fore, color.upper()) + 'hi' + Fore.RESET

        bg = getattr(ocflib.misc.shell, 'bg_' + color)
        assert bg('hi') == getattr(Back, color.upper()) + 'hi' + Back.RESET


@pytest.mark.parametrize('env,expected', [
    ({}, 'nano'),
    ({'VISUAL': 'vi'}, 'vi'),
    ({'VISUAL': 'vi', 'EDITOR': 'nano'}, 'vi'),
    ({'EDITOR': 'emacs'}, 'emacs'),
])
def test_get_editor(env, expected):
    with mock.patch('os.environ', env):
        assert get_editor() == expected
