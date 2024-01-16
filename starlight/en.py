import csvloader
import functools
import os
import re

NO_STRING_FMT = "<Voice ID {0}:{1}:{2} has no transcript, but you can still submit a translation for it.>"

def westernized_name(chara):
    """Our conventionals are ordered Last First, but project-imas uses First Last."""
    if " " in chara.kanji_spaced:
        # "The majority of Japanese people have one surname and one given name with no middle name,"
        # in case that proves false, here's an implementation that reverses
        # "Last First Middle" -> "First Middle Last".

        # names = chara.conventional.split(" ")
        # return "{0} {1}".format(" ".join(names[1:]), names[0]).strip()
        return " ".join(reversed(chara.conventional.split(" ")))
    else:
        return chara.conventional

def availability_date_range(a, now):
    if a.start.year == a.end.year:
        return "{0}; {1} ~ {2}".format(
            a.start.strftime("%Y"),
            a.start.strftime("%d %B"),
            a.end.strftime("%d %B") if a.end < now else "present",
        )
    else:
        return "{0} ~ {1}".format(
            a.start.strftime("%Y %b %d"),
            a.end.strftime("%Y %b %d") if a.end < now else "present",
        )

def gap_date_range(a):
    delta = (a.end - a.start)
    return "{0} ~ {1} ({2} d)".format(
        a.start.strftime("%d %B"),
        a.end.strftime("%d %B"),
        round(delta.days + (delta.seconds / 86400))
    )

# skill describer

SKILL_DESCRIPTIONS = {
    1: """that Perfect notes will receive a <span class="let">{0}</span>% score bonus""",
    2: """that Great/Perfect notes will receive a <span class="let">{0}</span>% score bonus""",
    3: """that Nice/Great/Perfect notes will receive a <span class="let">{0}</span>% score bonus""", #provisional
    4: """that you will gain an extra <span class="let">{0}</span>% combo bonus""",
    5: """that Great notes will become Perfect notes""",
    6: """that Nice/Great notes will become Perfect notes""",
    7: """that Bad/Nice/Great notes will become Perfect notes""",
    8: """that all notes will become Perfect notes""", #provisional
    9: """that Nice notes will not break combo""",
    10: """that Bad/Nice notes will not break combo""", #provisional
    11: """that your combo will not be broken""", #provisional
    12: """that life will not decrease""",
    13: """that all notes will restore <span class="let">{0}</span> life""", #provisional
    14: """that <span class="let">{1}</span> life will be consumed to apply a/an <span class="let">{0}</span>% Perfect/Great score bonus, and prevent Nice/Bad notes from breaking combo""",
    15: """that Perfect notes will receive a <span class="let">{0}</span>% score bonus""", #provisional
    16: """to activate the previous skill again""",
    17: """that Perfect notes will restore <span class="let">{0}</span> life""",
    18: """that Great/Perfect notes will restore <span class="let">{0}</span> life""", #provisional
    19: """that Nice/Great/Perfect notes will restore <span class="let">{0}</span> life""", #provisional
    20: """to boost the effects of currently active skills""",
    21: """that Perfect notes will receive a <span class="let">{0}</span>% score bonus, and you will gain an extra <span class="let">{2}</span>% combo bonus""",
    22: """that Perfect notes will receive a <span class="let">{0}</span>% score bonus, and you will gain an extra <span class="let">{2}</span>% combo bonus""",
    23: """that Perfect notes will receive a <span class="let">{0}</span>% score bonus, and you will gain an extra <span class="let">{2}</span>% combo bonus""",
    24: """that you will gain an extra <span class="let">{0}</span>% combo bonus, and Perfect notes will restore <span class="let">{2}</span> life""",
    25: """that you will gain an extra <a href="/sparkle_internal/{0}">combo bonus based on your current life</a>""",
    26: """that you will gain an extra <span class="let">{2}</span>% combo bonus, and Perfect notes will receive a <span class="let">{0}</span>% score bonus plus restore <span class="let">{3}</span> life""",
    27: """that Perfect notes will receive a <span class="let">{0}</span>% score bonus, and you will gain an extra <span class="let">{2}</span>% combo bonus""",
    28: """that Perfect notes will receive a <span class="let">{0}</span>% score bonus, and hold notes a <span class="let">{2}</span>% score bonus""",
    29: """that Perfect notes will receive a <span class="let">{0}</span>% score bonus, and flick notes a <span class="let">{2}</span>% score bonus""",
    30: """that Perfect notes will receive a <span class="let">{0}</span>% score bonus, and slide notes a <span class="let">{2}</span>% score bonus""",
    31: """that you will gain an extra <span class="let">{0}</span>% combo bonus, and Nice/Great notes will become Perfect notes""",
    32: """to boost the score/combo bonus of Cute idols' active skills""",
    33: """to boost the score/combo bonus of Cool idols' active skills""",
    34: """to boost the score/combo bonus of Passion idols' active skills""",
    35: """that Perfect notes will receive a <a href="/motif_internal/{0}?appeal=vocal">score bonus determined by the team's Vocal appeal</a>""",
    36: """that Perfect notes will receive a <a href="/motif_internal/{0}?appeal=dance">score bonus determined by the team's Dance appeal</a>""",
    37: """that Perfect notes will receive a <a href="/motif_internal/{0}?appeal=visual">score bonus determined by the team's Visual appeal</a>""",
    38: """that with all three types of idols on the team, to boost the score/combo bonus/life recovery of currently active skills""",
    39: """to reduce combo bonus by <span class="let">{0}</span>%, but also apply the highest score bonus gained so far with a boost of <span class="let">{2}</span>%""",
    40: """to apply the effect of the best score or combo bonus skill activated so far""",
    41: """to activate all skills on the team, then apply the best available score/combo bonus to each note""",
    42: """to reduce score gain by <span class="let">{0}</span>%, but also apply the highest extra combo bonus gained so far with a boost of <span class="let">{2}</span>%""",
    43: """to increase combo bonus by <span class="let">{0}</span>%, and Perfect notes will restore <span class="let">{2}</span> life""",
    44: """that <span class="let">{1}</span> life will be consumed to apply an extra <span class="let">{2}</span>% combo bonus, and a <span class="let">{1}</span>% Perfect score bonus, """,
    # Dominant variants
    45: """to boost the score bonus of Cute idols' active skills, and the combo bonus of Cool idols' active skills""",
    46: """to boost the score bonus of Cute idols' active skills, and the combo bonus of Passion idols' active skills""",
    47: """to boost the score bonus of Cool idols' active skills, and the combo bonus of Cute idols' active skills""",
    48: """to boost the score bonus of Cool idols' active skills, and the combo bonus of Passion idols' active skills""",
    49: """to boost the score bonus of Passion idols' active skills, and the combo bonus of Cute idols' active skills""",
    50: """to boost the score bonus of Passion idols' active skills, and the combo bonus of Cool idols' active skills""",
}

SKILL_CAVEATS = {
    15: "The timing window for Perfect notes becomes smaller during this time.",
    21: "All idols on your team must be Cute-type.",
    22: "All idols on your team must be Cool-type.",
    23: "All idols on your team must be Passion-type.",
    26: "Only when all three types of idols are on the team.",
    41: "Bonuses are subject to the conditions of each skill.",
    43: "Great notes will break your combo during this time.",
    44: "Only when playing an all-type song with all three types of idols on the team."
}

SKILL_TRIGGER_DUAL_TYPE = {
    12: ("Cute", "Cool"),
    13: ("Cute", "Passion"),
    21: ("Cool", "Cute"),
    23: ("Cool", "Passion"),
    31: ("Passion", "Cute"),
    32: ("Passion", "Cool"),
}

SKILL_TYPES_WITH_PERCENTAGE_EFF_VAL1 = [1, 2, 3, 4, 14, 15, 21, 22, 23, 24, 26, 27, 28, 29, 30, 31, 39, 42, 43, 44]
SKILL_TYPES_WITH_PERCENTAGE_EFF_VAL2 = [21, 22, 23, 26, 27, 28, 29, 30, 44]

# Whether the skill's description uses the value in a negative context
# (e.g. ...reduces by x%...)
SKILL_TYPES_WITH_NEGATIVE_EFF_VAL1 = [39, 42]
SKILL_TYPES_WITH_NEGATIVE_EFF_VAL2 = []

SKILL_TYPES_WITH_THOUSANDTHS_EFF_VAL1 = [20]
SKILL_TYPES_WITH_THOUSANDTHS_EFF_VAL2 = [39, 42]

REMOVE_HTML = re.compile(r"</?(span|a)[^>]*>")

def describe_skill(skill):
    return REMOVE_HTML.sub("", describe_skill_html(skill))

def describe_lead_skill(lskill):
    return REMOVE_HTML.sub("", describe_lead_skill_html(lskill))

def skill_caveat_from_trigger_type(skill):
    if skill.skill_trigger_type == 6:
        pair = SKILL_TRIGGER_DUAL_TYPE.get(skill.skill_trigger_value, ("?", "?"))
        return "Only when team consists of just {0} and {1} idols.".format(*pair)

    return None

def describe_skill_html(skill):
    if skill is None:
        return "No effect"

    fire_interval = skill.condition
    effect_val = skill.value
    # TODO symbols
    if skill.skill_type in SKILL_TYPES_WITH_PERCENTAGE_EFF_VAL1:
        effect_val -= 100
    elif skill.skill_type in SKILL_TYPES_WITH_THOUSANDTHS_EFF_VAL1:
        effect_val = (effect_val // 10) - 100

    if skill.skill_type in SKILL_TYPES_WITH_NEGATIVE_EFF_VAL1:
        effect_val = -effect_val

    value_2 = skill.value_2
    if skill.skill_type in SKILL_TYPES_WITH_PERCENTAGE_EFF_VAL2:
        value_2 -= 100
    elif skill.skill_type in SKILL_TYPES_WITH_THOUSANDTHS_EFF_VAL2:
        value_2 = (value_2 // 10) - 100

    if skill.skill_type in SKILL_TYPES_WITH_NEGATIVE_EFF_VAL2:
        value_2 = -value_2

    value_3 = skill.value_3

    effect_clause = SKILL_DESCRIPTIONS.get(
        skill.skill_type, "").format(effect_val, skill.skill_trigger_value, value_2, value_3)
    interval_clause = """Every <span class="let">{0}</span> seconds:""".format(
        fire_interval)
    probability_clause = """there is a <span class="var">{0}</span>% chance""".format(
        skill.chance())
    length_clause = """for <span class="var">{0}</span> seconds.""".format(
        skill.dur())
    
    caveat_fmt = SKILL_CAVEATS.get(skill.skill_type)

    if not caveat_fmt:
        caveat_fmt = skill_caveat_from_trigger_type(skill)

    if caveat_fmt:
        caveat_fmt = """<span class="caveat">({0})</span>""".format(caveat_fmt)
        return " ".join((interval_clause, probability_clause, effect_clause, length_clause, caveat_fmt))

    return " ".join((interval_clause, probability_clause, effect_clause, length_clause))


LEADER_SKILL_TARGET = {
    1: "all Cute",
    2: "all Cool",
    3: "all Passion",
    4: "all",

    11: "Cute-type",
    12: "Cool-type",
    13: "Passion-type",
    14: "all-type",
}

LEADER_SKILL_PARAM = {
    1: "the Vocal appeal",
    2: "the Visual appeal",
    3: "the Dance appeal",
    4: "all appeals",
    5: "the life",
    6: "the skill probability",
    # FIXME: only grammatically works when used in world level desc
    # FIXME: find variants for other stats
    13: "own Dance appeal"
}

def build_lead_skill_predicate(skill):
    need_list = []
    need_sum = 0
    if skill.need_cute:
        need_list.append("Cute")
        need_sum += skill.need_cute
    if skill.need_cool:
        need_list.append("Cool")
        need_sum += skill.need_cool
    if skill.need_passion:
        need_list.append("Passion")
        need_sum += skill.need_passion

    if len(need_list) == 0:
        need_str = None
    elif len(need_list) == 1:
        need_str = need_list[0]
    elif len(need_list) == 2:
        need_str = "{0} and {1}".format(*need_list)
    else:
        need_str = ", ".join(need_list[:-1])
        need_str = "{0}, and {1}".format(need_str, need_list[-1])

    if len(need_list) < 3 and need_sum >= 5:
        need_str = "only " + need_str

    if skill.need_skill_variation > 1 and need_list:
        return """If the team has at least {1} different skill types, and there are {0} idols on the team:""".format(need_str, skill.need_skill_variation)
    elif skill.need_skill_variation > 1:
        return """If the team has at least {0} different skill types:""".format(skill.need_skill_variation)
    elif need_list:
        return """If there are {0} idols on the team:""".format(need_str)
    else:
        return None

def describe_lead_skill_html(skill):
    if skill is None:
        return "No effect"

    if skill.up_type == 1 and skill.type == 20:
        target_attr = LEADER_SKILL_TARGET.get(skill.target_attribute, "<unknown>")
        target_param = LEADER_SKILL_PARAM.get(skill.target_param, "<unknown>")

        effect_clause = """Raises {0} of {1} members by <span class="let">{2}</span>%""".format(
            target_param, target_attr, skill.up_value)
    elif skill.up_type == 1 and skill.type == 30:
        if skill.up_value == 12:
            # Riina
            effect_clause = "May drop star pieces when you finish a live. The drop rate scales based on star rank"
        else:
            effect_clause = "May give extra rewards when you finish a live. The drop rate scales based on star rank"
    elif skill.up_type == 1 and skill.type == 40:
        effect_clause = "Increases fan gain by <span class=\"let\">{0}</span>% when you finish a live".format(
            skill.up_value)
    elif skill.type == 50:
        target_attr = LEADER_SKILL_TARGET.get(skill.target_attribute, "<unknown>")
        target_param = LEADER_SKILL_PARAM.get(skill.target_param, "<unknown>")

        target_attr_2 = LEADER_SKILL_TARGET.get(skill.target_attribute_2, "<unknown>")
        target_param_2 = LEADER_SKILL_PARAM.get(skill.target_param_2, "<unknown>")

        effect_clause = """Raises {0} of {1} members by <span class="let">{2}</span>%, and {3} of {4} members by <span class="let">{5}</span>%""".format(
            target_param, target_attr, skill.up_value, target_param_2, target_attr_2, skill.up_value_2)
    elif skill.type == 60:
        target_attr = LEADER_SKILL_TARGET.get(skill.target_attribute, "<unknown>")
        target_param = LEADER_SKILL_PARAM.get(skill.target_param, "<unknown>")

        target_attr_2 = LEADER_SKILL_TARGET.get(skill.target_attribute_2, "<unknown>")
        target_param_2 = LEADER_SKILL_PARAM.get(skill.target_param_2, "<unknown>")

        if target_param_2 != target_param:
            effect_clause = """Raises {0} of {1} members by <span class="let">{2}</span>% (and {3} by <span class="let">{4}</span>% when playing a {5} song)""".format(
                target_param, target_attr, skill.up_value, target_param_2, skill.up_value_2, target_attr_2)
        else:
            effect_clause = """Raises {0} of {1} members by <span class="let">{2}</span>% (<span class="let">{3}</span>% when playing a {4} song)""".format(
                target_param, target_attr, skill.up_value, skill.up_value_2, target_attr_2)
    elif skill.type == 70:
        target_param = LEADER_SKILL_PARAM.get(skill.param_limit, "<unknown>")

        effect_clause = """Allows active skill effects to stack, but only {0} of the team applies during the live""".format(
                target_param)
    elif skill.type == 80:
        effect_clause = """Raises the XP, money, and friend points that you (and your guest's producer) receive by <span class="let">{0}</span>% when you finish a live""".format(
            skill.up_value)
    elif skill.type == 90:
        target_param = LEADER_SKILL_PARAM.get(skill.target_param, "<unknown>")
        target_attr_2 = LEADER_SKILL_TARGET.get(skill.target_attribute_2, "<unknown>")
        target_param_2 = LEADER_SKILL_PARAM.get(skill.target_param_2, "<unknown>")
        effect_clause = """Raises this card's {0} by <span class="let">{1}</span>%. If this card's costume is equipped and on your own team, raises {2} of {3} members by <span class="let">{4}</span>% when her mask is removed""".format(
            target_param, skill.up_value, target_param_2, target_attr_2, skill.up_value_2)
    elif skill.type == 100:
        effect_clause = """Each member on your team will receive the best available leader effect from your team (including your guest's leader effect)"""
    elif skill.type == 110:
        song_attr = LEADER_SKILL_TARGET.get(skill.target_attribute_2 + 10, "<unknown>")
        target_param = LEADER_SKILL_PARAM.get(skill.target_param, "<unknown>")
        target_param_2 = LEADER_SKILL_PARAM.get(skill.target_param_2, "<unknown>")
        effect_clause = """Raises {0} of all cards by <span class="let">{1}</span>%, and {2} of all cards by <span class="let">{3}</span>% (when playing a {4} song)""".format(
            target_param, skill.up_value, target_param_2, skill.up_value_2, song_attr)
    elif skill.type == 120:
        target_attr = LEADER_SKILL_TARGET.get(skill.target_attribute, "<unknown>")
        target_param = LEADER_SKILL_PARAM.get(skill.target_param, "<unknown>")

        target_attr_2 = LEADER_SKILL_TARGET.get(skill.target_attribute_2, "<unknown>")
        target_param_2 = LEADER_SKILL_PARAM.get(skill.target_param_2, "<unknown>")

        type_bonus_target = LEADER_SKILL_TARGET.get(skill.target_attribute + 10, "<unknown>")
        song_attr = LEADER_SKILL_TARGET.get(skill.target_attribute_2 + 10, "<unknown>")
        effect_clause = """Raise {2} of {3} cards by <span class="let">{4}%</span>, and {5} of {6} cards by <span class="let">{7}</span>%. {0} cards will also receive the type bonus from {1} songs""".format(
            type_bonus_target, song_attr, target_param, target_attr, skill.up_value, target_param_2, target_attr_2, skill.up_value_2)
    else:
        return """I don't know how to describe this leader skill. This is a bug, please report it. (up_type: {0}, type: {1})""".format(
            skill.up_type, skill.type
        )

    predicate_clause = build_lead_skill_predicate(skill)
    if predicate_clause:
        built = " ".join((predicate_clause, effect_clause))
    else:
        built = effect_clause
    return built + "."
