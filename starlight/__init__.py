import re
import sqlite3
import pickle
import os
import subprocess
import sys
from time import time
from datetime import datetime, timedelta
from pytz import timezone, utc
from functools import lru_cache, partial
from collections import defaultdict, namedtuple, Counter
from tornado import ioloop

from csvloader import clean_value, load_keyed_db_file, load_db_file
from . import en
from . import apiclient
from . import acquisition
from . import extra_va_tables

ark_data_path = partial(os.path.join, "_data", "ark")
private_data_path = partial(os.path.join, "_data", "private")
story_data_path = partial(os.path.join, "_data", "stories")
transient_data_path = partial(os.path.join, os.getenv(os.getenv("TRANSIENT_DIR_POINTER", ""), "_data/transient"))

acquisition.CACHE = transient_data_path()

_JST = timezone("Asia/Tokyo")
def JST(date, to_utc=1):
    # this is here because some datetime calls were throwing on 29 Feb.
    # TODO in 4 years, check if this is still needed
    try:
        time = _JST.localize(datetime.strptime(date.replace("-02-29 ", "-03-01 "), "%Y-%m-%d %H:%M:%S"))
    except ValueError:
        # and this is here because the date format changed starting 10021500
        time = _JST.localize(datetime.strptime(date.replace("/02/29 ", "/03/01 "), "%Y/%m/%d %H:%M:%S"))

    if to_utc:
        return time.astimezone(utc)
    else:
        return time

def TODAY():
    return utc.localize(datetime.utcnow())

def _real_scale_skill_value(max_, min_, lv):
    return (min_ + ((max_ - min_) / 9) * lv) / 100.0

def _scale_skill_value(max_, min_, lv):
    val = _real_scale_skill_value(max_, min_, lv)
    # if the decimal part is too small, just remove it
    if val - int(val) < 0.01:
        return int(val)
    else:
        return val

def skill_chance(prob_def, ptype):
    maxv, minv = prob_def[ptype].probability_max, prob_def[ptype].probability_min
    return "{0}..{1}".format(_scale_skill_value(maxv, minv, 0),
                             _scale_skill_value(maxv, minv, 9))

def skill_dur(dur_def, ttype):
    maxv, minv = dur_def[ttype].available_time_max, dur_def[ttype].available_time_min
    return "{0}..{1}".format(_scale_skill_value(maxv, minv, 0),
                             _scale_skill_value(maxv, minv, 9))

def determine_best_stat(vo, vi, da):
    """Card stats are either balanced (VoViDa are around the same),
       or one stat will be noticeably higher.
       This function returns which one."""
    VISUAL, DANCE, VOCAL, BALANCED = 1, 2, 3, 4
    # for balanced cards, the ratio hi:lo will be close to 1
    THRES = 1.2
    stats = ((vo, VOCAL), (vi, VISUAL), (da, DANCE))
    lo, lo_typ = min(stats)
    hi, hi_typ = max(stats)
    if hi / lo > THRES:
        return hi_typ
    else:
        return BALANCED + hi_typ

Availability = namedtuple("Availability", ("type", "name", "start", "end"))
Availability._TYPE_GACHA = 1
Availability._TYPE_EVENT = 2

gacha_rates_t = namedtuple("gacha_rates_t", ("r", "sr", "ssr"))
# to be safe: define as exprs of int so the resulting floats will compare properly.
# otherwise there may be a subtle difference between "8850/100" and "88.5"
# and == will break.
gacha_rates_t._REGULAR_RATES = gacha_rates_t(8850 / 100, 1000 / 100, 150 / 100)

gacha_single_reward_t = namedtuple("gacha_single_reward_t",
    ("card_id", "is_limited", "sort_order", "relative_odds", "gsr_relative_odds"))

potential_birthday_t = namedtuple("potential_birthday_t", ("month", "day", "chara"))

TITLE_ONLY_REGEX = r"^［(.+)］"
NAME_ONLY_REGEX = r"^(?:［.+］)?(.+)$"
AWAKENED_SYMBOL = "＋"

class DataCache(object):
    def __init__(self, version):
        self.version = version
        self.load_date = datetime.utcnow()
        self.hnd = sqlite3.connect(transient_data_path("{0}.mdb".format(version)))
        self.class_cache = {}
        self.prime_caches()
        self.reset_statistics()

    def reset_statistics(self):
        self.vc_this = 0
        self.primed_this = Counter()

    @lru_cache(1)
    def gacha_ids(self):
        gachas = []
        gacha_stub_t = namedtuple("gacha_stub_t", ("id", "name", "start_date", "end_date", "type", "subtype", "rates"))
        stub_query = """SELECT gacha_data.id, gacha_data.name, start_date, end_date, type, type_detail,
                        gacha_rate.rare_ratio, gacha_rate.sr_ratio, gacha_rate.ssr_ratio
                        FROM gacha_data LEFT JOIN gacha_rate USING (id) WHERE type = 3 AND type_detail = 1"""
        for id, n, ss, es, t, t2, r, sr, ssr in self.hnd.execute(stub_query):
            ss, es = JST(ss), JST(es)
            gachas.append(gacha_stub_t(id, n, ss, es, t, t2, gacha_rates_t(r / 100, sr / 100, ssr / 100)))

        self.primed_this["sel_gacha"] += 1
        return sorted(gachas, key=lambda x: x.start_date)

    @lru_cache(1)
    def event_ids(self):
        events = []
        event_stub_t = namedtuple("event_stub_t", ("id", "name", "start_date", "end_date"))

        for id, na, ss, es in self.hnd.execute("SELECT id, name, event_start, event_end FROM event_data"):
            ss, es = JST(ss), JST(es)
            events.append(event_stub_t(id, na, ss, es))

        self.primed_this["sel_event"] += 1
        return sorted(events, key=lambda x: x.start_date)

    def gachas(self, when):
        select = []
        for stub in reversed(self.gacha_ids()):
            if stub.start_date <= when < stub.end_date:
                select.append(stub)
        return select

    def available_cards(self, gacha):
        query = "SELECT reward_id, limited_flag, (CASE WHEN recommend_order == 0 THEN 9999 ELSE recommend_order END), relative_odds, relative_sr_odds FROM gacha_available WHERE gacha_id = ?"
        self.primed_this["sel_ac"] += 1
        return [gacha_single_reward_t(*r) for r in self.hnd.execute(query, (gacha.id,)).fetchall()]

    def limited_availability_cards(self, gachas):
        select = [gacha.id for gacha in gachas]
        query = "SELECT gacha_id, reward_id FROM gacha_available WHERE limited_flag == 1 AND gacha_id IN ({0})".format(",".join("?" * len(select)))
        tmp = defaultdict(lambda: [])
        [tmp[gid].append(reward) for gid, reward in self.hnd.execute(query, select)]

        self.primed_this["sel_la"] += 1
        return [tmp[gacha.id] for gacha in gachas]

    def current_limited_availability(self):
        return self.limited_availability(TODAY())

    def event_availability(self, cards):
        events = {x.id: Availability(Availability._TYPE_EVENT, x.name, x.start_date, x.end_date) for x in self.event_ids()}
        query = "SELECT event_id, reward_id FROM event_available WHERE reward_id IN ({0})".format(",".join("?" * len(cards)))
        ea = defaultdict(lambda: [])

        for event, reward in self.hnd.execute(query, cards):
            if event in self.overridden_events:
                continue
            ea[reward].append(events[event])

        for event, reward in self.ea_overrides:
            if reward in cards:
                ea[reward].append(events[event])

        [v.sort(key=lambda x: x.start) for v in ea.values()]
        self.primed_this["sel_evtreward_rev"] += 1
        return ea

    def events(self, when):
        select = []
        for stub in reversed(self.event_ids()):
            if stub.start_date <= when < stub.end_date:
                select.append(stub)

        return select

    # Sometimes this method will return more events than you asked for.
    # Make sure to filter the results on the caller side.
    def event_rewards(self, events):
        select = [event.id for event in events if event.id not in self.overridden_events]
        query = "SELECT event_id, reward_id FROM event_available WHERE event_id IN ({0})".format(",".join("?" * len(select)))
        tmp = defaultdict(lambda: [])
        [tmp[event].append(reward) for event, reward in self.hnd.execute(query, select)]

        for event, reward in self.ea_overrides:
            tmp[event].append(reward)

        self.primed_this["sel_evtreward"] += 1
        return [tmp[event.id] for event in events]

    def current_events(self):
        return self.events(TODAY())

    def load_names(self):
        overrides = load_keyed_db_file(private_data_path("overrides.csv"))
        names = load_keyed_db_file(transient_data_path("names.csv"))

        if not names:
            # then we can't get a schema
            names.update(overrides)
            return names

        schema = next(iter(names.values())).__class__
        names_keys = set(schema._fields)
        overrides_keys = set(schema._fields)
        if not overrides_keys <= names_keys:
            raise Exception('names.csv schema error: all of "chara_id","kanji","kanji_spaced","kana_spaced","conventional" must be present in the header')

        # maps kanji -> chara id
        by_kanji = {v.kanji: k for k, v in names.items()}

        for key in overrides:
            if key < 0:
                # a negative chara id in the override entry means we should match on kanji.
                real_key = by_kanji.get(overrides[key].kanji)
                intermediate = names.get(real_key)
            else:
                real_key = key
                intermediate = names.get(key)

            if intermediate is None:
                continue

            d = intermediate._asdict()
            override_vals = overrides[key]._asdict()
            # chara_id may differ if we indexed on kanji, so remove it
            del override_vals["chara_id"]
            d.update(override_vals)
            names[real_key] = schema(**d)

        return names

    def prime_caches(self):
        self.names = self.load_names()
        self.kanji_to_name = {v.kanji: v.conventional for v in self.names.values()}

        self.ea_overrides = list(load_db_file(private_data_path("event_availability_overrides.csv")))
        self.overridden_events = set(x.event_id for x in self.ea_overrides)

        prob_def = self.keyed_prime_from_table("probability_type")
        time_def = self.keyed_prime_from_table("available_time_type")

        self._skills = self.keyed_prime_from_table("skill_data",
            chance=lambda obj: partial(skill_chance, prob_def, obj.probability_type),
            dur=lambda obj: partial(skill_dur, time_def, obj.available_time_type),
            max_chance=lambda obj: prob_def[obj.probability_type].probability_max,
            max_duration=lambda obj: time_def[obj.available_time_type].available_time_max)
        self._lead_skills = self.keyed_prime_from_table("leader_skill_data")
        self.rarity_dep = self.keyed_prime_from_table("card_rarity")

        self.chain_id = {}
        self.id_chain = defaultdict(lambda: [])
        chain_cur = self.hnd.execute("SELECT id, series_id FROM card_data WHERE album_id > 0")
        for p in self.prime_from_cursor("chain_id_t", chain_cur):
            self.chain_id[p.id] = p.series_id
            self.id_chain[p.series_id].append(p.id)

        self.char_cache = {}
        self.card_cache = {}

    def prime_from_table(self, table, **kwargs):
        rows = self.hnd.execute("SELECT * FROM {0}".format(table))
        class_name = table + "_t"

        return self.prime_from_cursor(class_name, rows, **kwargs)

    def prime_from_cursor(self, typename, cursor, **kwargs):
        the_raw_type, the_type = self.class_cache.get(typename, (None, None))
        keys = list(kwargs.keys())

        if not the_raw_type:
            print("trace prime_from_cursor needs to create a class")
            fields = [x[0] for x in cursor.description]
            raw_field_len = len(fields)
            the_raw_type = namedtuple("_" + typename, fields)

            for key in keys:
                fields.append(key)

            the_type = namedtuple(typename, fields)
            self.class_cache[typename] = (the_raw_type, the_type)

        for val_list in cursor:
            temp_obj = the_raw_type(*map(clean_value, val_list))
            try:
                extvalues = tuple(kwargs[key](temp_obj) for key in keys)
            except Exception:
                raise RuntimeError(
                    "Uncaught exception while filling stage2 data for {0}. Are you missing data?".format(temp_obj))
            yield the_type(*temp_obj + extvalues)

    def keyed_prime_from_table(self, table, **kwargs):
        ret = {}
        for t in self.prime_from_table(table, **kwargs):
            ret[t[0]] = t
        return ret

    def cache_chars(self, idl):
        query = "SELECT * FROM chara_data WHERE chara_id IN ({0})".format(",".join("?" * len(idl)))
        cur = self.hnd.execute(query, idl)

        for p in self.prime_from_cursor("chara_data_t", cur,
            kanji_spaced=lambda obj: self.names.get(obj.chara_id).kanji_spaced,
            kana_spaced=lambda obj:  self.names.get(obj.chara_id).kana_spaced,
            conventional=lambda obj: self.names.get(obj.chara_id).conventional,
            valist=lambda obj: []):
            self.char_cache[p.chara_id] = p
            self.primed_this["prm_char"] += 1
        self.primed_this["prm_char_calls"] += 1

    def cache_cards(self, idl):
        normalized_idl = set()
        for id in idl:
            a = self.chain_id.get(id)
            if a:
                normalized_idl.add(a)

        idl = list(normalized_idl)

        query_preload_chars = "SELECT DISTINCT chara_id FROM card_data WHERE id IN ({0})".format(",".join("?" * len(idl)))
        self.cache_chars(list(map(lambda x: x[0], self.hnd.execute(query_preload_chars, idl))))

        query = "SELECT * FROM card_data WHERE series_id IN ({0})".format(",".join("?" * len(idl)))
        cur = self.hnd.execute(query, idl)

        selected = self.prime_from_cursor("card_data_t", cur,
            chara=lambda obj: self.char_cache.get(obj.chara_id),
            has_spread=lambda obj: obj.rarity > 4,
            has_sign=lambda obj: obj.rarity > 6,
            name_only=lambda obj: re.match(NAME_ONLY_REGEX, obj.name).group(1),
            title=lambda obj: re.match(TITLE_ONLY_REGEX, obj.name).group(1) if obj.title_flag else None,
            skill=lambda obj: self._skills.get(obj.skill_id),
            lead_skill=lambda obj: self._lead_skills.get(obj.leader_skill_id),
            rarity_dep=lambda obj: self.rarity_dep.get(obj.rarity),
            overall_min=lambda obj: obj.vocal_min + obj.dance_min + obj.visual_min,
            overall_max=lambda obj: obj.vocal_max + obj.dance_max + obj.visual_max,
            overall_bonus=lambda obj: obj.bonus_vocal + obj.bonus_dance + obj.bonus_visual,
            valist=lambda obj: [],
            best_stat=lambda obj: determine_best_stat(obj.vocal_max, obj.visual_max, obj.dance_max))

        for p in selected:
            self.card_cache[p.id] = p
            self.primed_this["prm_card"] += 1
        self.primed_this["prm_card_calls"] += 1

    def card(self, id):
        if id not in self.card_cache:
            self.cache_cards([id])

        return self.card_cache.get(id)

    def cards(self, ids):
        ret = []
        need = []

        for id in ids:
            ret.append(self.card_cache.get(id, id))
            if isinstance(ret[-1], int):
                need.append(id)

        self.cache_cards(need)

        for idx in range(len(ret)):
            if isinstance(ret[idx], int):
                ret[idx] = self.card_cache.get(ret[idx])

        return ret

    def cards_belonging_to_char(self, id):
        return self.all_chara_id_to_cards().get(id, [])

    @lru_cache(1)
    def all_chara_id_to_cards(self):
        print("all_chara_id_to_cards")
        ret = defaultdict(lambda: [])
        idl = self.hnd.execute("SELECT chara_id, id FROM card_data WHERE evolution_id != 0")
        for cid, card in idl:
            ret[cid].append(card)
        return ret

    def chara(self, id):
        if id not in self.char_cache:
            self.cache_chars([id])

        return self.char_cache.get(id)

    def charas(self, ids):
        ret = []
        need = []

        for id in ids:
            ret.append(self.char_cache.get(id, id))
            if isinstance(ret[-1], int):
                need.append(id)

        self.cache_chars(need)

        for idx in range(len(ret)):
            if isinstance(ret[idx], int):
                ret[idx] = self.char_cache.get(ret[idx])

        return ret

    def chain(self, id):
        series_id = self.chain_id.get(id)
        if not series_id:
            return None
        return self.id_chain[series_id]

    def all_chain_ids(self):
        return sorted(self.id_chain.keys())

    def skills(self, ids):
        return [self._skills.get(id) for id in ids]

    def lead_skills(self, ids):
        return [self._lead_skills.get(id) for id in ids]

    def va_data(self, id):
        va_list = self.hnd.execute("SELECT id, use_type, `index`, voice_flag, discription, 0 AS n1 FROM card_comments WHERE id = ?", (id,))
        self.primed_this["sel_valist"] += 1
        ret = list(self.prime_from_cursor("va_data_t", va_list))

        if len(ret) == 0:
            return []

        r_va_data_t, va_data_t = self.class_cache.get("va_data_t")

        if ret[0].voice_flag:
            if id in self.char_cache:
                yield from extra_va_tables.char_voices(va_data_t, id)
            else:
                yield from extra_va_tables.card_voices(va_data_t, id, self.chain_id[id])

        yield from ret

    def svx_data(self, id):
        return self.prime_from_cursor("fp_data_t",
            self.hnd.execute("SELECT pose, position_x, position_y FROM chara_face_position WHERE chara_id = ?", (id,)))

    def translate_name(self, kanji):
        if kanji[-1] == AWAKENED_SYMBOL:
            return self.kanji_to_name.get(kanji[:-1], kanji[:-1]) + "+"
        else:
            return self.kanji_to_name.get(kanji, kanji)

    @lru_cache(1)
    def birthdays(self):
        return_value = defaultdict(lambda: [])

        for month, day, chara_id in self.hnd.execute("SELECT birth_month, birth_day, chara_id FROM chara_data WHERE birth_month + birth_day > 0"):
            return_value[(month, day)].append(chara_id)

        self.primed_this["sel_birth"] += 1
        return return_value

    def potential_birthdays(self, date):
        # the date changes depending on timezone.
        # we can't assume everyone is in UTC, so we'll
        # return every chara whose birthday is the day
        # of, the day before, or the day after the date
        # (UTC) specified in `date`.

        # If you use this method, you should filter
        # the returned values based on the actual date boundaries
        # of the user's timezone, i.e. clientside.

        yesterday = date.date() - timedelta(days=1)
        today = date.date()
        tomorrow = date.date() + timedelta(days=1)

        pool = []

        for d in [yesterday, today, tomorrow]:
            char_ids_for_this_day = self.birthdays()[(d.month, d.day)]
            pool.extend(char_ids_for_this_day)

        return self.charas(pool)

    def __del__(self):
        self.hnd.close()

def display_app_ver():
    return os.environ.get("VC_APP_VER", "(unset)")

def do_preswitch_tasks(new_db_path, old_db_path):
    print("trace do_preswitch_tasks", new_db_path, old_db_path)
    subprocess.call(["toolchain/name_finder.py",
        private_data_path("enamdictu"),
        new_db_path,
        transient_data_path("names.csv")])

    if not os.getenv("DISABLE_HISTORY_UPDATES", None):
        subprocess.call(["toolchain/update_rich_history.py", new_db_path])

    if old_db_path:
        subprocess.call(["toolchain/make_contiguous_gacha.py", old_db_path, new_db_path])

def update_to_res_ver(res_ver):
    global is_updating_to_new_truth

    def ok_to_reload(path):
        global data, last_version_check, is_updating_to_new_truth

        is_updating_to_new_truth = 0
        last_version_check = time()

        if path:
            try:
                do_preswitch_tasks(path, transient_data_path("{0}.mdb".format(data.version)) if data else None)
                data = DataCache(res_ver)
            except Exception as e:
                print("do_preswitch_tasks croaked, update aborted.")
                raise

    is_updating_to_new_truth = 1
    mdb_path = ark_data_path("{0}.mdb".format(res_ver))
    if not os.path.exists(mdb_path):
        acquisition.get_master(res_ver, transient_data_path("{0}.mdb".format(res_ver)), ok_to_reload)
    else:
        ok_to_reload(mdb_path)

def check_version_api_recv(response, msg):
    global is_updating_to_new_truth

    if response.error:
        is_updating_to_new_truth = 0
        response.rethrow()
        return

    res_ver = msg.get(b"data_headers", {}).get(b"required_res_ver", b"-1").decode("utf8")
    if not data or res_ver != data.version:
        if res_ver != "-1":
            update_to_res_ver(res_ver)
        else:
            print("no required_res_ver, did the app get a forced update?")
            print("current APP_VER:", os.environ.get("VC_APP_VER"))
            is_updating_to_new_truth = 0
            # FIXME if data is none, we'll get stuck after this
    else:
        print("we're on latest")
        is_updating_to_new_truth = 0

def can_check_version():
    return all([x in os.environ for x in ["VC_ACCOUNT", "VC_AES_KEY", "VC_SID_SALT"]]) \
        and not os.getenv("DISABLE_AUTO_UPDATES", None)

def check_version():
    global is_updating_to_new_truth, last_version_check

    if not is_updating_to_new_truth and (time() - last_version_check >= 3600
                                         or time() < last_version_check):
        if not can_check_version():
            return

        print("trace check_version")
        if data:
            data.vc_this = 1

        is_updating_to_new_truth = 1
        # usually updates happen on the hour so this keeps our
        # schedule on the hour too
        t = time()
        last_version_check = t - (t % 3600) - 90
        apiclient.versioncheck(check_version_api_recv)

is_updating_to_new_truth = 0
last_version_check = 0
data = None

def init():
    global data
    available_mdbs = sorted(list(filter(lambda x: x.endswith(".mdb"), os.listdir(transient_data_path()))), reverse=1)

    try:
        explicit_vers = int(sys.argv[1])
    except (ValueError, IndexError):
        if available_mdbs:
            explicit_vers = available_mdbs[0].split(".")[0]
        else:
            explicit_vers = 0

    if explicit_vers and os.path.exists(transient_data_path("{0}.mdb".format(explicit_vers))):
        print("Loading mdb:", explicit_vers)
        data = DataCache(explicit_vers)
    else:
        print("No mdb, let's download one")

        loop = ioloop.IOLoop.current()
        if can_check_version():
            print("We have enough secrets to do an automatic version check")
            check_version()
        else:
            try:
                vers = int(sys.argv[1])
            except (ValueError, IndexError):
                print("No data installed and we can't get it automatically. Crashing.")
                print("Hint: Try running this again with a version number.")
                print("    {0} 100xxxxx".format(sys.argv[0]))
                sys.exit(1)

            update_to_res_ver(vers)

        check = ioloop.PeriodicCallback(are_we_there_yet, 250, loop)
        check.start()
        loop.start()
        check.stop()
        ioloop.IOLoop.clear_instance()
        print("Initial download complete. Please restart the server...")
        sys.exit()

def are_we_there_yet():
    if not is_updating_to_new_truth:
        ioloop.IOLoop.instance().stop()
    else:
        print("not done yet")
