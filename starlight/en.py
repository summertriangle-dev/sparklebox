import re
from html import escape

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
    1: """to increase Perfect note scores by <span class="let">{0}</span>%""",
    2: """to increase Perfect/Great note scores by <span class="let">{0}</span>%""",
    3: """to increase Perfect/Great/Nice note scores by <span class="let">{0}</span>%""", #provisional
    4: """to increase the combo bonus by <span class="let">{0}</span>%""",
    5: """that Great notes will become Perfect notes""",
    6: """that Great/Nice notes will become Perfect notes""",
    7: """that Great/Nice/Bad notes will become Perfect notes""",
    8: """that all notes will become Perfect notes""", #provisional
    9: """that Nice notes will not break combo""",
    10: """that Nice/Bad notes will not break combo""", #provisional
    11: """that your combo will not be broken""", #provisional
    12: """that life will not decrease""",
    13: """that all notes will restore <span class="let">{0}</span> life""", #provisional
    14: """that <span class="let">{1}</span> life will be consumed to increase Perfect/Great note scores by <span class="let">{0}</span>%, and prevent Nice/Bad notes from breaking the combo""",
    15: """to increase Perfect note scores by <span class="let">{0}</span>%""", #provisional
    16: """to activate the previous skill again""",
    17: """that Perfect notes will restore <span class="let">{0}</span> life""",
    18: """that Perfect/Great notes will restore <span class="let">{0}</span> life""", #provisional
    19: """that Perfect/Great/Nice notes will restore <span class="let">{0}</span> life""", #provisional
    20: """to boost the effects of currently active skills""",
    21: """to increase Perfect note scores by <span class="let">{0}</span>%, and the combo bonus by <span class="let">{2}</span>%""",
    22: """to increase Perfect note scores by <span class="let">{0}</span>%, and the combo bonus by <span class="let">{2}</span>%""",
    23: """to increase Perfect note scores by <span class="let">{0}</span>%, and the combo bonus by <span class="let">{2}</span>%""",
    24: """to increase the combo bonus by <span class="let">{0}</span>%, and Perfect notes will restore <span class="let">{2}</span> life""",
    25: """that you will gain a <a href="/sparkle_internal/{0}">combo bonus based on your current life</a>""",
    26: """to increase the combo bonus by <span class="let">{2}</span>%, and Perfect notes will receive a <span class="let">{0}</span>% score bonus plus restore <span class="let">{3}</span> life""",
    27: """to increase Perfect note scores by <span class="let">{0}</span>%, and the combo bonus by<span class="let">{2}</span>%""",
    28: """to increase Perfect note scores by <span class="let">{0}</span>%, and hold notes will receive a <span class="let">{2}</span>% score bonus""",
    29: """to increase Perfect note scores by <span class="let">{0}</span>%, and flick notes will receive a <span class="let">{2}</span>% score bonus""",
    30: """to increase Perfect note scores by <span class="let">{0}</span>%, and slide notes will receive a <span class="let">{2}</span>% score bonus""",
    31: """to increase the combo bonus by <span class="let">{0}</span>%, and Great/Nice notes will become Perfect notes""",
    32: """to boost the score/combo bonus of Cute idols' active skills""",
    33: """to boost the score/combo bonus of Cool idols' active skills""",
    34: """to boost the score/combo bonus of Passion idols' active skills""",
    35: """that Perfect notes will receive a <a href="/motif_internal/{0}?appeal=vocal">score bonus determined by the team's Vocal appeal</a>""",
    36: """that Perfect notes will receive a <a href="/motif_internal/{0}?appeal=dance">score bonus determined by the team's Dance appeal</a>""",
    37: """that Perfect notes will receive a <a href="/motif_internal/{0}?appeal=visual">score bonus determined by the team's Visual appeal</a>""",
    38: """to boost the score/combo bonus/life recovery effects of currently active skills""",
    39: """to reduce combo bonus by <span class="let">{0}</span>%, but also apply the highest score bonus gained so far with a <span class="let">{2}</span>% boost""",
    40: """to apply the effect of the best score or combo bonus skill activated so far""",
    41: """to activate all skills on the team, then apply the best available score/combo bonus to each note""",
    42: """to reduce score gain by <span class="let">{0}</span>%, but also apply the highest extra combo bonus gained so far with a <span class="let">{2}</span>% boost""",
    43: """to increase the combo bonus by <span class="let">{0}</span>%, and Perfect notes will restore <span class="let">{2}</span> life""",
    44: """that <span class="let">{1}</span> life will be consumed to increase the combo bonus by <span class="let">{2}</span>%, and Perfect note scores by <span class="let">{1}</span>%""",
    # Dominant variants
    45: """to boost the score bonus of Cute idols' active skills, and the combo bonus of Cool idols' active skills""",
    46: """to boost the score bonus of Cute idols' active skills, and the combo bonus of Passion idols' active skills""",
    47: """to boost the score bonus of Cool idols' active skills, and the combo bonus of Cute idols' active skills""",
    48: """to boost the score bonus of Cool idols' active skills, and the combo bonus of Passion idols' active skills""",
    49: """to boost the score bonus of Passion idols' active skills, and the combo bonus of Cute idols' active skills""",
    50: """to boost the score bonus of Passion idols' active skills, and the combo bonus of Cool idols' active skills""",
    51: """At the start of a live, sets life to <span class="let">200</span>% of its maximum and reduces all incoming damage by <span class="let">50</span>%."""
}

SKILL_CAVEATS = {
    15: "The timing window for Perfect notes will be smaller during this time.",
    21: "All idols on your team must be Cute types.",
    22: "All idols on your team must be Cool types.",
    23: "All idols on your team must be Passion types.",
    26: "Only when all three types of idols are on the team.",
    38: "Only when all three types of idols are on the team.",
    41: "Bonuses are subject to the conditions of each skill.",
    43: "Your combo will only continue on Perfect notes during this time.",
    44: "Only when playing an all-type song with all three types of idols on the team.",
    45: "Only when playing a Cool-type song with only Cute and Cool-type idols on the team.",
    46: "Only when playing a Passion-type song with only Cute and Passion-type idols on the team.",
    47: "Only when playing a Cute-type song with only Cool and Cute-type idols on the team.",
    48: "Only when playing a Passion-type song with only Cool and Passion-type idols on the team.",
    49: "Only when playing a Cute-type song with only Passion and Cute-type idols on the team.",
    50: "Only when playing a Cool-type song with only Passion and Cool-type idols on the team.",
    51: "Cannot be re-activated by the effect of Encore or Cinderella Magic."
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

SKILL_TYPES_WITH_GLOBAL_EFFECT = [51]

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

def skill_fallback_html(skill):
    return """{0} <span class="caveat">(Translated effects are not yet available for this skill.)</span>""".format(escape(skill.explain))

def describe_skill_html(skill):
    if skill is None:
        return "No effect"

    effect_fmt = SKILL_DESCRIPTIONS.get(skill.skill_type)
    if effect_fmt is None:
        return skill_fallback_html(skill)

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

    effect_clause = effect_fmt.format(effect_val, skill.skill_trigger_value, value_2, value_3)
    
    caveat_fmt = SKILL_CAVEATS.get(skill.skill_type)
    if caveat_fmt:
        caveat_clause = """<span class="caveat">({0})</span>""".format(caveat_fmt)
    else:
        caveat_clause = ""

    if skill.skill_type in SKILL_TYPES_WITH_GLOBAL_EFFECT:
        return " ".join((effect_clause, caveat_clause))

    interval_clause = """Every <span class="let">{0}</span> seconds,""".format(
        fire_interval)
    probability_clause = """there is a <span class="var">{0}</span>% chance""".format(
        skill.chance())
    length_clause = """for <span class="var">{0}</span> seconds.""".format(
        skill.dur())
    
    return " ".join((interval_clause, probability_clause, effect_clause, length_clause, caveat_clause))


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

def lead_skill_fallback_html(skill):
    return """{0} <span class="caveat">(Translated effects are not yet available for this skill.)</span>""".format(escape(skill.explain))
 
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

        effect_clause = """Allows active skill effects to stack, but all appeal values except {0} are reduced by 100% during the live""".format(
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
        return lead_skill_fallback_html(skill)

    predicate_clause = build_lead_skill_predicate(skill)
    if predicate_clause:
        built = " ".join((predicate_clause, effect_clause))
    else:
        built = effect_clause
    return built + "."
