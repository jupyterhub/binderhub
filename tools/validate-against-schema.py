#!/usr/bin/env python3
import os

import jsonschema
import yaml

here_dir = os.path.abspath(os.path.dirname(__file__))
schema_yaml = os.path.join(here_dir, os.pardir, "binderhub-service", "values.schema.yaml")
values_yaml = os.path.join(here_dir, os.pardir, "binderhub-service", "values.yaml")
lint_and_validate_values_yaml = os.path.join(
    here_dir, "templates", "lint-and-validate-values.yaml"
)

with open(schema_yaml) as f:
    schema = yaml.safe_load(f)
with open(values_yaml) as f:
    values = yaml.safe_load(f)
with open(lint_and_validate_values_yaml) as f:
    lint_and_validate_values = yaml.safe_load(f)

# Validate values.yaml against schema
print("Validating values.yaml against values.schema.yaml...")
jsonschema.validate(values, schema)
print("OK!")
print()

# Validate lint-and-validate-values.yaml against schema
print("Validating lint-and-validate-values.yaml against values.schema.yaml...")
jsonschema.validate(lint_and_validate_values, schema)
print("OK!")
