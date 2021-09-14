#!/usr/bin/env python

# FIXME:
# We currently have some code duplicated in binderhub/binderspawner_mixin.py and
# helm-chart/binderhub/values.yaml
# We should remove the embedded code from values.yaml and install the required
# BinderSpawner code in the JupyterHub container.

# For now just check that the two are in sync
import argparse
import difflib
import os
import sys
import yaml

parser = argparse.ArgumentParser(description='Check embedded chart code')
parser.add_argument('--update', action='store_true', help='Update binderhub code from values.yaml')
args = parser.parse_args()

root = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.pardir)
binderspawner_mixin_py = os.path.join(root, 'binderhub', 'binderspawner_mixin.py')
values_yaml = os.path.join(root, 'helm-chart', 'binderhub', 'values.yaml')

with open(values_yaml) as f:
    values = yaml.safe_load(f)
    values_code = values['jupyterhub']['hub']['extraConfig']['0-binderspawnermixin'].splitlines()

if args.update:
    with open(binderspawner_mixin_py, 'w') as f:
        f.write(values['jupyterhub']['hub']['extraConfig']['0-binderspawnermixin'])
else:
    with open(binderspawner_mixin_py, 'r') as f:
        py_code = f.read().splitlines()

    difflines = list(difflib.context_diff(values_code, py_code))
    if difflines:
        print('\n'.join(difflines))
        print('\n')
        print('Values code is not in sync with binderhub/binderspawner_mixin.py')
        print('Run `python {} --update` to update binderhub/binderspawner_mixin.py from values.yaml'.format(sys.argv[0]))
        sys.exit(1)
