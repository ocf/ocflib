from contextlib import contextmanager

import mock
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ocflib.account.creation import NewAccountRequest
from ocflib.account.submission import Base
from ocflib.account.submission import get_tasks
from ocflib.account.submission import NewAccountResponse
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
        session.add(StoredNewAccountRequest.from_request(fake_new_account_request, 'reason'))
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
        session.add(StoredNewAccountRequest.from_request(fake_new_account_request, 'reason'))
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
        session.add(StoredNewAccountRequest.from_request(fake_new_account_request, 'reason'))
        session.commit()
        assert not user_has_request_pending(session, fake_new_account_request)


@pytest.fixture
def celery_app():
    sent_messages = []

    def mock_celery_task(f):
        def update_state(**kwargs):
            pass

        # wrap everything in Mock so we can track calls
        return mock.Mock(
            side_effect=f,
            delay=mock.Mock(),
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
    session.add(StoredNewAccountRequest.from_request(fake_new_account_request, 'reason'))
    session.add(StoredNewAccountRequest.from_request(
        fake_new_account_request._replace(user_name='other'),
        'reason',
    ))
    session.commit()
    assert len(session.query(StoredNewAccountRequest).all()) == 2
    return session


def test_approve_request(celery_app, fake_new_account_request, session_with_requests, tasks):
    tasks.approve_request(fake_new_account_request.user_name)
    assert len(session_with_requests.query(StoredNewAccountRequest).all()) == 1

    # we want to make sure we go through the same conversion process:
    # live -> stored -> live -> dict
    request = StoredNewAccountRequest.from_request(fake_new_account_request, 'reason').to_request()
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
    request = StoredNewAccountRequest.from_request(fake_new_account_request, 'reason').to_request()
    assert celery_app._sent_messages == [
        {'type': 'ocflib.account_rejected', 'request': request.to_dict()}
    ]

    # TODO: assert real reason
    send_rejected_mail.assert_called_once_with(request, mock.ANY)


def test_get_pending_requests(session_with_requests, tasks, fake_new_account_request):
    request = fake_new_account_request
    pending_requests = tasks.get_pending_requests()
    assert set(request.to_request() for request in pending_requests) == {
        StoredNewAccountRequest.from_request(request, 'reason').to_request(),
        StoredNewAccountRequest.from_request(
            request._replace(user_name='other'),
            'reason',
        ).to_request(),
    }


@contextmanager
def mock_validate_request(errors, warnings):
    with mock.patch(
        'ocflib.account.submission.validate_request',
        return_value=(errors, warnings),
    ):
        yield


@pytest.yield_fixture
def mock_real_create_account():
    with mock.patch('ocflib.account.submission.real_create_account') as m:
        yield m


class TestValidateThenCreateAccount:

    def test_validate_no_issues(
        self,
        tasks,
        fake_new_account_request,
        mock_real_create_account,
        fake_credentials,
        celery_app,
    ):
        with mock_validate_request([], []):
            resp = tasks.validate_then_create_account(fake_new_account_request)
            tasks.create_account.delay.assert_called_once_with(fake_new_account_request)
            assert resp == tasks.create_account.delay(fake_new_account_request).id

    @pytest.mark.parametrize('handle_warnings,expected', [
        (NewAccountRequest.WARNINGS_WARN, NewAccountResponse.FLAGGED),
        (NewAccountRequest.WARNINGS_SUBMIT, NewAccountResponse.PENDING),
        (NewAccountRequest.WARNINGS_CREATE, NewAccountResponse.CREATED),
    ])
    def test_validate_with_warnings(
        self,
        tasks,
        fake_new_account_request,
        fake_credentials,
        handle_warnings,
        expected,
        celery_app,
        session,
    ):
        assert len(session.query(StoredNewAccountRequest).all()) == 0
        with mock_validate_request([], ['ok warning']):
            request = fake_new_account_request._replace(
                handle_warnings=handle_warnings,
            )
            resp = tasks.validate_then_create_account(request)

            if expected == NewAccountResponse.CREATED:
                tasks.create_account.delay.assert_called_once_with(request)
                assert resp == tasks.create_account.delay(request).id
            else:
                assert resp == NewAccountResponse(
                    status=expected,
                    errors=['ok warning'],
                )

            if expected == NewAccountResponse.PENDING:
                assert celery_app._sent_messages == [
                    {
                        'type': 'ocflib.account_submitted',
                        'request': dict(request.to_dict(), reasons=['ok warning']),
                    }
                ]
                assert len(session.query(StoredNewAccountRequest).all()) == 1
            else:
                assert len(session.query(StoredNewAccountRequest).all()) == 0

    def test_validate_with_errors(
        self,
        tasks,
        fake_new_account_request,
        fake_credentials,
    ):
        with mock_validate_request(['bad error'], ['ok warning']):
            resp = tasks.validate_then_create_account(fake_new_account_request)
            assert resp == NewAccountResponse(
                status=NewAccountResponse.REJECTED,
                errors=['bad error', 'ok warning'],
            )
            assert not tasks.create_account.delay.called


@pytest.yield_fixture
def mock_redis_locking():
    with mock.patch('redis.from_url') as m:
        yield m


class TestCreateAccount:

    def test_create_no_issues(
        self,
        tasks,
        fake_new_account_request,
        mock_real_create_account,
        fake_credentials,
        celery_app,
        mock_redis_locking,
    ):
        with mock_validate_request([], []):
            resp = tasks.create_account(fake_new_account_request)
            assert resp == NewAccountResponse(
                status=NewAccountResponse.CREATED,
                errors=[],
            )
            mock_real_create_account.assert_called_once_with(
                fake_new_account_request,
                fake_credentials,
                mock.ANY,
                known_uid=mock.ANY,
            )
            mock_redis_locking().set.assert_called_once_with('known_uid', mock.ANY)
            assert celery_app._sent_messages == [
                {'type': 'ocflib.account_created', 'request': fake_new_account_request.to_dict()}
            ]

    @mock.patch('ocflib.account.submission.send_rejected_mail')
    def test_create_with_errors(
        self,
        send_rejected_mail,
        tasks,
        fake_new_account_request,
        mock_real_create_account,
        fake_credentials,
        mock_redis_locking,
    ):
        with mock_validate_request(['bad error'], ['ok warning']):
            resp = tasks.create_account(fake_new_account_request)
            assert resp == NewAccountResponse(
                status=NewAccountResponse.REJECTED,
                errors=['bad error', 'ok warning'],
            )
            assert not mock_real_create_account.called
            assert send_rejected_mail.called


class TestStoredNewAccountRequest:

    def test_str(self, fake_new_account_request):
        assert (
            str(StoredNewAccountRequest.from_request(fake_new_account_request, 'reason')) ==
            'someuser (individual: "Some User"), because: reason'
        )


def test_change_password(tasks, fake_credentials):
    with mock.patch('ocflib.account.submission.change_password_with_keytab') as m:
        tasks.change_password('ggroup', 'hello world', comment='comment')
        m.assert_called_once_with(
            username='ggroup',
            password='hello world',
            principal=fake_credentials.kerberos_principal,
            keytab=fake_credentials.kerberos_keytab,
            comment='comment',
        )


def test_modify_ldap_attributes(tasks, fake_credentials):
    with mock.patch('ocflib.account.submission.real_modify_ldap_attributes') as m:
        tasks.modify_ldap_attributes('ggroup', {'a': ['b', 'c'], 'd': ['e']})
        m.assert_called_once_with(
            username='ggroup',
            attributes={'a': ['b', 'c'], 'd': ['e']},
            keytab=fake_credentials.kerberos_keytab,
            principal=fake_credentials.kerberos_principal,
        )
