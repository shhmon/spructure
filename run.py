import zipfile
import subprocess
import sqlite3
import shutil
import click
import json
import re
import os

from utils import Path, addPredicates

with open ('./config/config.json', 'r') as f:
    config = json.loads(f.read())
with open ('./config/hierarchy.json', 'r') as f:
    hierarchy = json.loads(f.read())

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

def traverse_hierarchy(db, node, symlink = True, path = output_path, query = None, chain = None):
    dirs = node.get('dirs')
    name = node.get('name')
    catchall = node.get('catchall')

    print(f"Traversing {name}")

    query = addPredicates(node, query)
    samples = []

    if name:
        path = path.append(name).make_directory()

    if dirs:
        for subnode in dirs:
            samples = samples + traverse_hierarchy(db, subnode, symlink, path, query, chain)
    else:
        samples = db.execute(str(query)).fetchall()
        if symlink: generate_symlinks(samples, path)

    if catchall:
        catchall_path = path.append(catchall.get('name'))
        catchall_samples = traverse_hierarchy(db, catchall, False)
        duplicates = filter(lambda sample: sample in samples, catchall_samples)
        for sample in duplicates: catchall_samples.remove(sample)
        generate_symlinks(catchall_samples, path.append(catchall_path))

    return samples

def generate_symlinks(samples: list, path: Path):
    print(f'Generating symlinks for {path}')

    for row in samples:
        sample_path = row[1]
        filename = row[10]
        link_path = str(path.append(filename))

        if not os.path.exists(link_path):
            os.symlink(sample_path, link_path)

@click.command()
@click.option('--keep/--no-keep', default=False)
@click.option('--reset/--no-reset', default=True)
def main(keep: bool, reset: bool):
    unpack_logs(keep)
    db = init_db()
    if reset: output_path.clear_directory()
    traverse_hierarchy(db, hierarchy)
    subprocess.call(f'open {output_path}', shell=True)
    print('Done')
    
if __name__ == '__main__':
    main()
