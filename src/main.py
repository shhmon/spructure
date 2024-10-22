import zipfile
import subprocess
import sqlite3
import shutil
import click
import yaml
import re
import os

from utils import Path, SampleWrapper
from predicates import add_predicates

with open ('./config/config.yaml', 'r') as f:
    config = yaml.safe_load(f.read())
with open ('./config/hierarchy.yaml', 'r') as f:
    hierarchy = yaml.safe_load(f.read())

output_path = Path(config.get('sorted_dir'))

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

def unpack_logs(keep: bool):
    print('Extracting Splice logs')

    log_path = Path(config.get('log_dir'))
    zip_path = Path(config.get('zip_dir'))

    zip_fuzzy = config.get('zip_fuzzy')
    target = zip_path.fuzzy_find(zip_fuzzy)

    if not target:
        print(f'Splice logs not found in {zip_path}')
        exit()

    log_path.clear_directory()
    shutil.copy(target, str(log_path))

    with zipfile.ZipFile(target, 'r') as ref:
        ref.extractall(str(log_path))

    if not keep: os.remove(str(target))

def traverse_hierarchy(db, node, path=output_path, query=None):
    dirs = node.get('dirs')
    name = node.get('name')
    output = node.get('output')
    catchall = node.get('catchall')

    def execute(query):
        return [*map(lambda s: SampleWrapper(s, path), db.execute(str(query)).fetchall())]

    def dedupe(target, check_list):
        hashes = [*map(lambda s: s.hash, check_list)]
        return [s for s in target if s.hash not in hashes]

    if name:
        path = path.append(name).make_directory()

    query = add_predicates(node, query)
    samples = []

    if dirs:
        for subnode in dirs:
            s = traverse_hierarchy(db, subnode, path, query)
            samples = samples + dedupe(s, samples)
        if output:
            s = execute(query)
            samples = samples + dedupe(s, samples)
    else:
        samples = execute(query)

    if catchall:
        s = traverse_hierarchy(db, catchall)
        samples = samples + dedupe(s, samples)

    return samples

@click.command()
@click.option('--keep/--no-keep', default=False)
@click.option('--reset/--no-reset', default=True)
def main(keep: bool, reset: bool):
    unpack_logs(keep)
    db = init_db()

    if reset: output_path.clear_directory()
    samples = traverse_hierarchy(db, hierarchy)
    for sample in samples: sample.generate_symlink()
    subprocess.call(f'open {output_path}', shell=True)

    print(f'Done ({len(samples)})')
    
if __name__ == '__main__':
    main()
