"""Generate HTML binderhubs tables for team pages
"""
import pandas as pd
import os
import os.path as op
from ruamel import yaml

# Variables
N_PER_ROW = 4

# Code to generate the HTML grid
template_binderhub = '<td align="center" class="contrib_entry"><a href="{URL_BINDERHUB}"><img src="{LOGO}" class="fed_logo" alt="{RUN_BY}" /></a><br /><p class="name">{BINDERHUB_SUBDOMAIN}</p><br /><p class="name">Run by</p><p class="name"><b><a href={RUN_BY_LINK}>{RUN_BY}</a></b></p><br /><a href={FUNDED_BY_LINK}><p class="name">Funded by</p><p class="name"><b>{FUNDED_BY}</b></p>'


def _generate_binderhubs(binderhubs):
    """Generate an HTML list of BinderHubs, given a dataframe of their information."""
    s = ['<table class="docutils binderhubs">', '<tr class="row-even">']
    for ix, binderhub in binderhubs.iterrows():
        if ix % N_PER_ROW == 0 and ix != 0:
            s += ['</tr><tr class="row-even">']

        # Add user
        format_dict = dict(
            URL_BINDERHUB=binderhub["url_binderhub"],
            BINDERHUB_SUBDOMAIN=binderhub["url_binderhub"].split("//")[-1],
            LOGO=binderhub["logo"],
            RUN_BY=binderhub["run_by"],
            RUN_BY_LINK=binderhub["run_by_link"],
            FUNDED_BY=binderhub["funded_by"],
            FUNDED_BY_LINK=binderhub["funded_by_link"],
        )

        # Render
        s += [template_binderhub.format(**format_dict)]
    s += ["</table>"]
    final_text = [".. raw:: html", ""]
    for line in s:
        final_text += ["   " + line]
    final_text = "\n".join(final_text)
    return final_text


# Run the function
path_data = op.join(
    op.dirname(op.abspath(__file__)), "..", "federation", "data-federation.yml"
)
yaml = yaml.YAML()

with open(path_data, "r") as ff:
    data = yaml.load(ff)

binderhubs = pd.DataFrame(data)
table = _generate_binderhubs(binderhubs)
new_name = os.path.splitext(path_data)[0]
with open(new_name + ".txt", "w") as ff:
    ff.write(table)
