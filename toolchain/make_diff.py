#!/usr/bin/env python3
import sys
import os
import json
import sqlite3

import locale
locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

def load_sql(f):
    a = sqlite3.connect(f)
    c = a.execute("SELECT id, rarity, event_available.reward_id FROM card_data LEFT JOIN event_available ON (id == event_available.reward_id)")

    lut = ["n", "n", "r", "r", "sr", "sr", "ssr", "ssr"]
    ret = {r[0]: "event" if r[2] else lut[r[1] - 1] for r in c}
    a.close()
    return ret

def main(file1, file2):
    data_a = load_sql(file1)
    data_b = load_sql(file2)

    ksa, ksb = map(lambda x: set(x.keys()), (data_a, data_b))
    added = ksb - ksa

    if added:
        diff_obj = {"n": [], "r": [], "sr": [], "ssr": [], "event": []}
        for key in added:
            diff_obj[data_b[key]].append(key)
        print(json.dumps(diff_obj))

if __name__ == '__main__':
    main(*sys.argv[1:])
