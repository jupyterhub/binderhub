#!/usr/bin/env python

# FIXME: We currently have some code duplicated in
#        binderhub/binderspawner_mixin.py and helm-chart/binderhub/values.yaml
#        and we use a pre-commit hook to automatically update the values in
#        values.yaml.
#
#        We should remove the embedded code from values.yaml and install the required
#        BinderSpawner code in the JupyterHub container.
#

# For now just check that the two are in sync
import argparse
import difflib
import os
import sys

from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)

parser = argparse.ArgumentParser(description="Check embedded chart code")
parser.add_argument(
    "--update", action="store_true", help="Update binderhub code from values.yaml"
)
args = parser.parse_args()

root = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.pardir)
binderspawner_mixin_py = os.path.join(root, "binderhub", "binderspawner_mixin.py")
values_yaml = os.path.join(root, "helm-chart", "binderhub", "values.yaml")

with open(binderspawner_mixin_py) as f:
    py_code = f.read()


if args.update:
    with open(values_yaml) as f:
        values = yaml.load(f)
    values_code = values["jupyterhub"]["hub"]["extraConfig"]["0-binderspawnermixin"]
    if values_code != py_code:
        print(f"Generating {values_yaml} from {binderspawner_mixin_py}")
        values["jupyterhub"]["hub"]["extraConfig"]["0-binderspawnermixin"] = py_code
        with open(values_yaml, "w") as f:
            yaml.dump(values, f)
else:
    with open(values_yaml) as f:
        values = yaml.load(f)
    values_code = values["jupyterhub"]["hub"]["extraConfig"]["0-binderspawnermixin"]

    difflines = list(
        difflib.context_diff(values_code.splitlines(), py_code.splitlines())
    )
    if difflines:
        print("\n".join(difflines))
        print("\n")
        print("Values code is not in sync with binderhub/binderspawner_mixin.py")
        print(
            f"Run `python {sys.argv[0]} --update` to update values.yaml from binderhub/binderspawner_mixin.py"
        )
        sys.exit(1)
