from pypika import Query, Table, CustomFunction
import subprocess
import zipfile
import sqlite3
import shutil
import click
import json
import re
import os

from utils import PathBuilder

with open ('./config/config.json', 'r') as f:
    config = json.loads(f.read())
with open ('./config/hierarchy.json', 'r') as f:
    hierarchy = json.loads(f.read())

sort_path = PathBuilder(config.get('sorted_dir'))

Samples = Table('samples')
Regexp = CustomFunction('REGEXP', ['expr', 'item'])

def init_db():
    print('Initializing DB')

    username = config.get('username')
    
    def regexp(expr, item):
        try:
            reg = re.compile(expr)
            return reg.search(item) is not None
        except Exception as e:
            print(e)
    
    db = sqlite3.connect(f'./logs/users/default/{username}/sounds.db')
    db.create_function("REGEXP", 2, regexp)

    return db

def reset_filetree():
    print('Resetting filetree')

    path = sort_path.settle()

    if os.path.isdir(path): shutil.rmtree(path)
    os.mkdir(path)

def get_samples(db: sqlite3.Connection, cat: dict, sample_type = None):
    execute = lambda query: db.execute(str(query)).fetchall()

    samples = Table('samples')
    Regexp = CustomFunction('REGEXP', ['expr', 'item'])

    if 'query' in cat:
        return execute(cat.get('query'))
    else:
        query = Query \
            .from_(samples) \
            .select('*') \
            .where(samples.local_path.notnull()) \
            .where(Regexp(cat.get('tag_regex'), samples.tags)) \
            .where(Regexp(cat.get('file_regex'), samples.filename)) \

        if sample_type:
            query = query.where(samples.sample_type == sample_type)

        return execute(query)

def generate_links(samples: list, *dirs):
    print(f'Generating symlinks for {os.path.join(*dirs)}')

    for row in samples:
        sample_path = row[1]
        filename = row[10]
        link_path = sort_path.add(*dirs, filename).settle()

        if not os.path.exists(link_path):
            os.symlink(sample_path, link_path)

def unpack_logs(keep: bool):
    print('Extracting Splice logs')

    log_dir     = config.get('log_dir')
    zip_fuzzy   = config.get('zip_fuzzy')
    zip_dir     = config.get('zip_dir')

    if os.path.isdir(log_dir): shutil.rmtree(log_dir)
    os.mkdir(log_dir)

    try:
        target = next(entry.path for entry in os.scandir(zip_dir) if zip_fuzzy in entry.name)
        if not target: raise Exception()
    except:
        print(f'Splice logs not found in {zip_dir}')
        exit()

    shutil.copy(target, log_dir)

    with zipfile.ZipFile(target, 'r') as ref:
        ref.extractall(log_dir)

    if not keep: os.remove(target)

def traverse_hierarchy(db, node, path = None, query = None):
    dirs = node.get('dirs')
    tag_regex = node.get('tag_regex')
    file_regex = node.get('file_regex')
    sample_type = node.get('sample_type')
    custom_where = node.get('where')
    name = node.get('name')

    if not query:
        query = Query().from_(Samples).select('*').where(Samples.local_path.notnull())

    if custom_where:
        query = query.where(CustomFunction(custom_where)())
    if tag_regex:
        query = query.where(Regexp(tag_regex, Samples.tags))
    if file_regex:
        query = query.where(Regexp(file_regex, Samples.filename))
    if sample_type:
        query = query.where(Samples.sample_type == sample_type)

    if not path:
        path = sort_path.add(name)

    os.mkdir(path.settle())

    if dirs:
        for subnode in dirs: traverse_hierarchy(db, subnode, path, query)
    else:
        samples = db.execute(query).fetchall()
        for row in samples:
            sample_path = row[1]
            filename = row[10]
            link_path = path.add(filename).settle()

            if not os.path.exists(link_path):
                os.symlink(sample_path, link_path)

@click.command()
@click.option('--keep/--no-keep', default=False)
@click.option('--reset/--no-reset', default=True)
def main(keep: bool, reset: bool):
    unpack_logs(keep)
    db = init_db()

    if reset: reset_filetree()

    sorted_samps = {}

    # process samples
    for name, cat in hierarchy.get('dirs').items():
        if cat.get('split') and len(cat.get('split')):
            for sample_type in cat.get('split'):
                sorted_samps[name] = {}
                sorted_samps[name][sample_type] = get_samples(db, cat, sample_type)
                generate_links(sorted_samps[name][sample_type], name, sample_type)
        else:
            sorted_samps[name] = get_samples(db, cat)
            generate_links(sorted_samps[name], name)
        
    # catchall
    catchall_samps = get_samples(db, hierarchy.get('catchall'))

    def remove_existing(samples):
        duplicates = filter(lambda sample: sample in catchall_samps, samples)
        for sample in duplicates: catchall_samps.remove(sample)

    for name, value in sorted_samps.items():
        if type(value) == list:
            remove_existing(value)
        else:
            remove_existing(value.values())
                
    generate_links(catchall_samps, hierarchy['catchall']['name'])
    subprocess.call(f'open {sorted_dir}', shell=True)

    print('Done')
    
if __name__ == '__main__':
    main()

