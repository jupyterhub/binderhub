import tempfile
import json
from contextlib import redirect_stderr
import logging
from binderhub.events import EventLog


def test_emit_launch():
    """
    Test emitting launch events works
    """
    with tempfile.NamedTemporaryFile() as f:
        handler = logging.FileHandler(f.name)
        el = EventLog(handlers_maker=lambda el: [handler])

        el.emit_launch('GitHub', 'test/test/master', 'success')
        handler.flush()

        f.seek(0)
        event_capsule = json.load(f)

        assert 'timestamp' in event_capsule
        # Remove timestamp from capsule when checking equality, since it is gonna vary
        del event_capsule['timestamp']
        assert event_capsule == {
            'schema': 'binderhub.jupyter.io/launch',
            'version': 1,
            'event': {'provider': 'GitHub', 'spec': 'test/test/master', 'status': 'success'}
        }
