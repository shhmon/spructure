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

def traverse(db, node, path, query=None):
    name = node.get('name')
    dirs = node.get('dirs', [])
    output = node.get('output', not dirs)
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

    for subnode in dirs:
        new_samples = traverse(db, subnode, path, query)
        samples = samples + dedupe(new_samples, samples)

    if output:
        new_samples = execute(query)
        samples = samples + dedupe(new_samples, samples)

    if catchall:
        catch_samples = traverse(db, catchall, path)
        samples = samples + dedupe(catch_samples, samples)

    return samples

@click.command()
@click.option('--keep/--no-keep', default=False)
@click.option('--reset/--no-reset', default=True)
def main(keep: bool, reset: bool):
    output_path = Path(config.get('sorted_dir'))
    if reset: output_path.clear_directory()

    unpack_logs(keep)
    db = init_db()

    samples = traverse(db, hierarchy, output_path)
    for sample in samples: sample.generate_symlink()
    subprocess.call(f'open {output_path}', shell=True)

    print(f'Done ({len(samples)})')
    
if __name__ == '__main__':
    main()
