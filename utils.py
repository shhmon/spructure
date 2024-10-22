import os
import shutil

from pypika import CustomFunction, Query, Table, Criterion

Samples = Table('samples')
Regexp = CustomFunction('REGEXP', ['expr', 'item'])

class Path:
    def __init__(self, *args):
        self.args = args

    def append(self, *args):
        return Path(*self.args, *args)

    def fuzzy_find(self, query):
        path = str(self)
        file = None

        try:
            if os.path.isdir(path):
                file = next(entry.path for entry in os.scandir(path) if query in entry.name)
        except: pass

        return file

    def make_directory(self):
        path = str(self)
        if not os.path.isdir(path): os.mkdir(path)
        return self

    def clear_directory(self):
        path = str(self)
        if os.path.isdir(path): shutil.rmtree(path)
        os.mkdir(path)
        return self

    def __str__(self):
        return os.path.join(*self.args)

class SampleWrapper:
    def __init__(self, sample):
        self.sample = sample
        self.path = sample[1]
        self.hash = sample[8]
        self.filename = sample[10]

class RawSql(Criterion):
    def __init__(self, raw_sql, alias=None):
        super().__init__(alias)
        self.raw_sql = raw_sql

    def fields(self):
        return []

    def get_sql(self, **_):
        return self.raw_sql

def add_predicates(node, query = None):
    tag_regex = node.get('tag_regex')
    file_regex = node.get('file_regex')
    key_regex = node.get('key_regex')
    sample_type = node.get('sample_type')
    custom_where = node.get('where')
    
    if not query:
        query = Query().from_(Samples).select('*').where(Samples.local_path.notnull())

    if custom_where:
        for predicate in custom_where:
            query = query.where(RawSql(predicate))

    if key_regex:
        query = query.where(Regexp(key_regex, Samples.audio_key) | Regexp(key_regex, Samples.filename))
    if tag_regex:
        query = query.where(Regexp(tag_regex, Samples.tags))
    if file_regex:
        query = query.where(Regexp(file_regex, Samples.filename))
    if sample_type:
        query = query.where(Samples.sample_type == sample_type)
    
    return query

