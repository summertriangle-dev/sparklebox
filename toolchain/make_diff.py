import csvloader
import sys
import os
import json
from datetime import date

def values_changed(a, b):
    for field in a.__class__._fields:
        if getattr(a, field) != getattr(b, field):
            yield "{0}: {1} -> {2}".format(field, getattr(a, field), getattr(b, field))

def main(file1, file2, title_key):
    loc = os.path.basename(file2)
    if "." in loc:
        loc = loc[:loc.rfind(".")]

    data_a = csvloader.load_keyed_db_file(file1)
    data_b = csvloader.load_keyed_db_file(file2)
    
    #assert schema_b == schema_a, "Schema mismatch."
    
    ksa, ksb = map(lambda x: set(x.keys()), (data_a, data_b))
    added = ksb - ksa
    removed = ksa - ksb
    changed = set()
        
    maybe_changed = ksb & ksa
    for key in maybe_changed:
        if data_a[key] != data_b[key]:
            changed.add(key)
    
    diff = []
    
    for key in removed:
        diff.append({
            "_k": key,
            "change_type": "Removed",
            "where": "{0}:{1}".format(loc, key),
            "title": getattr(data_a[key], title_key)
        })
    for key in added:
        diff.append({
            "_k": key,
            "change_type": "Added",
            "where": "{0}:{1}".format(loc, key),
            "title": getattr(data_b[key], title_key)
        })
    for key in changed:
        diff.append({
            "_k": key,
            "change_type": "Changed",
            "where": "{0}:{1}".format(loc, key),
            "title": getattr(data_b[key], title_key),
            "extra": "\n".join(values_changed(data_a[key], data_b[key]))
        })
    
    diff.sort(key=lambda x: x["_k"])
    for x in diff:
        print(json.dumps(x, sort_keys=1))

def main(file1, file2):
    data_a = csvloader.load_keyed_db_file(file1)
    data_b = csvloader.load_keyed_db_file(file2)
    ksa, ksb = map(lambda x: set(x.keys()), (data_a, data_b))
    added = ksb - ksa
    
    if added:
        diff_obj = {"date": str(date.today()), "cids": sorted(added)}
        print(json.dumps(diff_obj))

if __name__ == '__main__':
    main(*sys.argv[1:])
