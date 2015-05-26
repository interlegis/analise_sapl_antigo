# -*- coding: utf-8 -*-
import HTMLParser
import os
from collections import defaultdict

import matplotlib.pyplot as plt
import networkx as nx


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
        return '%s [%s]%s' % (
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

    def subl(self):
        os.system('subl %s' % self.path)


utils = ['index_html',
         'mensagem_emitir',
         'standard_html_footer',
         'standard_html_header',
         'pysc.data_converter_pysc',
         'pysc.PageListOutput_pysc',
         'pysc.verifica_conector_bd_pysc',
         'materia_header',
         'mensagem_popup_emitir',
         'standard_css_slot',
         'pysc.sessao_plenaria_log_pysc',
         'pysc.periodo_legislatura_format_pysc',
         'pysc.port_to_iso_pysc',
         'pysc.iso_to_port_pysc',
         'pysc.extrai_id_pysc',
         'pysc.ano_abrevia_pysc',
         'pysc.browser_verificar_pysc',
         'documento_header',
         'zsql.trans_rollback_zsql',
         'zsql.trans_begin_zsql',
         'zsql.trans_commit_zsql',
         'pysc.username_pysc',
         'pysc.data_atual_iso_pysc',
         'pysc.data_converter_por_extenso_pysc'
         ]


class Codebase(object):

    def __init__(self, basedir='skins'):
        self.basedir = basedir

        self.source_dict = {}
        self.orphan_metadata = []

        # collect sources
        metadata = []
        for root, dirs, files in os.walk(basedir):
            for f in files:
                if any(f.endswith(ig) for ig in IGNORED_ENDINGS):
                    continue
                source = Source(basedir, root, f)
                if source.metaref:
                    metadata.append(source)
                else:
                    self.source_dict[source.id] = source
        # associate metadata
        for meta in metadata:
            if meta.metaref in self.source_dict:
                self.source_dict[meta.metaref].metadata = meta
            else:
                self.orphan_metadata.append(meta)
        # remove utils
        for util in utils:
            del self.source_dict[util]
        # preset deps
        source_list = self.source_dict.values()
        for source in source_list:
            source._alldeps = [dep for dep in source_list if dep.id in source.contents]
        self.redep()

    def redep(self):
        for source in self.source_dict.values():
            source.deps, source.backrefs = [], []
        for source in self.source_dict.values():
            for dep in self.source_dict.values():
                if dep in source._alldeps:
                    source.deps.append(dep)
                    dep.backrefs.append(source)

    @property
    def sources(self):
        return self.source_dict.values()

    def util(self, source_or_id):
        if isinstance(source_or_id, str):
            source = self.source_dict[source_or_id]
        else:
            source = source_or_id
        utils.append(source.id)
        del self.source_dict[source.id]

    def count_backrefs(self, min=0, max=float("inf")):
        return sorted([(len(s.backrefs), s)
                       for s in self.sources if min <= len(s.backrefs) <= max])

    def prune(self, min=0):
        for l, source in self.count_backrefs(min):
            del self.source_dict[source.id]

    def build_graph(self):
        self.redep()

        D = nx.DiGraph()
        for source in self.sources:
            D.add_node(source.id)
            for dep in source.deps:
                if dep in self.sources:
                    D.add_edge(source.id, dep.id)
        return D

    def subl(self, source=None):
        if source is None:
            source = raw_input()
        if isinstance(source, str):
            if source in self.source_dict:
                source = self.source_dict[source]
            else:
                return
        source.subl()


def redigraph(graph, digraph):
    new = nx.DiGraph()
    new.add_nodes_from(graph)
    new.add_edges_from(
        (a, b) if (a, b) in digraph.edges() else (b, a)
        for a, b in graph.edges())
    return new


def show(graph):
    nx.draw_graphviz(graph, with_labels=True, font_size=20)
    plt.show()


def connected(graph):
    is_digraph = isinstance(graph, nx.DiGraph)
    undirected = graph.to_undirected() if is_digraph else graph
    components = nx.connected_component_subgraphs(undirected)
    if is_digraph:
        components = (redigraph(g, graph) for g in components)
    return list(components)


######################################################################
# tools

cb = Codebase()


def subl(sources):
    os.system('subl ' + ' '.join(s.path for s in sources))
