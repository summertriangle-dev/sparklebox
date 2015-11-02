import functools
import os
import csvloader
import json

ark_data_path = functools.partial(os.path.join, "_data", "ark")
private_data_path = functools.partial(os.path.join, "_data", "private")
story_data_path = functools.partial(os.path.join, "_data", "stories")

# primitives
def jsonl(path):
    with open(path, "r") as hsf:
        # tuple for immutability
        return tuple(json.loads(line.strip()) for line in hsf)


def cached_jsonl(path, cache={}):
    if path not in cache:
        cache[path] = jsonl(path)
    return cache[path]


def cached_keyed_db(path, cache={}, **kwargs):
    if path not in cache:
        cache[path] = csvloader.load_keyed_db_file(path, **kwargs)
    return cache[path]


def cached_db(path, cache={}, **kwargs):
    if path not in cache:
        cache[path] = tuple(csvloader.load_db_file(path, **kwargs))
    return cache[path]
