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
from models.base import *
from models.extra import *

from starlight import JST, private_data_path
import csvloader

def sync_event_lookup_table(tsql):
    with tsql as s:
        s.query(EventLookupEntry).delete()
        s.commit()

        rows = s.query(HistoryEventEntry).all()

        for h_ent in rows:
            print(h_ent)
            if h_ent.type() != HISTORY_TYPE_EVENT:
                continue
            seen = set()

            l = h_ent.category_card_list("progression")
            for cid in l:
                s.merge(EventLookupEntry(card_id=cid, event_id=h_ent.referred_id(), acquisition_type=1))
            seen.update(l)

            l = h_ent.category_card_list("ranking")
            for cid in l:
                s.merge(EventLookupEntry(card_id=cid, event_id=h_ent.referred_id(), acquisition_type=2))
            seen.update(l)

            l = h_ent.category_card_list("gacha")
            for cid in l:
                s.merge(EventLookupEntry(card_id=cid, event_id=h_ent.referred_id(), acquisition_type=3))
            seen.update(l)

            print(seen)

            for any_card in h_ent.card_list():
                if any_card not in seen:
                    s.merge(EventLookupEntry(card_id=any_card, event_id=h_ent.referred_id(), acquisition_type=0))
        s.commit()

def sync_gacha_lookup_table(tsql):
    with tsql as s:
        s.query(GachaLookupEntry).delete()
        s.commit()

        first = {}
        last = {}

        rows = s.query(HistoryEventEntry).order_by(HistoryEventEntry.start_time).all()
        for h_ent in rows:
            print(h_ent)
            if h_ent.type() != HISTORY_TYPE_GACHA:
                continue
            seen = set()

            l = h_ent.category_card_list("limited")
            for cid in l:
                tstart, gstart = first.get(cid, (h_ent.start_time, h_ent.referred_id()))
                first[cid] = tstart, gstart
                s.merge(GachaLookupEntry(card_id=cid, first_gacha_id=gstart, last_gacha_id=h_ent.referred_id(),
                    first_available=tstart, last_available=h_ent.end_time, is_limited=1))
            seen.update(l)

            l = h_ent.category_card_list("other")
            for cid in l:
                tstart, gstart = first.get(cid, (h_ent.start_time, h_ent.referred_id()))
                first[cid] = tstart, gstart
                s.merge(GachaLookupEntry(card_id=cid, first_gacha_id=gstart, last_gacha_id=h_ent.referred_id(),
                    first_available=tstart, last_available=h_ent.end_time, is_limited=0))
            seen.update(l)
            print(seen)
        s.commit()

def main():
    if not os.path.exists("./app.py"):
        print("You can only run this program with the cwd set to the main code directory.")

    m = models.TranslationSQL()
    sync_event_lookup_table(m)
    sync_gacha_lookup_table(m)

if __name__ == '__main__':
    main()
