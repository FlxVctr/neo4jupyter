import json
from collections import namedtuple
from functools import partial
from os import path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from IPython.display import IFrame
from jinja2 import Template

VIS_VERSION = '4.16.1'
VIS_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/vis/{}/'.format(VIS_VERSION)

Node = namedtuple('Node', ['id', 'label', 'group', 'title'])
NodeProperties = namedtuple('NodeProperties', ['font', 'size'])
EdgeProperties = namedtuple('EdgeProperties', ['font', 'color'])


class Neo4Jupyter:

    def __init__(self, **kwargs):
        """
        Thise init function accepts a couple of kwargs:
        * vis_path: (str) Path to vis.js library (the default is to use CDN)
        * nodes_size: (int) Size of nodes (default: 25)
        * nodes_font: (int) Size of nodes font (default: 14)
        * edges_color: (str) CSS color for edges font (default: gray)
        * edges_font: (int) Size of edges font (default: 14)
        * template: (str) Path to the HTML template file (the default is the
          template.html inside the package directory)
        """
        self.id = uuid4()
        self.vis_path = kwargs.get('vis_path', VIS_CDN)
        self.node = NodeProperties(
            size=kwargs.get('nodes_size', 25),
            font=kwargs.get('nodes_font', 14)
        )
        self.edge = EdgeProperties(
            color=kwargs.get('edges_color', 'gray'),
            font=kwargs.get('edges_font', 14)
        )
        self.template_path = kwargs.get('template', None)

    @property
    def template(self):
        if not self.template_path:
            template_path = path.join(path.dirname(__file__), 'template.html')
        elif path.exists(self.template_path):
            template_path = self.template_path
        else:
            error = 'Template {} not found'.format(self.template_path)
            raise RuntimeError(error)

        with open(template_path, 'r') as handler:
            return handler.read()

    def vis_options(self, **kwargs):
        """Return the options (dict) data expected for a vis visualization."""
        node_prop = dict(
            shape='dot',
            size=self.node.size,
            font=dict(size=self.node.font)
        )

        edge_prop = dict(
            color=self.edge.color,
            font=dict(color=self.edge.color, align='middle'),
            arrows=dict(to=dict(enabled=True, scaleFactor=0.5)),
            smooth=dict(enabled=True)
        )

        return dict(
            nodes=node_prop,
            edges=edge_prop,
            physics=dict(enabled=kwargs.get('physics'))
        )

    def vis(self, nodes, edges, **kwargs):
        """
        Renders a Graph vis network from 3 dictionaries (nodes, edges &
        physics). A custom width and height (HTML attributes) can be passed as
        kwargs as well as the physics argument from plot method.
        """
        width = kwargs.get('width', '100%')
        height = kwargs.get('height', '400')

        data = dict(nodes=nodes, edges=edges)
        options = self.vis_options(**kwargs)

        template = Template(self.template)
        context = dict(
            id=self.id,
            vis_path=self.vis_path,
            data=json.dumps(data),
            options=json.dumps(options)
        )

        with NamedTemporaryFile() as handler:
            handler.write(template.render(**context))
            return IFrame(handler.name, width=width, height=height)

    def plot(self, graph, **kwargs):
        """
        The options argument should be a dictionary of node labels and property
        keys; it determines which property is displayed for the node label.

        For example, in a movie graph:
            options = {"Movie": "title", "Person": "name"}.

        Omitting a node label from the options dictionary will leave the node
        unlabeled in the visualization.

        Setting physics=True makes the nodes bounce around when you touch them!

        Width and height (HTML attributes) can also be set as strings (defaults
        are width='100%' and height='400') as well as a limit (default to 100).

        :param graph: (py2neo.Graph) Graph object
        """
        options = kwargs.get('options', dict())
        limit = kwargs.get('limit', 100)

        query = """
            MATCH (n)
            WITH n, rand() AS random
            ORDER BY random
            LIMIT {limit}
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN n AS source_node,
                id(n) AS source_id,
                r,
                m AS target_node,
                id(m) AS target_id
        """
        data = graph.run(query, limit=limit)
        nodes, edges = list(), list()
        get_info = partial(self.get_vis_info, options=options)

        for source_node, source_id, rel, target_node, target_id in data:
            source_info = get_info(source_node, source_id)

            if source_info not in nodes:
                nodes.append(source_info)

            if rel:
                target_info = get_info(target_node, target_id)
                relationship = {
                    'from': source_info.id,
                    'to': target_info.id,
                    'label': rel.type()
                }
                edges.append(relationship)
                if target_info not in nodes:
                    nodes.append(target_info)

        return self.vis(nodes, edges, **kwargs)

    @staticmethod
    def get_vis_info(node, id, **kwargs):
        node_label, *_ = node.labels()
        prop_key = kwargs.get(node_label)

        return Node(
            id=id,
            label=node.properties.get(prop_key, ''),
            group=node_label,
            title=repr(node.properties)
        )
