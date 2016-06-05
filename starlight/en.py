import csvloader
import functools
import os
import enums
import re

NO_STRING_FMT = "<Voice ID {0}:6:{1} has no transcript, but you can still submit a translation for it.>"

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
    1: """all Perfect notes will receive a <span class="let">{0}</span>% score bonus""",
    2: """all Great and Perfect notes will receive a <span class="let">{0}</span>% score bonus""",
    4: """you will gain an extra <span class="let">{0}</span>% combo bonus""",
    5: """all Great notes will become Perfect notes""",
    6: """all Great and Nice notes will become Perfect notes""",
    7: """all Great, Nice, and Bad notes will become Perfect notes""",
    9: """Nice notes will not break combo""",
    12: """you will not lose health""",
    14: """<span class="let">{1}</span> life will be consumed, then: Perfect notes receive a <span class="let">{0}</span>% score bonus, and Nice/Bad notes will not break combo""",
    17: """all Perfect notes will restore <span class="let">{0}</span> health""" }

REMOVE_HTML = re.compile(r"</?span[^>]*>")

def describe_skill(skill):
    return REMOVE_HTML.sub("", describe_skill_html(skill))

def describe_lead_skill(lskill):
    return REMOVE_HTML.sub("", describe_lead_skill_html(lskill))

def describe_skill_html(skill):
    fire_interval = skill.condition
    effect_val = skill.value
    # TODO symbols
    if skill.skill_type in [1, 2, 4, 14]:
        effect_val -= 100

    effect_clause = SKILL_DESCRIPTIONS.get(
        skill.skill_type, "").format(effect_val, skill.skill_trigger_value)
    interval_clause = """Every <span class="let">{0}</span> seconds:""".format(
        fire_interval)
    probability_clause = """there is a <span class="var">{0}</span>% chance that""".format(
        skill.chance())
    length_clause = """for <span class="var">{0}</span> seconds.""".format(
        skill.dur())

    return " ".join((interval_clause, probability_clause, effect_clause, length_clause))


def describe_lead_skill_html(skill):
    assert skill.up_type == 1 and skill.type == 20

    target_attr = enums.lskill_target(skill.target_attribute)
    target_param = enums.lskill_param(skill.target_param)

    built = """Raises {0} of {1} members by <span class="let">{2}</span>%.""".format(
        target_param, target_attr, skill.up_value)
    return built
