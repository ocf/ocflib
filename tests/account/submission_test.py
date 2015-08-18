from contextlib import contextmanager

import mock
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ocflib.account.submission import Base
from ocflib.account.submission import get_tasks
from ocflib.account.submission import StoredNewAccountRequest
from ocflib.account.submission import user_has_request_pending
from ocflib.account.submission import username_pending
from tests.account.creation_test import fake_credentials  # noqa
from tests.account.creation_test import fake_new_account_request  # noqa
from tests.account.creation_test import mock_rsa_key  # noqa


@pytest.fixture
def session(fake_credentials):
    engine = create_engine(fake_credentials.mysql_uri)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


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


@pytest.fixture
def celery_app():
    sent_messages = []

    def mock_celery_task(f):
        def wrapper(*args, **kwargs):
            f(*args, **kwargs)

        def update_state(**kwargs):
            pass

        # wrap everything in Mock so we can track calls
        return mock.Mock(
            side_effect=wrapper,
            delay=mock.Mock(side_effect=wrapper),
            update_state=mock.Mock(side_effect=update_state),
        )

    @contextmanager
    def dispatcher():
        def send(**kwargs):
            sent_messages.append(kwargs)
        yield mock.Mock(send=send)

    return mock.Mock(
        task=mock_celery_task,
        _sent_messages=sent_messages,
        **{
            'events.default_dispatcher': dispatcher,
        }
    )


@pytest.yield_fixture
def tasks(session, celery_app, fake_credentials):
    with mock.patch('ocflib.account.submission.sessionmaker', return_value=lambda: session):
        yield get_tasks(celery_app, credentials=fake_credentials)


@pytest.fixture
def session_with_requests(session, fake_new_account_request):
    session.add(StoredNewAccountRequest.from_request(fake_new_account_request))
    session.add(StoredNewAccountRequest.from_request(fake_new_account_request._replace(user_name='other')))
    session.commit()
    assert len(session.query(StoredNewAccountRequest).all()) == 2
    return session


def test_approve_request(celery_app, fake_new_account_request, session_with_requests, tasks):
    tasks.approve_request(fake_new_account_request.user_name)
    assert len(session_with_requests.query(StoredNewAccountRequest).all()) == 1

    # we want to make sure we go through the same conversion process:
    # live -> stored -> live -> dict
    request = StoredNewAccountRequest.from_request(fake_new_account_request).to_request()
    tasks.create_account.delay.assert_called_once_with(request)
    assert celery_app._sent_messages == [
        {'type': 'ocflib.account_approved', 'request': request.to_dict()}
    ]


@mock.patch('ocflib.account.submission.send_rejected_mail')
def test_reject_request(send_rejected_mail, celery_app, fake_new_account_request, session_with_requests, tasks):
    tasks.reject_request(fake_new_account_request.user_name)
    assert len(session_with_requests.query(StoredNewAccountRequest).all()) == 1

    # we want to make sure we go through the same conversion process:
    # live -> stored -> live -> dict
    request = StoredNewAccountRequest.from_request(fake_new_account_request).to_request()
    assert celery_app._sent_messages == [
        {'type': 'ocflib.account_rejected', 'request': request.to_dict()}
    ]

    # TODO: assert real reason
    send_rejected_mail.assert_called_once_with(request, mock.ANY)
