import mock
import pytest

from ocflib.ucb.cas import verify_ticket


@pytest.yield_fixture
def mock_get():
    with mock.patch('requests.get') as mock_get:
        yield mock_get


GOOD_RESPONSE = """
<cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'>
        <cas:authenticationSuccess>
                <cas:user>1034192</cas:user>
        </cas:authenticationSuccess>
</cas:serviceResponse>"""  # noqa

BAD_RESPONSE = """
<cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'>
        <cas:authenticationFailure code='INVALID_TICKET'>
                ticket &#039;ST-832595-ZOm6NYCTBJO0d41jjL6l-ncas-p3.calnet.berkeley.edu&#039; not recognized
        </cas:authenticationFailure>
</cas:serviceResponse>"""  # noqa


class TestVerifyTicket:

    def test_good_ticket(self, mock_get):
        mock_get.return_value.text = GOOD_RESPONSE
        assert verify_ticket(
            'some-ticket',
            'https://accounts.ocf.berkeley.edu/',
        ) == '1034192'

        called_url = mock_get.call_args[0][0]
        start = 'https://auth.berkeley.edu/cas/serviceValidate?'
        assert called_url.startswith(start)

        params = called_url[len(start):].split('&')
        assert sorted(params) == [
            'service=https%3A%2F%2Faccounts.ocf.berkeley.edu%2F',
            'ticket=some-ticket',
        ]

    @pytest.mark.parametrize('response', [
        BAD_RESPONSE,
        '',
        'hello world',
    ])
    def test_bad_ticket(self, response, mock_get):
        mock_get.return_value.text = response
        assert verify_ticket(
            'some-ticket',
            'https://accounts.ocf.berkeley.edu/',
        ) is None
