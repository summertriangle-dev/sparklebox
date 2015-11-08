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
from datetime import datetime

JST = pytz.timezone("Asia/Tokyo")

try:
    import ap
except ImportError:
    # we don't have ap
    ap = None

from textwrap import dedent


def tlable_make_assr(text):
    if not text:
        return "@!@!"
    else:
        salt = os.getenv("TLABLE_SALT").encode("utf8")
        return base64.b64encode(hashlib.sha256(text.encode("utf8") + salt).digest()).decode("utf8")


def tlable(text):
    return """<span class="tlable" data-summertriangle-assr="{1}">{0}</span>""".format(
        tornado.escape.xhtml_escape(text), tlable_make_assr(text))


def icon(css_class):
    return """<div class="icon icon_{0}"></div>""".format(css_class)


expose_static_json("/suggest",
                   {value.conventional.lower(): [value.conventional, key] for key, value in starlight.names.items()})


def sieve_diff_contents(de):
    ret = {
        "event": [],
        "ssr": [],
        "sr": [],
        "r": [],
        "n": []
    }
    for card_id in filter(lambda x: starlight.card_db[x].evolution_id, de["cids"]):
        if card_id in event_cards:
            ret["event"].append(card_id)
        else:
            key = ["n", "n", "r", "r", "sr", "sr", "ssr", "ssr"][starlight.card_db[card_id].rarity - 1]
            ret[key].append(card_id)
    return {"date": de["date"], "cids": ret}
event_cards = [x.reward_id for x in starlight.cached_db(starlight.ark_data_path("event_available.txt"))]
HISTORY = [sieve_diff_contents(x) for x in reversed(starlight.jsonl(starlight.private_data_path("history.json")))]

@route(r"/")
class Home(tornado.web.RequestHandler):
    def get(self):
        eda = starlight.cached_db(starlight.ark_data_path("event_data.txt"))
        now = pytz.utc.localize(datetime.utcnow())
        for event in eda:
            if (now > JST.localize(datetime.strptime(event.event_start, "%Y-%m-%d %H:%M:%S")) and
                now < JST.localize(datetime.strptime(event.event_end, "%Y-%m-%d %H:%M:%S"))):
                break
        else:
            event = None

        # FIXME this is ridiculous. i just want to convert a fucking timestamp to a fucking UTC timestamp.
        event_end = time.mktime(JST.localize(datetime.strptime(event.event_end, "%Y-%m-%d %H:%M:%S")).astimezone(pytz.utc).timetuple())

        self.render("main.html", history=HISTORY, has_event=bool(event), event=event, event_end=event_end, **self.settings)
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__)


@route(r"/skill_table")
class SkillTable(tornado.web.RequestHandler):
    def get(self):
        self.render("skill_table.html",
                    cards=starlight.evolutionary_chains,
                    **self.settings)
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__)


@route(r"/lead_skill_table")
class LeadSkillTable(tornado.web.RequestHandler):
    def get(self):
        self.render("lead_skill_table.html",
                    cards=starlight.evolutionary_chains,
                    **self.settings)
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__)


@route(r"/char/([0-9]+)")
class Character(tornado.web.RequestHandler):
    def get(self, chara_id):
        chara_id = int(chara_id)
        achar = starlight.chara_db.get(chara_id)

        if achar:
            self.set_header("Content-Type", "text/html")
            self.render("chara.html",
                chara=achar,
                chara_id=chara_id,
                cards=starlight.evolutionary_chains,
                **self.settings)
            self.settings["analytics"].analyze_request(
                self.request, self.__class__.__name__, {"chara": achar.conventional})
        else:
            self.set_status(404)
            self.write("Not found.")


@route(r"/card/([0-9\,]+)")
class Card(tornado.web.RequestHandler):
    def get(self, card_idlist):
        card_ids = [int(x) for x in card_idlist.strip(",").split(",")]

        acard = [starlight.evolutionary_chains[x.series_id]
                 for x in filter(bool, [starlight.card_db.get(x) for x in card_ids])]

        if acard:
            self.set_header("Content-Type", "text/html")
            self.render("card.html", cards=acard, **self.settings)
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
        assoc_card = starlight.card_db[card_id]

        assoc_char = assoc_card.chara_id
        assoc_pose = assoc_card.pose
        self.redirect("{0}/chara/{1}/{2}.png".format(self.settings["image_host"],
                                                     assoc_char, assoc_pose))
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__,
            {"card_id": "({0}) {1} <{2}>".format(assoc_card.title, assoc_card.chara.conventional, card_id)})


@route("/read_tl")
class TranslateReadAPI(tornado.web.RequestHandler):
    """ Queries database for cs translation entries """

    @tornado.web.asynchronous
    def post(self):
        try:
            load = json.loads(self.request.body.decode("utf8"))
        except ValueError:
            self.set_status(400)
            return
        else:
            if not isinstance(load, list):
                self.set_status(400)
                return

        unique = list(set(load))

        if not unique:
            self.set_header("Content-Type", "application/json; charset=utf-8")
            self.write("{}")
            self.finish()

        self.settings["tle"].translate(self.complete, *unique)

    def complete(self, ret):
        from_db = {tlo.key: tlo.english for tlo in ret if tlo.english != tlo.key}
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps(from_db))
        self.finish()


@route("/send_tl")
class TranslateWriteAPI(tornado.web.RequestHandler):
    """ Save a contributed string to database.
        A security token is present to prevent spamming of random keys,
        but otherwise all strings will be accepted. """

    def post(self):
        try:
            load = json.loads(self.request.body.decode("utf8"))
        except ValueError:
            self.set_status(400)
            return

        key = load.get("key", "")
        s = load.get("tled", "").strip() or key
        assr = load.get("security")
        print(key, s, assr)
        if not (key and s and assr) or tlable_make_assr(key) != assr:
            self.set_status(400)
            return

        self.settings["tle"].set_translation(
            load.get("key"), s, self.request.remote_ip)
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__,
                                                   {"key": key, "value": s})

# @route(r"/room/app")
# class RoomSimMain(tornado.web.RequestHandler):
#     def get(self):
#         self.set_header("Content-Type", "text/html; charset=utf-8")
#         self.render("room_sim_main.html", **self.settings)


@route(r"/db/")
@dev_mode_only
class DebugListDatabase(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "text/html")
        self.write("<pre>")
        for file in os.listdir("_data/ark"):
            self.write("<a href='/db/{0}'>{0}</a>\n".format(file))
        self.write("</pre>")


@route(r"/db/([^/]+)")
@dev_mode_only
class DebugViewDatabase(tornado.web.RequestHandler):
    def get(self, db):
        loaded = list(starlight.cached_db(starlight.ark_data_path(db)))
        fields = loaded[0].__class__._fields

        self.set_header("Content-Type", "text/html")
        self.render("debug_view_database.html", data=loaded,
                    fields=fields, **self.settings)


@route(r"/tl_debug")
@dev_mode_only
class DebugViewTLs(tornado.web.RequestHandler):
    def get(self):
        #chara_id = int(chara_id)
        gen = list((x.key, x.english, x.submitter, time.strftime("%c", time.gmtime(x.submit_utc)))
            for x in self.settings["tle"].all())
        fields = ("key", "english", "sender", "ts")

        self.set_header("Content-Type", "text/html")
        self.render("debug_view_database.html", data=gen,
                    fields=fields, **self.settings)


@route(r"/story_list")
class ListScripts(tornado.web.RequestHandler):
    banner = dedent("""\
    Communication scripts in wiki format (https://hpt.moe/deresute/).

    "antl" stands for automatic name translation. Speaker names will be
    automatically filled with romanized versions.

    """)

    def write_story_ent(self, story):
        if story.story_detail_type not in (1, 2, 3, 11):
            return

        self.write("[<a href='/get_story/{x.dialog_id}?names=NO'>get script</a>] "
                   "[<a href='/get_story/{x.dialog_id}?names=YES'>+ antl</a>]".format(x=story))
        if story.story_detail_type == 1:
            self.write(
                "\t Main Story: {x.title}\t {x.sub_title}\n".format(x=story))
        elif story.story_detail_type == 2:
            assoc_card = starlight.card_db[story.open_card_id]
            self.write("\t Episode: <a href='/card/{2}'>{0} [{1}]</a>\n".format(
                assoc_card.chara.conventional, assoc_card.title, assoc_card.id, x=story))
        elif story.story_detail_type == 3:
            assoc_chara = starlight.chara_db[story.open_chara_id]
            self.write("\t Memorial: <a href='/char/{1}'>{0}</a>, Ch.{x.chapter}\n".format(
                assoc_chara.conventional, assoc_chara.chara_id, x=story))
        elif story.story_detail_type == 11:
            self.write("\t Event:\t {x.title} {x.sub_title}\n".format(x=story))

    def story_exists(self, entry):
        absolute = starlight.story_data_path(
            "storydata_{0}.txt".format(entry.dialog_id))
        if not os.path.exists(absolute):
            return 0
        return 1

    def get(self):
        gen = sorted(starlight.cached_db(starlight.ark_data_path(
            "story_detail.txt")), key=lambda x: (x.story_detail_type, x.dialog_id))

        self.set_header("Content-Type", "text/html; charset=utf-8")
        self.write("<pre>")
        self.write(self.banner)
        for story in gen:
            if self.story_exists(story):
                self.write_story_ent(story)
        self.write("</pre>")


@conditional_route(ap, "/get_story/... will not be routed because ap could not be imported.",
                   r"/get_story/([0-9]+)")
class GetScript(tornado.web.RequestHandler):
    banner = dedent("""\
    Asking ap to dump script...
    A syntax-highlighting text editor will make this easier to read.

    --8<-------------------Copy below this line---------------------

    """)

    def get(self, story_id):
        if self.get_argument("names", "NO") == "YES":
            ap.load_name_map(starlight.private_data_path("names.csv"))
        else:
            ap.NAME_MAP = {}

        absolute = starlight.story_data_path(
            "storydata_{0}.txt".format(story_id))
        if not os.path.exists(absolute):
            self.set_status(404)
            self.write("Script not found.")
            return

        self.set_header("Content-Type", "text/plain; charset=utf-8")
        self.write(self.banner)
        ap.format_for_wiki(absolute,
                           lambda *x: self.write(" ".join(x) + "\n"))
