import tempfile
import json
import logging
from binderhub.events import EventLog
import pytest
import jsonschema
import os


def test_register_invalid():
    """
    Test registering invalid schemas fails
    """
    el = EventLog()
    with pytest.raises(jsonschema.SchemaError):
        el.register_schema({
            # Totally invalid
            'properties': True
        })

    with pytest.raises(ValueError):
        el.register_schema({
            'properties': {}
        })

    with pytest.raises(ValueError):
        el.register_schema({
            '$id': 'something',
            '$version': 1,
            'properties': {
                'timestamp': {
                    'type': 'string'
                }
            }
        })



def test_emit_event():
    """
    Test emitting launch events works
    """
    schema = {
        '$id': 'test/test',
        'version': 1,
        'properties': {
            'something': {
                'type': 'string'
            },
        },
    }
    with tempfile.NamedTemporaryFile() as f:
        handler = logging.FileHandler(f.name)
        el = EventLog(handlers_maker=lambda el: [handler])
        el.register_schema(schema)

        el.emit('test/test', 1, {
            'something': 'blah',
        })
        handler.flush()

        f.seek(0)
        event_capsule = json.load(f)

        assert 'timestamp' in event_capsule
        # Remove timestamp from capsule when checking equality, since it is gonna vary
        del event_capsule['timestamp']
        assert event_capsule == {
            'schema': 'test/test',
            'version': 1,
            'something': 'blah'
        }


def test_emit_event_badschema():
    """
    Test failure when event doesn't match schema
    """
    schema = {
        '$id': 'test/test',
        'version': 1,
        'properties': {
            'something': {
                'type': 'string'
            },
            'status': {
                'enum': ['success', 'failure']
            }
        }
    }
    with tempfile.NamedTemporaryFile() as f:
        handler = logging.FileHandler(f.name)
        el = EventLog(handlers_maker=lambda el: [handler])
        el.register_schema(schema)

        with pytest.raises(jsonschema.ValidationError):
            el.emit('test/test', 1, {
                'something': 'blah',
                'status': 'not-in-enum'
            })


async def test_provider_completeness(app):
    """
    Test we add an entry in the launch schema for all providers
    """
    repo_providers = {
        rp.name.default_value for rp in app.repo_providers.values()
    }

    launch_schema_path = os.path.join(os.path.dirname(__file__), '..', 'event-schemas', 'launch.json')

    with open(launch_schema_path) as f:
        launch_schema = json.load(f)

    assert repo_providers == set(launch_schema['properties']['provider']['enum'])
