"""New account submission.

The functions here are all Celery tasks that submit new accounts for creation.
Account creation always happens on the admin server (supernova), but new
accounts can be submitted from anywhere (e.g. accounts.ocf.berkeley.edu (atool)
or the approve command-line staff script).

A pre-requisite to using functions in this module is configuring Celery with an
appropriate broker and backend URL (probably Redis).

    from celery import Celery
    from ocflib.account.submission import get_tasks

    celery_app = Celery(broker='..', backend='..')
    tasks = get_tasks(celery_app)

    result = tasks.create_account.delay(..)

    # result is now an AsyncResult:
    # https://celery.readthedocs.org/en/latest/reference/celery.result.html#celery.result.AsyncResult
    #
    # You can immediately resolve it with result.wait(timeout=5), or grab
    # result.id and fetch it later.
"""
from collections import namedtuple
from contextlib import contextmanager

import redis
from redis.exceptions import LockError
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy import Integer
from sqlalchemy import LargeBinary
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import exists

from ocflib.account.creation import create_account as real_create_account
from ocflib.account.creation import NewAccountRequest
from ocflib.account.creation import send_rejected_mail
from ocflib.account.creation import validate_request
from ocflib.account.manage import change_password_with_keytab
from ocflib.account.manage import modify_ldap_attributes as real_modify_ldap_attributes


Base = declarative_base()


def username_pending(session, request):
    """Returns whether the username is currently pending creation."""
    return session.query(exists().where(
        StoredNewAccountRequest.user_name == request.user_name
    )).scalar()


def user_has_request_pending(session, request):
    """Returns whether the user has an account request pending.
    Checks based on CalNet UID / CalLink OID.
    """
    query = None
    if request.is_group and request.callink_oid != 0:
        query = StoredNewAccountRequest.callink_oid == request.callink_oid
    elif not request.is_group:
        query = StoredNewAccountRequest.calnet_uid == request.calnet_uid
    return (
        query is not None and
        session.query(exists().where(query)).scalar()
    )


class StoredNewAccountRequest(Base):
    """SQLAlchemy object for holding account requests."""

    __tablename__ = 'request'

    # TODO: enforce these lengths during submission as errors
    id = Column(Integer, primary_key=True)
    user_name = Column(String(255), unique=True, nullable=False)
    real_name = Column(String(255), nullable=False)
    is_group = Column(Boolean, nullable=False)
    calnet_uid = Column(Integer, nullable=True)
    callink_oid = Column(Integer, nullable=True)
    email = Column(String(255), nullable=False)
    encrypted_password = Column(LargeBinary(510), nullable=False)
    reason = Column(Text, nullable=False)

    def __str__(self):
        return '{self.user_name} ({type}: "{self.real_name}"), because: {self.reason}'.format(
            self=self,
            type='group' if self.is_group else 'individual',
        )

    @classmethod
    def from_request(cls, request, reason):
        """Create a StoredNewAccountRequest from a NewAccountRequest."""
        return cls(
            user_name=request.user_name,
            real_name=request.real_name,
            is_group=request.is_group,
            calnet_uid=request.calnet_uid,
            callink_oid=request.callink_oid,
            email=request.email,
            encrypted_password=request.encrypted_password,
            reason=reason,
        )

    def to_request(self, handle_warnings=NewAccountRequest.WARNINGS_CREATE):
        """Convert this object to a NewAccountRequest."""
        return NewAccountRequest(**dict(
            {
                field: getattr(self, field)
                for field in NewAccountRequest._fields
                if field in self.__table__.columns._data.keys()
            },
            handle_warnings=handle_warnings,
        ))


class NewAccountResponse(namedtuple('NewAccountResponse', [
    'status', 'errors',
])):
    """Response to an account creation request.

    :param status: one of CREATED, FLAGGED, PENDING, REJECTED
        CREATED: account was created successfully
        FLAGGED: account was flagged and not submitted; the response includes a
                 list of warnings. The user can choose to continue, and should
                 send another request with handle_warnings=WARNINGS_SUBMIT.
        PENDING: account was flagged and submitted; staff will manually review
                 it, and the user will receive an email in a few days
        REJECTED: account cannot be created due to a fatal error (e.g. username
                  already taken)
    :param errors: list of errors (or None)
    """
    CREATED = 'created'
    FLAGGED = 'flagged'
    PENDING = 'pending'
    REJECTED = 'rejected'


def get_tasks(celery_app, credentials=None):
    """Return Celery tasks instantiated against the provided instance."""
    # mysql, for stored account requests
    Session = None

    @contextmanager
    def get_session():
        nonlocal Session
        if Session is None:
            Session = sessionmaker(
                bind=create_engine(credentials.mysql_uri, poolclass=NullPool),
            )
        session = Session()
        try:
            yield session
        finally:
            session.close()

    # convenience function for dispatching Celery events
    def dispatch_event(event_type, **kwargs):
        with celery_app.events.default_dispatcher() as disp:
            disp.send(type=event_type, **kwargs)

    @celery_app.task
    def validate_then_create_account(request):
        """First run validation, then create.

        This is handy because this task runs quickly, so you can wait for it to
        finish (unlike create_account, which is slow and uses a global lock).

        If this task succeeds, it will launch create_account, and returns you
        the new task ID.

        Assuming this task succeeds, it is almost certain that create_account
        will succeed. However, create_account runs validation again, so it is
        possible for it to fail (just exceedingly unlikely).
        """
        # TODO: docstring is not 100% correct
        with get_session() as session:
            errors, warnings = validate_request(request, credentials, session)
        if errors:
            # Fatal errors; cannot be bypassed, even with staff approval
            return NewAccountResponse(
                status=NewAccountResponse.REJECTED,
                errors=(errors + warnings),
            )
        elif warnings:
            # Non-fatal errors; the frontend can choose to create the account
            # anyway, submit the account for staff approval, or get a response
            # with a list of warnings for further inspection.
            if request.handle_warnings == NewAccountRequest.WARNINGS_SUBMIT:
                stored_request = StoredNewAccountRequest.from_request(request, str(warnings))

                with get_session() as session:
                    session.add(stored_request)  # TODO: error handling
                    session.commit()

                dispatch_event(
                    'ocflib.account_submitted',
                    request=dict(request.to_dict(), reasons=warnings),
                )
                return NewAccountResponse(
                    status=NewAccountResponse.PENDING,
                    errors=warnings,
                )
            elif request.handle_warnings == NewAccountRequest.WARNINGS_WARN:
                return NewAccountResponse(
                    status=NewAccountResponse.FLAGGED,
                    errors=warnings,
                )

        return create_account.delay(request).id

    @celery_app.task
    def create_account(request):
        # TODO: docstring
        # lock account creation for up to 5 minutes
        r = redis.from_url(credentials.redis_uri)
        lock = r.lock('ocflib.account.submission.create_account', timeout=60 * 5)
        try:
            if not lock.acquire(blocking=True, blocking_timeout=60 * 5):
                raise RuntimeError('Couldn\'t lock account creation, abandoning.')

            # status reporting
            status = []

            def _report_status(line):
                """Update task status by adding the given line."""
                status.append(line)
                create_account.update_state(meta={'status': status})

            @contextmanager
            def report_status(start, stop, task):
                _report_status(start + ' ' + task)
                yield
                _report_status(stop + ' ' + task)

            with report_status('Validating', 'Validated', 'request'), \
                    get_session() as session:
                errors, warnings = validate_request(request, credentials, session)

            if errors:
                send_rejected_mail(request, str(errors))
                return NewAccountResponse(
                    status=NewAccountResponse.REJECTED,
                    errors=(errors + warnings),
                )

            # actual account creation
            real_create_account(request, credentials, report_status)
            dispatch_event('ocflib.account_created', request=request.to_dict())
            return NewAccountResponse(
                status=NewAccountResponse.CREATED,
                errors=[],
            )
        finally:
            try:
                lock.release()
            except LockError:
                pass

    @celery_app.task
    def get_pending_requests():
        with get_session() as session:
            return session.query(StoredNewAccountRequest).all()

    def get_remove_row_by_user_name(user_name):
        """Fetch stored request, then remove it."""
        with get_session() as session:
            request_row = session.query(StoredNewAccountRequest).filter(
                StoredNewAccountRequest.user_name == user_name
            ).first()
            session.delete(request_row)
            session.commit()
            return request_row

    @celery_app.task
    def approve_request(user_name):
        request = get_remove_row_by_user_name(user_name).to_request()
        create_account.delay(request)
        dispatch_event('ocflib.account_approved', request=request.to_dict())

    @celery_app.task
    def reject_request(user_name):
        stored_request = get_remove_row_by_user_name(user_name)
        request = stored_request.to_request()
        send_rejected_mail(request, stored_request.reason)
        dispatch_event('ocflib.account_rejected', request=request.to_dict())

    @celery_app.task
    def change_password(username, new_password, comment=None):
        """Change the password of a username.

        Only passwords for a regular user can be changed (e.g. can't change a
        /admin principal's password), and passwords are subject to validation.

        Users are notified via email of the change.

        :param comment: comment to include in notification email
        """
        change_password_with_keytab(
            username=username,
            password=new_password,
            keytab=credentials.kerberos_keytab,
            principal=credentials.kerberos_principal,
            comment=comment,
        )

    @celery_app.task
    def modify_ldap_attributes(username, attributes):
        """Modify the ldap attributes of a username.

        Validation is applied for e.g. the 'mail' and 'loginShell' fields, but
        this operation is not guaranteed to be safe.

        :param attributes: dictionary of attribute names and values
        """
        real_modify_ldap_attributes(
            username=username,
            attributes=attributes,
            keytab=credentials.kerberos_keytab,
            principal=credentials.kerberos_principal,
        )

    return _AccountSubmissionTasks(
        validate_then_create_account=validate_then_create_account,
        create_account=create_account,
        get_pending_requests=get_pending_requests,
        approve_request=approve_request,
        reject_request=reject_request,
        change_password=change_password,
        modify_ldap_attributes=modify_ldap_attributes,
    )

_AccountSubmissionTasks = namedtuple('AccountSubmissionTasks', [
    'validate_then_create_account',
    'create_account',
    'get_pending_requests',
    'approve_request',
    'reject_request',
    'change_password',
    'modify_ldap_attributes',
])

AccountCreationCredentials = namedtuple('AccountCreationCredentials', [
    'encryption_key', 'mysql_uri', 'kerberos_keytab', 'kerberos_principal', 'redis_uri',
])
