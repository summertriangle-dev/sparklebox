#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__) + "/.."))

import json
import sqlite3

from datetime import datetime
import locale
locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

from pytz import timezone, utc
from collections import namedtuple
import models

from starlight import JST

gacha_stub_t = namedtuple("gacha_stub_t", ("id", "name", "start_date", "end_date", "type", "subtype"))

def gacha_ids(f):
    gachas = []

    a = sqlite3.connect(f)
    for id, n, ss, es, t, t2 in a.execute("SELECT id, name, start_date, end_date, type, type_detail FROM gacha_data where type = 3 and type_detail = 1"):
        ss, es = JST(ss), JST(es)
        gachas.append(gacha_stub_t(id, n, ss, es, t, t2))

    return sorted(gachas, key=lambda x: x.start_date)

def available(f, g):
    a = sqlite3.connect(f)
    for x in a.execute(
        "SELECT gacha_id, step_num, reward_id, recommend_order, limited_flag FROM gacha_available WHERE gacha_id IN ({0})"
            .format(",".join("?" * len(g))), tuple(g)):
        yield x
    a.close()

def main(file1, file2):
    gacha_ids_a = gacha_ids(file1)
    gacha_ids_b = gacha_ids(file2)

    ksa, ksb = map(lambda x: set([y.id for y in x]), (gacha_ids_a, gacha_ids_b))
    added = ksb - ksa

    m = models.TranslationSQL()
    m.add_reward_tracking_entries(available(file2, added))

    prev = gacha_ids_b[0]
    for gacha in gacha_ids_b[1:]:
        if gacha.id not in added:
            prev = gacha
            continue

        delta = gacha.start_date - prev.end_date
        if (delta.days * 86400) + delta.seconds < 10:
            m.extend_gacha(prev, gacha)
        else:
            m.seed_initial(gacha)
        prev = gacha

if __name__ == '__main__':
    main(*sys.argv[1:])
