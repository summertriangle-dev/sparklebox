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
    12: """that you will not lose health""",
    13: """that all notes will restore <span class="let">{0}</span> health""", #provisional
    14: """that <span class="let">{1}</span> life will be consumed, then: Perfect notes receive a <span class="let">{0}</span>% score bonus, and Nice/Bad notes will not break combo""",
    15: """that Perfect notes will receive a <span class="let">{0}</span>% score bonus, but become harder to hit""", #provisional
    16: """to activate the previous skill again""",
    17: """that Perfect notes will restore <span class="let">{0}</span> health""",
    18: """that Great/Perfect notes will restore <span class="let">{0}</span> health""", #provisional
    19: """that Nice/Great/Perfect notes will restore <span class="let">{0}</span> health""", #provisional
    20: """that currently active skills will be boosted""",
    21: """that with only Cute idols on the team, Perfect notes will receive a <span class="let">{0}</span>% score bonus, and you will gain an extra <span class="let">{2}</span>% combo bonus""",
    22: """that with only Cool idols on the team, Perfect notes will receive a <span class="let">{0}</span>% score bonus, and you will gain an extra <span class="let">{2}</span>% combo bonus""",
    23: """that with only Passion idols on the team, Perfect notes will receive a <span class="let">{0}</span>% score bonus, and you will gain an extra <span class="let">{2}</span>% combo bonus""",
    24: """that you will gain an extra <span class="let">{0}</span>% combo bonus, and Perfect notes will restore <span class="let">{2}</span> health""",
    25: """that you will gain an extra combo bonus based on your current health""",
    26: """that with all three types of idols on the team, you will gain an extra <span class="let">{2}</span>% combo bonus, and Perfect notes will receive a <span class="let">{0}</span>% score bonus plus restore <span class="let">{3}</span> HP,""",
    27: """that Perfect notes will receive a <span class="let">{0}</span>% score bonus, and you will gain an extra <span class="let">{2}</span>% combo bonus""",
    28: """that Perfect notes will receive a <span class="let">{0}</span>% score bonus, and hold notes a <span class="let">{2}</span>% score bonus""",
    29: """that Perfect notes will receive a <span class="let">{0}</span>% score bonus, and flick notes a <span class="let">{2}</span>% score bonus""",
    31: """that you will gain an extra <span class="let">{0}</span>% combo bonus, and Nice/Great notes will become Perfect notes""",
}

SKILL_TYPES_WITH_PERCENTAGE_EFF_VAL1 = [1, 2, 3, 4, 14, 15, 21, 22, 23, 24, 26, 27, 28, 29, 31]
SKILL_TYPES_WITH_PERCENTAGE_EFF_VAL2 = [21, 22, 23, 26, 27, 28, 29]

REMOVE_HTML = re.compile(r"</?span[^>]*>")

def describe_skill(skill):
    return REMOVE_HTML.sub("", describe_skill_html(skill))

def describe_lead_skill(lskill):
    return REMOVE_HTML.sub("", describe_lead_skill_html(lskill))

def describe_skill_html(skill):
    if skill is None:
        return "No effect"

    fire_interval = skill.condition
    effect_val = skill.value
    # TODO symbols
    if skill.skill_type in SKILL_TYPES_WITH_PERCENTAGE_EFF_VAL1:
        effect_val -= 100
    elif skill.skill_type in [20]:
        effect_val = (effect_val//10) - 100

    value_2 = skill.value_2
    if skill.skill_type in SKILL_TYPES_WITH_PERCENTAGE_EFF_VAL2:
        value_2 -= 100
    value_3 = skill.value_3

    effect_clause = SKILL_DESCRIPTIONS.get(
        skill.skill_type, "").format(effect_val, skill.skill_trigger_value, value_2, value_3)
    interval_clause = """Every <span class="let">{0}</span> seconds:""".format(
        fire_interval)
    probability_clause = """there is a <span class="var">{0}</span>% chance""".format(
        skill.chance())
    length_clause = """for <span class="var">{0}</span> seconds.""".format(
        skill.dur())

    return " ".join((interval_clause, probability_clause, effect_clause, length_clause))


LEADER_SKILL_TARGET = {
    1: "all Cute",
    2: "all Cool",
    3: "all Passion",
    4: "all",
}

LEADER_SKILL_PARAM = {
    1: "the Vocal appeal",
    2: "the Visual appeal",
    3: "the Dance appeal",
    4: "all appeals",
    5: "the life",
    6: "the skill probability",
}

def build_lead_skill_predicate(skill):
    need_list = []
    if skill.need_cute:
        need_list.append("Cute")
    if skill.need_cool:
        need_list.append("Cool")
    if skill.need_passion:
        need_list.append("Passion")

    if not need_list:
        return None

    if len(need_list) == 1:
        need_str = need_list[0]
    else:
        need_str = ", ".join(need_list[:-1])
        need_str = "{0}, and {1}".format(need_str, need_list[-1])

    # FIXME: consider values of need_x in leader_skill_t
    #   Rei_Fan49 - Today at 5:36 PM
    #   princess and focus only works for single color
    #   it requires 5 or 6 per color
    #   which implies monocolor team or no activation
    #   cinfest team requires 1 each color (according to internal data)
    if len(need_list) < 3:
        need_str = "only " + need_str

    predicate_clause = """when there are {0} idols on the team.""".format(need_str)
    return predicate_clause

def describe_lead_skill_html(skill):
    if skill is None:
        return "No effect"

    if skill.up_type == 1 and skill.type == 20:
        target_attr = LEADER_SKILL_TARGET.get(skill.target_attribute, "<unknown>")
        target_param = LEADER_SKILL_PARAM.get(skill.target_param, "<unknown>")

        effect_clause = """Raises {0} of {1} members by <span class="let">{2}</span>%""".format(
            target_param, target_attr, skill.up_value)

        predicate_clause = build_lead_skill_predicate(skill)
        if predicate_clause:
            built = " ".join((effect_clause, predicate_clause))
        else:
            built = effect_clause + "."
        return built
    elif skill.up_type == 1 and skill.type == 30:
        effect_clause = "Gives extra rewards when you finish a live"

        predicate_clause = build_lead_skill_predicate(skill)
        if predicate_clause:
            built = " ".join((effect_clause, predicate_clause))
        else:
            built = effect_clause + "."
        return built
    elif skill.up_type == 1 and skill.type == 40:
        effect_clause = "Increases fan gain by <span class=\"let\">{0}</span>% when you finish a live".format(
            skill.up_value)

        predicate_clause = build_lead_skill_predicate(skill)
        if predicate_clause:
            built = " ".join((effect_clause, predicate_clause))
        else:
            built = effect_clause + "."
        return built
    else:
        return """I don't know how to describe this leader skill. This is a bug, please report it. (up_type: {0}, type: {1})""".format(
            skill.up_type, skill.type
        )
