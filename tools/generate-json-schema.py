#!/usr/bin/env python3
"""
This script reads schema.yaml and generates a values.schema.json that we can
package with the Helm chart, allowing helm the CLI to perform validation.

While we can directly generate a values.schema.json from schema.yaml, it
contains a lot of description text we use to generate our configuration
reference that isn't helpful to ship along the validation schema. Due to that,
we trim away everything that isn't needed.
"""

import json
import os
from collections.abc import MutableMapping

from ruamel.yaml import YAML

yaml = YAML()

here_dir = os.path.abspath(os.path.dirname(__file__))
schema_yaml = os.path.join(here_dir, os.pardir, "helm-chart/binderhub", "schema.yaml")
values_schema_json = os.path.join(
    here_dir, os.pardir, "helm-chart/binderhub", "values.schema.json"
)


def clean_jsonschema(d, parent_key=""):
    """
    Modifies a dictionary representing a jsonschema in place to not contain
    jsonschema keys not relevant for a values.schema.json file solely for use by
    the helm CLI.
    """
    JSONSCHEMA_KEYS_TO_REMOVE = {"description"}

    # start by cleaning up the current level
    for k in set.intersection(JSONSCHEMA_KEYS_TO_REMOVE, set(d.keys())):
        del d[k]

    # Recursively cleanup nested levels, bypassing one level where there could
    # be a valid Helm chart configuration named just like the jsonschema
    # specific key to remove.
    if "properties" in d:
        for k, v in d["properties"].items():
            if isinstance(v, MutableMapping):
                clean_jsonschema(v, k)


def run():
    # Using these sets, we can validate further manually by printing the results
    # of set operations.
    with open(schema_yaml) as f:
        schema = yaml.load(f)

    # Drop what isn't relevant for a values.schema.json file packaged with the
    # Helm chart, such as the description keys only relevant for our
    # configuration reference.
    clean_jsonschema(schema)

    # dump schema to values.schema.json
    with open(values_schema_json, "w") as f:
        json.dump(schema, f)

    print("binderhub/values.schema.json created")


run()
