import zipfile
import subprocess
import sqlite3
import random
import shutil
import click
import yaml
import re
import os

from utils import Path, SampleWrapper, addPredicates

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

def traverse_hierarchy(db, node, symlink = True, path = output_path, query = None):
    dirs = node.get('dirs')
    name = node.get('name')
    output = node.get('output')
    catchall = node.get('catchall')

    samples = []
    query = addPredicates(node, query)

    def execute(query):
        return [*map(SampleWrapper, db.execute(str(query)).fetchall())]

    def remove_duplicates(target, checkList):
        get_hash = lambda s: s.get_hash() 
        hashes = [*map(get_hash, checkList)]
        return [s for s in target if get_hash(s) not in hashes]

    if name:
        path = path.append(name).make_directory()

    if dirs:
        for subnode in dirs:
            samples = samples + traverse_hierarchy(db, subnode, symlink, path, query)
        if output:
            current_samples = execute(query)
            current_samples = remove_duplicates(current_samples, samples)
            samples = samples + current_samples
            if symlink: generate_symlinks(current_samples, path)
    else:
        samples = execute(query)
        if symlink: generate_symlinks(samples, path)

    if catchall:
        catchall_path = path.append(catchall.get('name'))
        catchall_samples = traverse_hierarchy(db, catchall, False)
        catchall_samples = remove_duplicates(catchall_samples, samples)
        generate_symlinks(catchall_samples, catchall_path)

    return samples

def generate_symlinks(samples: list, path: Path):
    print(f'Generating symlinks for {path} ({len(samples)})')

    for sample in samples:
        link_path = str(path.append(sample.get_filename()))

        if not os.path.exists(link_path):
            os.symlink(sample.get_path(), link_path)

@click.command()
@click.option('--keep/--no-keep', default=False)
@click.option('--reset/--no-reset', default=True)
@click.option('--debug/--no-debug', default=False)
def main(keep: bool, reset: bool, debug: bool):
    unpack_logs(keep)
    db = init_db()

    if debug:
        samples = db.execute("SELECT * FROM samples").fetchall()
        random_index = random.randint(0, len(samples)-1)
        for i, col in enumerate(db.execute("PRAGMA table_info(samples)").fetchall()):
            print(col)
            print(samples[random_index][i])
    else:
        if reset: output_path.clear_directory()
        traverse_hierarchy(db, hierarchy)
        subprocess.call(f'open {output_path}', shell=True)

    print('Done')
    
if __name__ == '__main__':
    main()
