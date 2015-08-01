from colorama import Fore, Back

import ocflib.misc.shell


def test_shell_quote():
    assert ocflib.misc.shell.escape_arg


def test_color_wrappers():
    for color in ocflib.misc.shell.COLORS:
        fore = getattr(ocflib.misc.shell, color)
        assert fore('hi') == getattr(Fore, color.upper()) + 'hi' + Fore.RESET

        bg = getattr(ocflib.misc.shell, 'bg_' + color)
        assert bg('hi') == getattr(Back, color.upper()) + 'hi' + Back.RESET
