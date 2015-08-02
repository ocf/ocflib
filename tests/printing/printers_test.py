import mock
import pytest

from ocflib.printing.printers import _snmp
from ocflib.printing.printers import get_lifetime_pages
from ocflib.printing.printers import get_maintkit
from ocflib.printing.printers import get_toner
from ocflib.printing.printers import OID_LIFETIME_PAGES_PRINTED
from ocflib.printing.printers import OID_MAINTKIT_CUR
from ocflib.printing.printers import OID_MAINTKIT_MAX
from ocflib.printing.printers import OID_TONER_CUR
from ocflib.printing.printers import OID_TONER_MAX


class TestSNMP:

    @mock.patch('ocflib.printing.printers.cmdgen')
    def test_snmp(self, cmdgen):
        cmdgen.CommandGenerator.return_value.getCmd.return_value = (
            None,
            None,
            None,
            [[OID_TONER_CUR, 500]],
        )

        assert _snmp('logjam', OID_TONER_CUR) == 500
        cmdgen.CommandGenerator.return_value.getCmd.assert_called_with(
            cmdgen.CommunityData('my-agent', 'public', 0),
            cmdgen.UdpTransportTarget(('logjam', 161)),
            OID_TONER_CUR,
        )

    @mock.patch('ocflib.printing.printers.cmdgen')
    @pytest.mark.parametrize('err_indication,err_status', [
        ('it broke', None),
        (None, 'it broke'),
    ])
    def test_errors(self, cmdgen, err_indication, err_status):
        cmdgen.CommandGenerator.return_value.getCmd.return_value = (
            err_indication,
            err_status,
            None,
            [[OID_TONER_CUR, 500]],
        )
        with pytest.raises(IOError):
            _snmp('logjam', OID_TONER_CUR)


@pytest.yield_fixture
def mock_snmp():
    with mock.patch('ocflib.printing.printers._snmp') as mock_snmp:
        def fake(host, oid):
            return {
                OID_TONER_MAX: 24000,
                OID_TONER_CUR: 500,
                OID_MAINTKIT_MAX: 100000,
                OID_MAINTKIT_CUR: 2000,
                OID_LIFETIME_PAGES_PRINTED: 500000,
            }[oid]

        mock_snmp.side_effect = fake
        yield


def test_get_toner(mock_snmp):
    assert get_toner('logjam') == [500, 24000]


def test_get_maintkit(mock_snmp):
    assert get_maintkit('logjam') == [2000, 100000]


def test_get_lifetime_pages(mock_snmp):
    assert get_lifetime_pages('logjam') == 500000
