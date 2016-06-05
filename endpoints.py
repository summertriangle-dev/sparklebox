import tornado.web
import tornado.template
import tornado.escape
from dispatch import *
import os
import json
import starlight
import time
import pytz
import itertools
import enums
from datetime import datetime, timedelta

import api_endpoints
tlable = api_endpoints.tlable

def icon(css_class):
    return """<div class="icon icon_{0}"></div>""".format(css_class)

def icon_ex(card_id, is_lowbw=0, collapsible=0):
    rec = starlight.data.card(card_id)
    if not rec:
        btext = "(?) bug:{0}".format(card_id)
        ish = """<div class="profile">
            <div class="icon icon_unknown"></div>
            <div class="profile_text {0}"><b>Mysterious Kashikoi Person</b><br>{btext}</div>
        </div>""".format("hides_under_mobile" if collapsible else "", btext=btext)
        return """<a class="noline">{ish}</a>""".format(ish=ish)
    else:
        if not is_lowbw:
            link = "/char/{rec.chara_id}#c_{rec.id}_head".format(rec=rec)
        else:
            link = "/card/{rec.id}".format(rec=rec)

        btext = "({0}) {1}".format(enums.rarity(rec.rarity), tlable(rec.title, write=0) if rec.title_flag else "")
        ish = """<div class="profile">
            <div class="icon icon_{rec.id} msprites m{1} {2}"></div>
            <div class="profile_text {3}"><b>{0}</b><br>{btext}</div>
        </div>""".format(tornado.escape.xhtml_escape(rec.chara.conventional),
            enums.stat_dot(rec.best_stat),
            "m" + enums.skill_class(rec.skill.skill_type) if rec.skill else "",
            "hides_under_mobile" if collapsible else "",
            rec=rec, btext=btext)
        return """<a href="{link}" class="noline">{ish}</a>""".format(rec=rec, ish=ish, link=link)

def audio(object_id, use, index):
    a = (object_id << 40) | ((abs(use) & 0xFF) << 24) | ((index & 0xFF) << 16) | 0x11AB
    # make everything 8 bytes long for reasons
    a &= 0xFFFFFFFFFFFFFFFF
    a ^= 0x1042FC1040200700
    basename = hex(a)[2:]

    return "va2/{0}.mp3".format(basename)

@route(r"/([0-9]+-[0-9]+-[0-9]+)?")
class Home(HandlerSyncedWithMaster):
    def get(self, pretend_date):
        if pretend_date:
            now = pytz.utc.localize(datetime.strptime(pretend_date, "%Y-%m-%d"))
        else:
            now = pytz.utc.localize(datetime.utcnow())

        if now.day == 29 and now.month == 2:
            now += timedelta(days=1)

        events = starlight.data.events(now)
        event_rewards = starlight.data.event_rewards(events)

        gachas = starlight.data.gachas(now)
        gacha_limited = starlight.data.limited_availability_cards(gachas)

        recent_history = self.settings["tle"].get_history(5)

        # cache priming has a high overhead so prime all icons at once
        preprime_set = set()
        for h in [x.asdict() for x in recent_history]:
            for k in ["n", "r", "sr", "ssr", "event"]:
                preprime_set.update(h.get(k, ()))
        starlight.data.cards(preprime_set)

        self.render("main.html", history=recent_history,
            events=zip(events, event_rewards),
            la_cards=zip(gachas, gacha_limited), **self.settings)
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__)

@route("/suggest")
class SuggestNames(HandlerSyncedWithMaster):
    def get(self):
        names = {value.conventional.lower(): [value.conventional, key] for key, value in starlight.data.names.items()}
        names.update({str(key): [value.conventional, key] for key, value in starlight.data.names.items()})

        self.set_header("Content-Type", "application/json")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Expires", "0")
        self.write(names)

@route(r"/_evt")
class EventD(HandlerSyncedWithMaster):
    def get(self):
        self.set_header("Content-Type", "text/plain; charset=utf-8")

        now = pytz.utc.localize(datetime.utcnow())
        if now.day == 29 and now.month == 2:
            now += timedelta(days=1)

        events = starlight.data.events(now)

        if events:
            evedt = events[0].end_date.astimezone(pytz.timezone("Asia/Tokyo"))
            self.set_header("Content-Type", "text/plain; charset=utf-8")
            self.write("{0}".format(evedt.strftime("%B %d, %Y %H:%M")))
        else:
            self.write("None")


@route(r"/gacha")
class GachaTable(HandlerSyncedWithMaster):
    def get(self):
        self.set_header("Content-Type", "text/plain; charset=utf-8")
        self.write("Sorry, I'll get around to implementing this soon...")

@route(r"/skill_table")
class SkillTable(HandlerSyncedWithMaster):
    def get(self):
        self.render("skill_table.html",
                    cards=starlight.data.cards(starlight.data.all_chain_ids()),
                    **self.settings)
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__)


@route(r"/lead_skill_table")
class LeadSkillTable(HandlerSyncedWithMaster):
    def get(self):
        self.render("lead_skill_table.html",
                    cards=starlight.data.cards(starlight.data.all_chain_ids()),
                    **self.settings)
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__)


@route(r"/char/([0-9]+)(/table)?")
class Character(HandlerSyncedWithMaster):
    def get(self, chara_id, use_table):
        chara_id = int(chara_id)
        achar = starlight.data.chara(chara_id)

        card_ids = starlight.data.cards_belonging_to_char(chara_id)
        chains = [starlight.data.chain(id) for id in card_ids]
        unique = []
        for c in chains:
            if c not in unique:
                unique.append(c)

        acard = [starlight.data.cards(ch) for ch in unique]
        availability = starlight.data.event_availability(card_ids)
        ga_av = self.settings["tle"].gacha_availability(card_ids, starlight.data.gacha_ids())
        for k in ga_av:
            availability[k].extend(ga_av[k])

        if achar:
            self.set_header("Content-Type", "text/html")
            self.render("chara.html",
                chara=achar,
                chara_id=chara_id,
                cards=acard,
                use_table=use_table,
                availability=availability,
                now=pytz.utc.localize(datetime.utcnow()),
                **self.settings)
            self.settings["analytics"].analyze_request(
                self.request, self.__class__.__name__, {"chara": achar.conventional})
        else:
            self.set_status(404)
            self.write("Not found.")


@route(r"/card/([0-9\,]+)(/table)?")
class Card(HandlerSyncedWithMaster):
    def get(self, card_idlist, use_table):
        card_ids = [int(x) for x in card_idlist.strip(",").split(",")]

        chains = [starlight.data.chain(id) for id in card_ids]
        unique = []
        for c in chains:
            if c not in unique:
                unique.append(c)

        acard = [starlight.data.cards(ch) for ch in unique if ch]
        availability = starlight.data.event_availability(card_ids)
        ga_av = self.settings["tle"].gacha_availability(card_ids, starlight.data.gacha_ids())
        for k in ga_av:
            availability[k].extend(ga_av[k])

        if acard:
            if len(acard) == 1:
                just_one_card = acard[0][0]
            else:
                just_one_card = None
            self.set_header("Content-Type", "text/html")
            self.render("card.html", cards=acard, use_table=use_table,
                just_one_card=just_one_card, availability=availability,
                now=pytz.utc.localize(datetime.utcnow()), **self.settings)
            self.settings["analytics"].analyze_request(
                self.request, self.__class__.__name__, {"card_id": card_idlist})
        else:
            self.set_status(404)
            self.write("Not found.")


@route(r"/sprite_go/([0-9]+).png")
class SpriteRedirect(tornado.web.RequestHandler):
    """ Javascript trampoline to locate transparents' URLs. """

    def get(self, card_id):
        card_id = int(card_id)
        assoc_card = starlight.data.card(card_id)

        assoc_char = assoc_card.chara_id
        assoc_pose = assoc_card.pose
        self.redirect("{0}/chara2/{1}/{2}.png".format(self.settings["image_host"],
                                                     assoc_char, assoc_pose))
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__,
            {"card_id": "({0}) {1} <{2}>".format(assoc_card.title, assoc_card.chara.conventional, card_id)})


@route(r"/sprite_go_ex/([0-9]+)")
class SpriteViewerEX(tornado.web.RequestHandler):
    def get(self, chara_id):
        achar = starlight.data.chara(int(chara_id))
        if achar:
            svxdata = starlight.data.svx_data(achar.chara_id)
            self.render("spriteviewer.html",
                load="{0}/chara2/{1}".format(self.settings["image_host"], int(chara_id)),
                known_poses=svxdata,
                chara=achar,
                **self.settings)
        else:
            self.set_status(404)
            self.write("Not found.")

@route("/history")
class History(HandlerSyncedWithMaster):
    """ Display all history entries. """
    def get(self):
        all_history = self.settings["tle"].get_history(nent=None)

        preprime_set = set()
        for h in [x.asdict() for x in all_history]:
            for k in ["n", "r", "sr", "ssr", "event"]:
                preprime_set.update(h.get(k, ()))
        starlight.data.cards(preprime_set)

        self.render("history.html", history=all_history, **self.settings)
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__)

@route(r"/dbgva/([^/]+)")
@dev_mode_only
class DebugViewVA(HandlerSyncedWithMaster):
    def get(self, db):
        loaded = list(starlight.card_va_by_object_id(int(db)))
        fields = loaded[0].__class__._fields

        self.set_header("Content-Type", "text/html")
        self.render("debug_view_database.html", data=loaded,
                    fields=fields, **self.settings)

@route(r"/tl_cacheall")
@dev_mode_only
class DebugTLCacheUpdate(tornado.web.RequestHandler):
    def get(self):
        self.settings["tle"].update_caches()
        self.write("ok.")

@route(r"/ga_genpresencecache")
@dev_mode_only
class DebugGachaPresenceUpdate(tornado.web.RequestHandler):
    def get(self):
        cl = self.settings["tle"].gen_presence(starlight.data.gacha_ids())
        self.set_header("Content-Type", "text/plain; charset=utf-8")
        self.write("ok")

@route(r"/tl_debug")
@dev_mode_only
class DebugViewTLs(tornado.web.RequestHandler):
    def get(self):
        #chara_id = int(chara_id)
        gen = list((x.key, x.english, x.submitter, time.strftime("%c", time.gmtime(x.submit_utc)))
            for x in filter(lambda x: x.key != x.english, self.settings["tle"].all()))
        fields = ("key", "english", "sender", "ts")

        self.set_header("Content-Type", "text/html")
        self.render("debug_view_database.html", data=gen,
                    fields=fields, **self.settings)

@route(r"/tl_debug/(.+)")
@dev_mode_only
class DebugViewTLExtreme(tornado.web.RequestHandler):
    def get(self, key):
        #chara_id = int(chara_id)
        gen = list((x.key, x.english, x.submitter, time.strftime("%c", time.gmtime(x.submit_utc)))
            for x in self.settings["tle"].all_for_key(key))
        fields = ("key", "english", "sender", "ts")

        self.set_header("Content-Type", "text/html")
        self.render("debug_view_database.html", data=gen,
                    fields=fields, **self.settings)
