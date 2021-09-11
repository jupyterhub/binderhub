#!/usr/bin/env python

import os
from ruamel.yaml import YAML

yaml = YAML()
here = os.path.dirname(os.path.abspath(__file__))


values_yaml = os.path.join(here, os.pardir, "helm-chart", "binderhub", "values.yaml")
binderspawner_mixin_py = os.path.join(here, os.pardir, "binderhub", "binderspawner_mixin.py")

with open(values_yaml) as f:
    values = yaml.load(f)

with open(binderspawner_mixin_py) as f:
    code = f.read()

replace_str = 'from binderhub.binderspawner_mixin import BinderSpawnerMixin'
values['jupyterhub']['hub']['extraConfig']['00-binder'] = values['jupyterhub']['hub']['extraConfig']['00-binder'].replace(replace_str, code)

with open(values_yaml, 'w') as f:
    yaml.dump(values, f)
