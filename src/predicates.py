from pypika import CustomFunction, Query, Table, Criterion

Samples = Table('samples')
Regexp = CustomFunction('REGEXP', ['expr', 'item'])

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
