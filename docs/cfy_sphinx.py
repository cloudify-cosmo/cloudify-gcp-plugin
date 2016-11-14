
import os
from abc import ABCMeta, abstractproperty
from copy import deepcopy

import yaml

from docutils import nodes
from sphinx import addnodes
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, ObjType


with open(os.path.join(os.path.dirname(__file__), '..', 'plugin.yaml')) as f:
    plugin = yaml.load(f)

plugin_undocumented = deepcopy(plugin)


class node(nodes.Element):
    pass


def visit_node_node(self, node):
    print("visit_node_node called")


def depart_node_node(self, node):
    print("depart_node_node called")


def check_all_types_documented(app):
    for section in [
            'node_types',
            'relationships',
            ]:
        for item in plugin_undocumented[section]:
            app.warn('{item} from {section} has not been documented!'.format(
                item=item,
                section=section,
                ))


def build_finished(app, exception):
    check_all_types_documented(app)


class CfyDirective(ObjectDescription):
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        super(CfyDirective, self).__init__(*args, **kwargs)

        self.data = plugin_undocumented[self.section].pop(
                self.arguments[0].strip())

    def handle_signature(self, sig, signode):
        signode.append(addnodes.desc_name(sig, sig))
        signode.append(addnodes.desc_returns(
            self.data['derived_from'],
            self.data['derived_from'],
            ))

    def after_contentnode(self, node):
        if 'properties' in self.data:
            node.append(nodes.rubric('', 'Properties:'))
            props = nodes.definition_list()
            node.append(props)
            for name, property in self.data['properties'].items():
                props.append(nodes.definition_list_item(
                    '',
                    nodes.term('', name),
#                    nodes.definition(
#                        '',
#                        nodes.Text('', property['description'])),
                    ))

    def run(self):
        indexnode, node = super(CfyDirective, self).run()

        self.after_contentnode(node)

        return [indexnode, node]

    @abstractproperty
    def section():
        """
        Name of the section in `plugin.yaml` for this type.
        """


class Node(CfyDirective):
    section = 'node_types'


class Relationship(CfyDirective):
    section = 'relationships'


class CfyDomain(Domain):

    name = 'cfy'
    description = 'Cloudify DSL'

    object_types = {
            'node': ObjType('node'),
            'rel': ObjType('rel', 'relationship'),
            }

    directives = {
            'node': Node,
            'rel': Relationship,
            }


def setup(app):
    app.add_domain(CfyDomain)

    app.connect('build-finished', build_finished)

    return {'version': '0.1'}
