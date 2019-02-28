#!/usr/bin/env python3
import sys
import os
import json
import sqlite3
import csvloader
import starlight
import models
from collections import namedtuple, defaultdict

import locale
locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

QUERY_GET_EVENT_STUBS       = "SELECT id, name, type, event_start, event_end FROM event_data"
QUERY_GET_REWARDS_FOR_EVENT = "SELECT reward_id FROM event_available WHERE event_id = ? ORDER BY recommend_order"
QUERY_GET_NORMAL_GACHAS =   """SELECT gacha_data.id, gacha_data.name, start_date, end_date, type, type_detail,
    gacha_rate.rare_ratio, gacha_rate.sr_ratio, gacha_rate.ssr_ratio
    FROM gacha_data LEFT JOIN gacha_rate USING (id) WHERE type = 3 AND type_detail = 1"""
QUERY_GET_GACHA_REWARD_META = """SELECT reward_id, limited_flag, recommend_order
    FROM gacha_available WHERE gacha_id = ? AND recommend_order != 0
    ORDER BY recommend_order"""
QUERY_GET_GACHA_REWARD_META_V2 = """SELECT card_id, limited_flag, recommend_order
    FROM gacha_available_2 WHERE gacha_id = ? ORDER BY recommend_order"""
QUERY_GET_ROOTS = "SELECT id FROM card_data WHERE evolution_id != 0"
QUERY_GET_STORY_START_DATES = """SELECT card_data.id, start_date FROM card_data
    LEFT JOIN story_detail ON (open_story_id == story_detail.id)
    WHERE card_data.id IN ({0})"""
QUERY_FIND_CONTAINING_GACHA = "SELECT DISTINCT gacha_id FROM gacha_available WHERE reward_id = ? AND gacha_id IN ({0})"
QUERY_FIND_CONTAINING_GACHA_V2 = "SELECT DISTINCT gacha_id FROM gacha_available_2 WHERE card_id = ? AND gacha_id IN ({0})"

ea_overrides = list(csvloader.load_db_file(starlight.private_data_path("event_availability_overrides.csv")))
overridden_events = set(x.event_id for x in ea_overrides)

def htype(x):
    return (x & 0xF0000000) >> 28

def internal_id(x):
    return x & 0x0FFFFFFF

def get_overridden(event_id):
    for k, v in ea_overrides:
        if k == event_id:
            yield v

def prime_from_cursor(typename, cursor, **kwargs):
    keys = list(kwargs.keys())

    fields = [x[0] for x in cursor.description]
    raw_field_len = len(fields)
    the_raw_type = namedtuple("_" + typename, fields)

    for key in keys:
        fields.append(key)

    the_type = namedtuple(typename, fields)

    for val_list in cursor:
        temp_obj = the_raw_type(*map(csvloader.clean_value, val_list))
        try:
            extvalues = tuple(kwargs[key](temp_obj) for key in keys)
        except Exception:
            raise RuntimeError(
                "Uncaught exception while filling stage2 data for {0}. Are you missing data?".format(temp_obj))
        yield the_type(*temp_obj + extvalues)

def log_events(have_logged, seen, local, remote):
    # map: event id -> event_stub_t
    events = {k[0]: k
        for k in prime_from_cursor("event_stub_t",
            local.execute(QUERY_GET_EVENT_STUBS))
    }

    # generate a set of all event ids with the type bitfield set correctly
    event_h_ids = set(map(lambda x: (models.HISTORY_TYPE_EVENT << 28) | (x & 0x0FFFFFFF), events))
    # xor the top 4 bits (i.e., the history type id) of each descriptor by 7,
    # which just turns the 2 (HISTORY_TYPE_EVENT) to a 5 (HISTORY_TYPE_EVENT_END).
    event_end_h_ids = set(map(lambda x: x ^ 0x70000000, event_h_ids))

    need_to_add = (event_h_ids | event_end_h_ids) - have_logged

    def ge_cards(event_id):
        if event_id in overridden_events:
            rl = list(get_overridden(event_id))
        else:
            rl = [k for k, in local.execute(QUERY_GET_REWARDS_FOR_EVENT, (event_id,)).fetchall()]

        seen.update(rl)
        return json.dumps({ "event": rl })

    def eti(event_id):
        base = (events[event_id].type - 1) & 0x7
        # TODO figure out where to get token attribute/medley focus...
        return base

    with remote as s:
        # add event markers
        for desc in event_h_ids - have_logged:
            if starlight.JST(events[internal_id(desc)].event_start).year >= 2099:
                continue

            s.add(models.HistoryEventEntry(
                descriptor=desc,
                extra_type_info=eti(internal_id(desc)),
                added_cards=ge_cards(internal_id(desc)),
                event_name=events[internal_id(desc)].name,

                start_time=starlight.JST(events[internal_id(desc)].event_start).timestamp(),
                end_time=starlight.JST(events[internal_id(desc)].event_end).timestamp()
            ))

        # add event end markers
        # for desc in event_end_h_ids - have_logged:
        #     s.add(models.HistoryEventEntry(
        #         descriptor=desc,
        #         extra_type_info=0,
        #         added_cards=None,
        #         event_name=events[internal_id(desc)].name,
        #
        #         start_time=starlight.JST(events[internal_id(desc)].event_end).timestamp(),
        #         end_time=0
        #     ))
        s.commit()

def log_gachas(have_logged, seen, seen_in_gacha, local, remote):
    # code sucks
    # TODO clean up and refactor everything after this line
    have_gacha_set = set( map( lambda x: internal_id(x),
                               filter(lambda x: htype(x) == 3, have_logged) ) )

    # map: gacha id -> gacha_stub_t
    gachas = {k[0]: k for k in prime_from_cursor("gacha_stub_t", local.execute(QUERY_GET_NORMAL_GACHAS))}

    # { gacha id -> { "limited": [], "other": [] ... } }
    add_sets = {k: defaultdict(lambda: []) for k in gachas}

    new_gachas = set(gachas.keys()) - have_gacha_set
    gachas_in_chrono_order = sorted(new_gachas, key=lambda x: starlight.JST(gachas[x].start_date))

    orphans = set(k for k, in local.execute(QUERY_GET_ROOTS).fetchall()) - seen_in_gacha

    is_limited = {}
    # check limited/featured
    for gid in new_gachas:
        keys = {}
        my_add_set = add_sets[gid]

        query_v2 = local.execute(QUERY_GET_GACHA_REWARD_META_V2, (gid,)).fetchall()
        if not query_v2:
            query_v2 = local.execute(QUERY_GET_GACHA_REWARD_META, (gid,)).fetchall()

        for a_card, lim_flag, order in query_v2:
            my_add_set["limited" if lim_flag else "other"].append(a_card)

            seen.add(a_card)
            seen_in_gacha.add(a_card)
            try:
                orphans.remove(a_card)
            except KeyError:
                pass

            keys[a_card] = order

            if lim_flag:
                # mark the gacha as limited
                is_limited[gid] = 1

        # now sort the add set
        if "limited" in my_add_set:
            my_add_set["limited"].sort(key=keys.get)

        if "other" in my_add_set:
            my_add_set["other"].sort(key=keys.get)

    gspec = ",".join(map(str, new_gachas))
    for orphan in orphans:
        havers = [k for k, in local.execute(QUERY_FIND_CONTAINING_GACHA_V2.format(gspec), (orphan,))]
        if not havers:
            havers = [k for k, in local.execute(QUERY_FIND_CONTAINING_GACHA.format(gspec), (orphan,))]
        for gid in gachas_in_chrono_order:
            if gid in havers:
                break
        else:
            # print("orphan:", orphan)
            continue

        seen.add(orphan)
        seen_in_gacha.add(orphan)
        add_sets[gid]["other"].append(orphan)

    with remote as s:
        for gid in new_gachas:
            s.add(models.HistoryEventEntry(
                descriptor=gid | (models.HISTORY_TYPE_GACHA << 28),
                extra_type_info=is_limited.get(gid, 0),
                added_cards=json.dumps(add_sets[gid]) if add_sets[gid] else None,
                event_name=gachas[gid].name,

                start_time=starlight.JST(gachas[gid].start_date).timestamp(),
                end_time=starlight.JST(gachas[gid].end_date).timestamp()
            ))
        s.commit()

def log_lastresort(have_logged, seen, local, remote):
    orphans = set(k for k, in local.execute(QUERY_GET_ROOTS).fetchall()) - seen

    buckets = defaultdict(lambda: [])

    spec = ",".join(map(str, orphans))
    for card, datestr in local.execute(QUERY_GET_STORY_START_DATES.format(spec)):
        if not datestr:
            continue

        buckets[starlight.JST(datestr).timestamp()].append(card)
        seen.add(card)

    with remote as s:
        for time in buckets:
            # hours since the epoch, hopefully will last us long enough lul
            primary_key = int(time / (60 * 60))

            s.add(models.HistoryEventEntry(
                descriptor=primary_key | (models.HISTORY_TYPE_ADD_N << 28),
                extra_type_info=0,
                added_cards=json.dumps({ "new": buckets[time] }),
                event_name=None,

                start_time=time,
                end_time=0,
            ))
        s.commit()

def main(new_db):
    local = sqlite3.connect(new_db)
    remote = models.TranslationSQL()

    seen = set()
    seen_in_gacha = set()
    have_logged = set()

    with remote as s:
        raw = s.query(models.HistoryEventEntry.descriptor, models.HistoryEventEntry.added_cards).all()
        for descriptor, payload in raw:
            have_logged.add(descriptor)

            if not payload:
                continue

            for each_list in json.loads(payload).values():
                seen.update(each_list)

            if htype(descriptor) == models.HISTORY_TYPE_GACHA:
                for each_list in json.loads(payload).values():
                    seen_in_gacha.update(each_list)

    log_events(have_logged, seen, local, remote)
    log_gachas(have_logged, seen, seen_in_gacha, local, remote)
    log_lastresort(have_logged, seen, local, remote)

    print("final orphaned set:", set(k for k, in local.execute(QUERY_GET_ROOTS).fetchall()) - seen)
    print("if the above set isn't empty, file a bug because i missed something")

if __name__ == '__main__':
    main(*sys.argv[1:])
