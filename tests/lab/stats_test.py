from ocflib.lab.stats import list_desktops


def test_list_desktops():
    desktops = list_desktops()
    assert 10 < len(desktops) < 50

    assert 'eruption' in desktops
    assert 'destruction' in desktops

    assert 'death' not in desktops


def test_list_desktops_staff_only():
    desktops = list_desktops(public_only=True)
    assert 10 < len(desktops) < 50

    assert 'destruction' in desktops

    assert 'eruption' not in desktops
    assert 'death' not in desktops
