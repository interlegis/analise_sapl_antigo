# -*- coding: utf-8 -*-
import os
from collections import defaultdict

basedir = "skins"


class Source(object):

    def __init__(self, root, filename):
        self.path = os.path.join(root, filename)
        self.id, self.extension = os.path.splitext(self.path)
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


byext = defaultdict(list)
sources = {}
metadata = []
for root, dirs, files in os.walk(basedir):
    for f in files:
        source = Source(root[len(basedir) + 1:], f)
        if source.metaref:
            metadata.append(source)
        else:
            byext[source.extension].append(source)
            sources[source.id] = source
# associate metadata
orphan_metadata = []
for meta in metadata:
    if meta.metaref in sources:
        sources[meta.metaref].metadata = meta
    else:
        orphan_metadata.append(meta)
