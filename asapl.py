# -*- coding: utf-8 -*-
import HTMLParser
import os
from collections import defaultdict

import matplotlib.pyplot as plt
import networkx as nx


basedir = "skins"
sources = {}
orphan_metadata = []

EXTENSIONS = dict(
    python=['py', 'cpy', ],
    templates=['dtml', 'zsql', 'cpt', 'pt', ],
    other_sources=['metatada', 'js', ],

    binary=['gif', 'ico', 'jar', 'jpg', 'png', 'swf', 'zip', ],
    extras=['ext', 'props', ],
)


def dot_extension(exts):
    return ['.' + e for e in exts]

IGNORED_ENDINGS = ['~', 'Thumbs.db', 'license.txt', 'logo_casa'] + dot_extension(
    EXTENSIONS['binary'] + EXTENSIONS['extras'])


class Source(object):

    def __init__(self, basedir, root, filename):
        self.path = os.path.join(root, filename)
        self.id, self.extension = os.path.splitext(self.path[len(basedir) + 1:])
        self.id = self.id.replace('/', '.')
        self.extension = self.extension[1:]
        self.metadata = None

    def __repr__(self):
        return '%s - %s [%s]%s' % (
            self.extension.upper(),
            self.id,
            self.path,
            ' (WITH METADATA)' if self.metadata else '')

    @property
    def metaref(self):
        if self.extension == 'metadata':
            return os.path.splitext(self.id)[0]

    @property
    def contents(self):
        if not hasattr(self, '_contents'):
            with open(self.path, 'r') as f:
                self._original_contents = f.read()
                decoded = self._original_contents.decode('utf-8')
                h = HTMLParser.HTMLParser()
                self._contents = h.unescape(decoded)
        return self._contents

    @property
    def deps(self):
        if not hasattr(self, '_deps'):
            self._deps = [source for source in sources.values()
                          if source.id in self.contents]
        return self._deps

    # UTILS
    def subl(self):
        os.system('subl %s' % s.path)


# collect sources
byext = defaultdict(list)
metadata = []
for root, dirs, files in os.walk(basedir):
    for f in files:
        if any(f.endswith(ig) for ig in IGNORED_ENDINGS):
            continue
        source = Source(basedir, root, f)
        if source.metaref:
            metadata.append(source)
        else:
            byext[source.extension].append(source)
            sources[source.id] = source
# associate metadata
for meta in metadata:
    if meta.metaref in sources:
        sources[meta.metaref].metadata = meta
    else:
        orphan_metadata.append(meta)

# adjustments
del sources['index_html']
del sources['mensagem_emitir']
del sources['standard_html_footer']
del sources['standard_html_header']


def mark_backrefs():
    for source in sources.values():
        source.backrefs = []
    for source in sources.values():
        for dep in source.deps:
            dep.backrefs.append(source)

mark_backrefs()


def build_graph(source_list):
    D = nx.DiGraph()
    for source in source_list:
        D.add_node(source.id)
        for dep in source.deps:
            if dep in source_list:
                D.add_edge(source.id, dep.id)
    return D


def build_all_sources_graph():
    return build_graph(sources.values())


def show(G):
    nx.draw_graphviz(G, with_labels=True)
    plt.show()


def connected(graph):
    if isinstance(graph, nx.DiGraph):
        graph = graph.to_undirected()
    return list(nx.connected_component_subgraphs(graph))


######################################################################
# ANALISE

count_backrefs = sorted([(len(s.backrefs), s.id) for s in sources.values() if len(s.backrefs) > 0])


def subl(source_list):
    os.system('subl ' + ' '.join(s.path for s in source_list))
