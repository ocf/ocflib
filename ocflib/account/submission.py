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

_AccountSubmissionTasks = namedtuple('AccountSubmissionTasks', [
    'create_account',
])


class NewAccountRequest(namedtuple('NewAccountRequest', [
    'user_name',
    'real_name',
    'is_group',
    'calnet_uid',
    'callink_oid',
    'email',
    'encrypted_password',
    'handle_warnings',
])):
    """Request for account creation.

    :param user_name:
    :param real_name:
    :param is_group:
    :param calnet_uid: uid (or None)
    :param callink_oid: oid (or None)
    :param email:
    :param encrypted_password:
    :param handle_warnings: one of WARNINGS_WARN, WARNINGS_SUBMIT,
                            WARNINGS_CREATE
        WARNINGS_WARN: don't create account, return warnings
        WARNINGS_SUBMIT: don't create account, submit for staff approval
        WARNINGS_CREATE: create the account anyway
    """
    WARNINGS_WARN = 'warn'
    WARNINGS_SUBMIT = 'submit'
    WARNINGS_CREATE = 'create'


class NewAccountResponse(namedtuple('NewAccountResponse', [
    'status',
    'errors',
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


def get_tasks(celery_app):
    """Return Celery tasks instantiated against the provided instance."""

    @celery_app.task
    def create_account(request):
        raise NotImplementedError()

    return _AccountSubmissionTasks(
        create_account=create_account,
    )
