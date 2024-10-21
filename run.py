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

log_dir     = config.get('log_dir')
sorted_dir  = config.get('sorted_dir')
splice_dir  = config.get('splice_dir')
zip_fuzzy   = config.get('zip_fuzzy')
zip_dir     = config.get('zip_dir')
username    = config.get('username')

sort_path = PathBuilder(sorted_dir)

def init_db():
    print('Initializing DB')

    sounds_db = sqlite3.connect(f'./logs/users/default/{username}/sounds.db')

    def regexp(expr, item):
        try:
            reg = re.compile(expr)
            return reg.search(item) is not None
        except Exception as e:
            print(e)

    sounds_db.create_function("REGEXP", 2, regexp)

    return sounds_db

def reset_filetree():
    print('Resetting filetree')

    if os.path.isdir(sorted_dir): shutil.rmtree(sorted_dir)
    os.mkdir(sorted_dir)
    
    for dirname, entry in hierarchy.get('dirs').items():
        dir_path = sort_path.add(dirname)
        os.mkdir(dir_path.settle())
        split = entry.get('split')

        if split:
            for sample_type in split: os.mkdir(dir_path.add(sample_type).settle())

    os.mkdir(sort_path.add(hierarchy.get('catchall').get('dirname')).settle())

def get_samples(db: sqlite3.Connection, cat: dict, sample_type = None):
    execute = lambda query: db.execute(query).fetchall()

    if 'query' in cat:
        return execute(cat.get('query'))
    else:
        query = """
        select * from samples 
        where tags regexp '{tag_regex}'
        and filename regexp '{file_regex}'
        {type_filter}
        and local_path not null;""".format(
            tag_regex = cat.get('tag_regex'),
            file_regex = cat.get('file_regex'),
            type_filter = f'and sample_type = \'{sample_type}\'' if sample_type else ''
        )

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
                
    generate_links(catchall_samps, hierarchy['catchall']['dirname'])
    subprocess.call(f'open {sorted_dir}', shell=True)

    print('Done')
    
if __name__ == '__main__':
    main()

