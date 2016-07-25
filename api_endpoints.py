import tornado.web
import tornado.template
import tornado.escape
from dispatch import *
import os
import json
import starlight
import hashlib
import base64
import time
import pytz
import itertools
import enums
from datetime import datetime, timedelta
from functools import partial
import webutil

@route("/api/v1/read_tl")
class TranslateReadAPI(tornado.web.RequestHandler):
    """ Queries database for cs translation entries """

    @tornado.web.asynchronous
    def post(self):
        try:
            load = json.loads(self.request.body.decode("utf8"))
        except ValueError:
            self.set_status(400)
            return self.finish()
        else:
            if not isinstance(load, list):
                self.set_status(400)
                return self.finish()

        unique = list(set(load))

        if not unique:
            self.set_header("Content-Type", "application/json; charset=utf-8")
            self.write("{}")
            self.finish()

        self.settings["tle"].translate(self.complete, *unique)

    def complete(self, ret):
        from_db = {tlo.key: tlo.english for tlo in ret if tlo.english != tlo.key}
        self.set_header("Content-Type", "application/json; charset=utf-8")
        json.dump(from_db, self, ensure_ascii=0)
        self.finish()


@route("/api/v1/send_tl")
class TranslateWriteAPI(tornado.web.RequestHandler):
    """ Save a contributed string to database.
        A security token is present to prevent spamming of random keys,
        but otherwise all strings will be accepted. """

    BAD_WORDS = ["undefined", "null", ""]

    def post(self):
        try:
            load = json.loads(self.request.body.decode("utf8"))
        except ValueError:
            self.set_status(400)
            return

        key = load.get("key", "")
        s = load.get("tled", "").strip()
        assr = load.get("security")
        #print(key, s, assr)
        if not (key and s and assr) or webutil.tlable_make_assr(key) != assr:
            self.set_status(400)
            return

        if s in self.BAD_WORDS:
            self.set_status(400)
            return

        # ** resets the string
        if s == "**":
            s = key

        self.settings["tle"].set_translation(
            load.get("key"), s, self.request.remote_ip)
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__,
                                                   {"key": key, "value": s})

class objproxy(object):
    def __init__(self, d):
        self.d = d
    def __getattr__(self, key):
        return self.d[key]

def extend_skill(self, d):
    d["explain_en"] = starlight.en.describe_skill(objproxy(d))
    d["skill_type"] = enums.skill_type(d["skill_type"])

    duration_table = d["dur"].args[0]
    probabil_table = d["chance"].args[0]

    d["effect_length"] = [duration_table[d["available_time_type"]].available_time_min,
        duration_table[d["available_time_type"]].available_time_max]
    del d["available_time_type"]

    d["proc_chance"] = [probabil_table[d["probability_type"]].probability_min,
        probabil_table[d["probability_type"]].probability_max]
    del d["probability_type"]

def extend_lead_skill(self, d):
    d["explain_en"] = starlight.en.describe_lead_skill(objproxy(d))
    d["target_attribute"] = enums.lskill_target_attr(d["target_attribute"])
    d["target_param"] = enums.lskill_target_param(d["target_param"])

def extend_card(self, d):
    d["rarity"] = d["rarity_dep"]
    del d["rarity_dep"]

    d["spread_image_ref"] = "/".join((self.settings["image_host"], "spread", "{0}.png".format(d["id"]))) \
        if d["has_spread"] else None
    d["card_image_ref"] = "/".join((self.settings["image_host"], "card", "{0}.png".format(d["id"])))
    d["sprite_image_ref"] = "/".join((self.settings["image_host"], "chara2", str(d["chara_id"]), "{0}.png".format(d["pose"])))
    d["attribute"] = enums.api_char_type(d["attribute"])

def extend_char(self, d):
    d["type"] = enums.api_char_type(d["type"])

EXTEND_FUNC = {"skill_data_t": extend_skill,
               "leader_skill_data_t": extend_lead_skill,
               "card_data_t": extend_card,
               "chara_data_t": extend_char}
KEY_BLACKLIST = {
    "skill_data_t": ["chance", "dur"]
}

class APIUtilMixin(object):
    @staticmethod
    def stub_object(obj):
        name_to_api = {"chara_data_t": "char_t",
                       "skill_data_t": "skill_t",
                       "leader_skill_data_t": "leader_skill_t",
                       "card_data_t": "card_t"}
        get_spec = {"chara_data_t": lambda x: x.chara_id}
        typename = obj.__class__.__name__

        if typename in name_to_api:
            return {"ref": "/api/v1/{0}/{1}".format(
                name_to_api.get(typename),
                get_spec.get(typename, lambda x: x.id)(obj))}

    def fix_namedtuples(self, original_typename, d, cfg):
        for key in d.keys():
            if hasattr(d[key], "_asdict"):
                if cfg["stubs"] == "yes":
                    stub = self.stub_object(d[key])
                else:
                    stub = None
                d[key] = stub or self.fix_namedtuples(d[key].__class__.__name__, d[key]._asdict(), cfg)
            elif isinstance(d[key], dict):
                d[key] = self.fix_namedtuples(d[key].__class__.__name__, d[key], cfg)
            elif isinstance(d[key], list):
                d[key] = list(self.fix_namedtuples_list(d[key], cfg))

        EXTEND_FUNC.get(original_typename, lambda self, x: None)(self, d)

        for key in KEY_BLACKLIST.get(original_typename, []):
            del d[key]

        return d

    def fix_namedtuples_list(self, alist, cfg):
        for obj in alist:
            if hasattr(obj, "_asdict"):
                if cfg["stubs"] == "yes":
                    stub = self.stub_object(obj)
                else:
                    stub = None
                yield stub or self.fix_namedtuples(obj.__class__.__name__, obj._asdict(), cfg)
            elif isinstance(obj, dict):
                yield self.fix_namedtuples(obj.__class__.__name__, obj, cfg)
            elif isinstance(obj, list):
                yield list(self.fix_namedtuples_list(d[key], cfg))
            else:
                yield obj

@route(r"/api/v1/([a-z_]+)_t/(.+)")
class ObjectAPI(HandlerSyncedWithMaster, APIUtilMixin):
    SELECTOR_ALL = object()
    SELECTOR_RANDOM = object()

    def real_expand_spec(self, spec):
        return [ int(spec) ]

    def expand_spec(self, spec):
        comp = filter(bool, spec.split(","))
        real_spec = []
        for component in comp:
            real_spec.extend(self.real_expand_spec(component))
        return real_spec

    def get(self, objectid, spec):
        try:
            ids = self.expand_spec(spec)
        except Exception as e:
            self.set_status(400)
            self.write({"error": str(e)})
            return

        self.do_object_request(objectid, ids)

    def collect_chars(self, ids, cfg):
        result = []
        for char in starlight.data.charas(ids):
            if hasattr(char, "_asdict"):
                d = self.fix_namedtuples(char.__class__.__name__, char._asdict(), cfg)
                result.append(d)
            else:
                result.append(char)

        return result

    def collect_skill(self, ids, cfg):
        result = []
        for skill in starlight.data.skills(ids):
            if hasattr(skill, "_asdict"):
                d = self.fix_namedtuples(skill.__class__.__name__, skill._asdict(), cfg)
                result.append(d)
            else:
                result.append(skill)

        return result

    def collect_lskill(self, ids, cfg):
        result = []
        for skill in starlight.data.lead_skills(ids):
            if hasattr(skill, "_asdict"):
                d = self.fix_namedtuples(skill.__class__.__name__, skill._asdict(), cfg)
                result.append(d)
            else:
                result.append(skill)

        return result

    def collect_cards(self, ids, cfg):
        result = []
        for card in starlight.data.cards(ids):
            if hasattr(card, "_asdict"):
                d = self.fix_namedtuples(card.__class__.__name__, card._asdict(), cfg)
                result.append(d)
            else:
                result.append(card)

        return result

    def do_object_request(self, kind, ids):
        cfg = {
            "stubs": self.get_argument("stubs", "no"),
            "datetime": self.get_argument("datetime", "unix")
        }
        handlers = {"card": self.collect_cards,
                    "char": self.collect_chars,
                    "skill": self.collect_skill,
                    "leader_skill": self.collect_lskill}

        h = handlers.get(kind)
        if not h:
            self.set_status(400)
            self.write({"error": "you requested an unknown object type '{0}_t'".format(kind)})
            return

        self.set_header("Content-Type", "application/json; charset=utf-8")
        if self.settings["is_dev"]:
            json.dump({"result": h(ids, cfg)}, self, ensure_ascii=0, sort_keys=1, indent=2)
        else:
            json.dump({"result": h(ids, cfg)}, self, ensure_ascii=0)

@route(r"/api/v1/list/card_t")
class CardListAPI(HandlerSyncedWithMaster, APIUtilMixin):
    KEYS = ["id", "chara_id", "attribute", "has_spread", "pose", "title", "name_only",
        "hp_min", "hp_max", "vocal_min", "vocal_max", "visual_min", "visual_max",
        "dance_min", "dance_max", "bonus_hp", "bonus_dance", "bonus_vocal", "bonus_visual",
        "evolution_id"]
    STRUCTS = ["rarity_dep"]

    def stub_object(self, obj, user_want_keys):
        base = {}

        user_want_keys = user_want_keys or (self.KEYS + self.STRUCTS)

        for key in self.KEYS:
            if key in user_want_keys:
                base[key] = getattr(obj, key)

        for key in self.STRUCTS:
            if key in user_want_keys:
                ob = getattr(obj, key)
                base[key] = self.fix_namedtuples(ob.__class__.__name__, ob._asdict(), {"stubs": "no"})

        self.post_stubbing(base, obj)

        base.update(APIUtilMixin.stub_object(obj))
        return base

    def post_stubbing(self, base, obj):
        base["conventional"] = obj.chara.conventional
        base["chara"] = APIUtilMixin.stub_object(obj.chara)

    def list_objects(self):
        return starlight.data.cards([chain[0] for _, chain in starlight.data.id_chain.items()])

    def get(self):
        ks_raw = self.get_argument("keys", "")
        if ks_raw:
            normalized = (x.lower().strip() for x in ks_raw.split(","))
        else:
            normalized = ""
        f = partial(self.stub_object, user_want_keys=list(normalized))
        roots = map(f, self.list_objects())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        if self.settings["is_dev"]:
            json.dump({"result": list(roots)}, self, ensure_ascii=0, sort_keys=1, indent=2)
        else:
            json.dump({"result": list(roots)}, self, ensure_ascii=0)

@route(r"/api/v1/list/char_t")
class CharListAPI(CardListAPI):
    KEYS = ["chara_id", "conventional", "kanji_spaced", "kana_spaced"]
    STRUCTS = []

    def list_objects(self):
        # TODO proper way to get all charids
        return starlight.data.charas(starlight.data.all_chara_id_to_cards())

    def post_stubbing(self, base, obj):
        base["cards"] = starlight.data.cards_belonging_to_char(obj.chara_id)

@route(r"/api/v1/happening/(now|-?[0-9+])")
class HappeningAPI(HandlerSyncedWithMaster, APIUtilMixin):
    def fix_datetime(self, obj):
        if isinstance(obj, datetime):
            fmt = self.get_argument("datetime", "unix")
            if fmt == "unix":
                return obj.timestamp()
            else:
                return obj.isoformat()

        raise TypeError()

    def get(self, timespec):
        if timespec == "now":
            timespec = datetime.utcnow()
        else:
            try:
                timespec = int(timespec)
            except ValueError as e:
                self.set_status(400)
                self.write({"error": str(e)})
                return
            timespec = datetime.utcfromtimestamp(timespec)
        timespec = pytz.utc.localize(timespec)

        cfg = {
            "stubs": self.get_argument("stubs", "no"),
            "datetime": self.get_argument("datetime", "unix")
        }

        self.set_header("Content-Type", "application/json; charset=utf-8")
        payload = self.fix_namedtuples("",
            {"events": starlight.data.events(timespec),
             "gachas": starlight.data.gachas(timespec)}, cfg)
        if self.settings["is_dev"]:
            json.dump(payload, self, ensure_ascii=0, sort_keys=1, indent=2, default=self.fix_datetime)
        else:
            json.dump(payload, self, ensure_ascii=0, default=self.fix_datetime)

@route(r"/api/v1/info")
class InformationAPI(HandlerSyncedWithMaster):
    def get(self):
        self.set_header("Content-Type", "application/json; charset=utf-8")

        payload = {
            "truth_version": starlight.data.version
        }

        if self.settings["is_dev"]:
            json.dump(payload, self, ensure_ascii=0, sort_keys=1, indent=2)
        else:
            json.dump(payload, self, ensure_ascii=0)

@route(r"/api/private/va_table")
class VATable(HandlerSyncedWithMaster):
    def post(self):
        try:
            load = json.loads(self.request.body.decode("utf8"))
        except ValueError:
            self.set_status(400)
            return

        has_title_call = load["has_title_call"]
        va_ids = load["va_ids"]
        unique = list(set(va_ids))
        self.render("va_table_partial.html", include_title_call=has_title_call, va_id=unique, **self.settings)
