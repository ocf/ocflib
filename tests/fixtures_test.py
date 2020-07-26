from contextlib import contextmanager

import mock
import pytest

# Shared testing components


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
