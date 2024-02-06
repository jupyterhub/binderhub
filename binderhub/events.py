"""
Emit structured, discrete events when various actions happen.
"""

import json
import logging
from datetime import datetime

import jsonschema
from jupyterhub.traitlets import Callable
from pythonjsonlogger import jsonlogger
from traitlets.config import Configurable


def _skip_message(record, **kwargs):
    """
    Remove 'message' from log record.

    It is always emitted with 'null', and we do not want it,
    since we are always emitting events only
    """
    del record["message"]
    return json.dumps(record, **kwargs)


class EventLog(Configurable):
    """
    Send structured events to a logging sink
    """

    handlers_maker = Callable(
        None,
        config=True,
        allow_none=True,
        help="""
        Callable that returns a list of logging.Handler instances to send events to.

        When set to None (the default), events are discarded.
        """,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.log = logging.getLogger(__name__)
        # We don't want events to show up in the default logs
        self.log.propagate = False
        self.log.setLevel(logging.INFO)

        if self.handlers_maker:
            self.handlers = self.handlers_maker(self)
            formatter = jsonlogger.JsonFormatter(json_serializer=_skip_message)
            for handler in self.handlers:
                handler.setFormatter(formatter)
                self.log.addHandler(handler)

        self.schemas = {}

    def register_schema(self, schema):
        """
        Register a given JSON Schema with this event emitter

        'version' and '$id' are required fields.
        """
        # Check if our schema itself is valid
        # This throws an exception if it isn't valid
        jsonschema.validators.validator_for(schema).check_schema(schema)

        # Check that the properties we require are present
        required_schema_fields = {"$id", "version"}
        for rsf in required_schema_fields:
            if rsf not in schema:
                raise ValueError(f"{rsf} is required in schema specification")

        # Make sure reserved, auto-added fields are not in schema
        reserved_fields = {"timestamp", "schema", "version"}
        for rf in reserved_fields:
            if rf in schema["properties"]:
                raise ValueError(
                    f"{rf} field is reserved by event emitter & can not be explicitly set in schema"
                )

        self.schemas[(schema["$id"], schema["version"])] = schema

    def emit(self, schema_name, version, event):
        """
        Emit event with given schema / version in a capsule.
        """
        if not self.handlers_maker:
            # If we don't have a handler setup, ignore everything
            return

        if (schema_name, version) not in self.schemas:
            raise ValueError(f"Schema {schema_name} version {version} not registered")
        schema = self.schemas[(schema_name, version)]
        jsonschema.validate(event, schema)

        capsule = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "schema": schema_name,
            "version": version,
        }
        capsule.update(event)
        self.log.info(capsule)
