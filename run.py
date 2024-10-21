import subprocess
import zipfile
import sqlite3
import shutil
import json
import re
import os

with open ('./config/config.json', 'r') as f:
    config = json.loads(f.read())
with open ('./config/hierarchy.json', 'r') as f:
    hierarchy = json.loads(f.read())

log_dir = config['log_dir']
sorted_dir = config['sorted_dir']
splice_dir = config['splice_dir']
zip_fuzzy = config['zip_fuzzy']
zip_dir = config['zip_dir']
username = config['username']

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
    
    for dirname in hierarchy['sample_dirs'].keys():
        os.mkdir(os.path.join(sorted_dir, dirname))

    os.mkdir(os.path.join(sorted_dir, hierarchy['catchall']['dirname']))

def get_samples(db: sqlite3.Connection, cat: dict, custom_query=None):
    if 'query' in cat:
        query = cat['query']
    else:
        query = """
        select * from samples 
        where tags regexp '{tag_regex}'
        and filename regexp '{file_regex}'
        {loop_filter}
        and local_path not null;""".format (
            tag_regex = cat['tag_regex'],
            file_regex = cat['file_regex'],
            loop_filter = "and sample_type = 'oneshot'" if not cat['include_loops'] else ""
        ) if not custom_query else custom_query
    
    return db.execute(query).fetchall()

def generate_links(dirname: str, samples: list):
    print(f'Generating symlinks for {dirname}')

    for row in samples:
        sample_path = row[1]
        filename = row[10]
        link_path = '{}/{}/{}'.format(sorted_dir, dirname, filename)
        
        if not os.path.exists(link_path):
            os.symlink(sample_path, link_path)

def unpack_logs():
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

    os.remove(target)

def main():
    unpack_logs()
    db = init_db()
    reset_filetree()

    sorted_samps = {}

    # process samples
    for i in hierarchy['sample_dirs'].keys():
        sorted_samps[i] = get_samples(db, hierarchy['sample_dirs'][i])
        generate_links(i, sorted_samps[i])
        
    # catchall (percussion)
    catchall_samps = get_samples(db, hierarchy['catchall'])

    for i in sorted_samps.keys():
        for samp in sorted_samps[i]:
            if samp in catchall_samps:
                catchall_samps.remove(samp)
                
    generate_links(hierarchy['catchall']['dirname'], catchall_samps)
    subprocess.call(f'open {sorted_dir}', shell=True)

    print('Done')
    
if __name__ == '__main__':
    main()

