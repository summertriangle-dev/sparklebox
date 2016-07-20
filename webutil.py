import tornado.escape
import hashlib
import base64
import os
import starlight
import enums

def tlable_make_assr(text):
    if not text:
        return "@!@!"
    else:
        salt = os.getenv("TLABLE_SALT").encode("utf8")
        return base64.b64encode(hashlib.sha256(text.encode("utf8") + salt).digest()).decode("utf8")

def tlable(text, write=1):
    text = text.replace("\n", " ")
    if write:
        return """<span class="tlable" data-summertriangle-assr="{1}">{0}</span>""".format(
            tornado.escape.xhtml_escape(text), tlable_make_assr(text))
    else:
        return """<span class="tlable">{0}</span>""".format(
            tornado.escape.xhtml_escape(text))

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
