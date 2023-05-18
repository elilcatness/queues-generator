import os
from uuid import uuid1


def manage_empty_q(q: str):
    if q and not os.path.exists(q):
        os.mkdir(q)
    elif not q:
        q = str(uuid1)
        os.mkdir(q)
    return q


def read_file(filename: str):
    with open(filename, encoding='utf-8') as f:
        return [line.strip().replace('\n', '') for line in f]
    

def write_to_file(filename: str, data: list):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(data))