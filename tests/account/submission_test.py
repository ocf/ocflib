import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ocflib.account.submission import Base
from ocflib.account.submission import StoredNewAccountRequest
from ocflib.account.submission import user_has_request_pending
from ocflib.account.submission import username_pending
from tests.account.creation_test import fake_new_account_request  # noqa
from tests.account.creation_test import mock_rsa_key  # noqa


@pytest.yield_fixture
def session():
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine)()


class TestUsernamePending:

    def test_pending(self, session, fake_new_account_request):
        session.add(StoredNewAccountRequest.from_request(fake_new_account_request))
        session.commit()
        assert username_pending(session, fake_new_account_request)

    def test_not_pending(self, session, fake_new_account_request):
        assert not username_pending(session, fake_new_account_request)


class TestUserHasRequestPending:

    @pytest.mark.parametrize('attrs', [
        {'is_group': True, 'calnet_uid': None, 'callink_oid': 14},
        {'is_group': False, 'calnet_uid': 14, 'callink_oid': None},
    ])
    def test_has_pending(self, session, fake_new_account_request, attrs):
        fake_new_account_request = fake_new_account_request._replace(**attrs)
        session.add(StoredNewAccountRequest.from_request(fake_new_account_request))
        session.commit()
        assert user_has_request_pending(session, fake_new_account_request)

    def test_not_has_pending(self, session, fake_new_account_request):
        assert not user_has_request_pending(session, fake_new_account_request)

    def test_not_has_pending_zero_group(self, session, fake_new_account_request):
        """callink_oid=0 can create infinite accounts."""
        fake_new_account_request = fake_new_account_request._replace(
            is_group=True,
            callink_oid=0,
            calnet_uid=None,
        )
        session.add(StoredNewAccountRequest.from_request(fake_new_account_request))
        session.commit()
        assert not user_has_request_pending(session, fake_new_account_request)
