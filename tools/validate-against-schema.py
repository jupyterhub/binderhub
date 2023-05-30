#!/usr/bin/env python3
import os

import jsonschema
from ruamel.yaml import YAML

yaml = YAML()

here_dir = os.path.abspath(os.path.dirname(__file__))
schema_yaml = os.path.join(here_dir, os.pardir, "helm-chart/binderhub", "schema.yaml")
values_yaml = os.path.join(here_dir, os.pardir, "helm-chart/binderhub", "values.yaml")
lint_and_validate_values_yaml = os.path.join(
    here_dir, "templates", "lint-and-validate-values.yaml"
)
binderhub_chart_config_yaml = os.path.join(
    here_dir, os.pardir, "testing/k8s-binder-k8s-hub", "binderhub-chart-config.yaml"
)

with open(schema_yaml) as f:
    schema = yaml.load(f)
with open(values_yaml) as f:
    values = yaml.load(f)
with open(lint_and_validate_values_yaml) as f:
    lint_and_validate_values = yaml.load(f)
with open(binderhub_chart_config_yaml) as f:
    binderhub_chart_config_yaml = yaml.load(f)

# Validate values.yaml against schema
print("Validating values.yaml against schema.yaml...")
jsonschema.validate(values, schema)
print("OK!")
print()

# Validate lint-and-validate-values.yaml against schema
print("Validating lint-and-validate-values.yaml against schema.yaml...")
jsonschema.validate(lint_and_validate_values, schema)
print("OK!")
print()

# Validate lint-and-validate-values.yaml against schema
print("Validating binderhub-chart-config.yaml against schema.yaml...")
jsonschema.validate(lint_and_validate_values, schema)
print("OK!")
