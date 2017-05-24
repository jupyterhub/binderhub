# -*- coding: utf-8 -*-

import os
from os import path as op

title = 'Binder flow diagram'

font_face = 'Arial'
node_size = 12
node_small_size = 9
edge_size = 9
sensor_color = '#7bbeca'
source_color = '#ff6347'

nodes = dict(
    jhub='JupyterHub',
    bhub='BinderHub',
    gcr='gcr.io / DockerHub',
    build='Build Machine\n(s2i / Dockerfile)',
    image="Docker Image",
    user='User Interface'
)

services = ('jhub', 'gcr', 'bhub', 'build', 'user')
derivatives = ('image',)

edges = (
    ('bhub', 'jhub', 'SEND image registry information\nREDIRECT user interface to'),
    ('bhub', 'build', 'SEND repo name,\nbranch'),
    ('build', 'image', "IF image not already registered, or diff found:\nBUILD a"),
    ('build', 'bhub', "RETURN image registry information"),
    ('image', 'gcr', 'REGISTERED and SENT to\nonline repository'),
    ('user', 'bhub', "SEND repo,\nbranch, file"),
)

subgraphs = (
    [('gcr', 'jhub'),
     'External Services'],
)


def setup(app):
    app.connect('builder-inited', generate_flow_diagram)
    app.add_config_value('make_flow_diagram', True, 'html')


def setup_module():
    # HACK: Stop nosetests running setup() above
    pass


def generate_flow_diagram(app):
    out_dir = op.join(app.builder.outdir, '_static')
    if not op.isdir(out_dir):
        os.makedirs(out_dir)
    out_fname = op.join(out_dir, 'binder_flow.svg')
    make_flow_diagram = app is None or \
        bool(app.builder.config.make_flow_diagram)
    if not make_flow_diagram:
        print('Skipping flow diagram, webpage will have a missing image')
        return

    import pygraphviz as pgv
    g = pgv.AGraph(name=title, directed=True)

    for key, label in nodes.items():
        label = label.split('\n')
        if len(label) > 1:
            label[0] = ('<<FONT POINT-SIZE="%s">' % node_size
                        + label[0] + '</FONT>')
            for li in range(1, len(label)):
                label[li] = ('<FONT POINT-SIZE="%s"><I>' % node_small_size
                             + label[li] + '</I></FONT>')
            label[-1] = label[-1] + '>'
            label = '<BR/>'.join(label)
        else:
            label = label[0]
        g.add_node(key, shape='plaintext', label=label)

    # Create and customize nodes and edges
    for edge in edges:
        g.add_edge(*edge[:2])
        e = g.get_edge(*edge[:2])
        if len(edge) > 2:
            e.attr['label'] = ('<<I>' +
                               '<BR ALIGN="LEFT"/>'.join(edge[2].split('\n')) +
                               '<BR ALIGN="LEFT"/></I>>')
        e.attr['fontsize'] = edge_size

    # Change colors
    for these_nodes, color in zip((services, derivatives),
                                  (sensor_color, source_color)):
        for node in these_nodes:
            g.get_node(node).attr['fillcolor'] = color
            g.get_node(node).attr['style'] = 'filled'

    # Create subgraphs
    for si, subgraph in enumerate(subgraphs):
        g.add_subgraph(subgraph[0], 'cluster%s' % si,
                       label=subgraph[1], color='black')

    # Format (sub)graphs
    for gr in g.subgraphs() + [g]:
        for x in [gr.node_attr, gr.edge_attr]:
            x['fontname'] = font_face
    g.node_attr['shape'] = 'box'
 
    g.layout('dot')
    g.draw(out_fname, format='svg')
    return g


# This is useful for testing/iterating to see what the result looks like
if __name__ == '__main__':
    from mne.io.constants import Bunch
    out_dir = op.abspath(op.join(op.dirname(__file__), '..', '_build', 'html'))
    app = Bunch(builder=Bunch(outdir=out_dir,
                              config=Bunch(make_flow_diagram=True)))
    g = generate_flow_diagram(app)
