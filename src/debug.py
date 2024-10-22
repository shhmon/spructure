import random

import click
import itertools

from main import init_db, unpack_logs

@click.command()
@click.option('--mode', default='tags')
def debug(mode: str):
    unpack_logs(True)
    db = init_db()

    if mode == 'tags':
        tags = db.execute('SELECT "tags" FROM samples WHERE "local_path" NOT NULL').fetchall()
        flat = set(','.join(list(itertools.chain(*tags))).split(','))
        for tag in sorted(flat): print(tag)
        exit()

    samples = db.execute('SELECT * FROM samples WHERE "local_path" NOT NULL').fetchall()
    random_index = random.randint(0, len(samples)-1)
    for i, col in enumerate(db.execute("PRAGMA table_info(samples)").fetchall()):
        print(col)
        print(samples[random_index][i])


    while True:
        query = input("Query:")
        print(query)
        samples = db.execute(str(query)).fetchall()
        print(samples)
    
if __name__ == '__main__':
    debug()
