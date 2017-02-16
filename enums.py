import models

def enum(kv):
    i = iter(kv)
    dic = dict(zip(i, i))
    rev = {v: k for k, v in dic.items()}

    def f(key):
        return dic.get(key, "<missing string: {0}>".format(key))
    def _reverse_enum(val):
        return rev[val]
    f.value_for_description = _reverse_enum
    return f

rarity = enum([
    1, "Normal",
    2, "Normal+",
    3, "Rare",
    4, "Rare+",
    5, "SR",
    6, "SR+",
    7, "SSR",
    8, "SSR+",
])

attribute = enum([
    1, "Cute",
    2, "Cool",
    3, "Passion",
    4, "Office",
])

skill_type = enum([
    1, "Perfect Score Bonus",
    2, "Score Bonus",
    3, "Score Bonus",

    4, "Combo Bonus",

    5, "Lesser Perfect Lock",
    6, "Greater Perfect Lock",
    7, "Extreme Perfect Lock",
    8, "Unconditional Perfect Lock",

    9, "Combo Guard",
    10, "Greater Combo Guard",
    11, "Unconditional Combo Guard",

    12, "Life Guard",
    13, "Unconditional Healer",
    14, "Overload",

    17, "Healer",
    18, "Healer",
    19, "Healer",

    24, "Combo Bonus/Heal"
])

skill_probability = enum([
    2, "small",
    3, "fair",
    4, "high",
])

skill_length_type = enum([
    3, "short",
    4, "medium",
    5, "long",
])

lskill_target = enum([
    1, "all Cute",
    2, "all Cool",
    3, "all Passion",
    4, "all",
])

lskill_effective_target = enum([
    1, "ca_cute",
    2, "ca_cool",
    3, "ca_passion",
    4, "ca_all",
])

lskill_param = enum([
    1, "the Vocal appeal",
    2, "the Visual appeal",
    3, "the Dance appeal",
    4, "all appeals",
    5, "the life",
    6, "the skill probability",
])

lskill_effective_param = enum([
    1, "ce_vocal",
    2, "ce_visual",
    3, "ce_dance",
    4, "ce_anyappeal",
    5, "ce_life",
    6, "ce_skill",
])

api_char_type = enum([
    1, "cute",
    2, "cool",
    3, "passion",
    4, "office"
])

lskill_target_attr = enum([
    1, "cute",
    2, "cool",
    3, "passion",
    4, "all",
])

lskill_target_param = enum([
    1, "vocal",
    2, "visual",
    3, "dance",
    4, "all",
    5, "life",
    6, "skill_probability",
])

skill_class = enum([
    1, "s_scorebonus",
    2, "s_scorebonus",
    3, "s_scorebonus",

    4, "s_combobonus",

    5, "s_pl",
    6, "s_pl",
    7, "s_pl",
    8, "s_pl",

    9, "s_cprot",
    10, "s_cprot",
    11, "s_cprot",

    12, "s_life",
    13, "s_heal",
    14, "s_overload",

    17, "s_heal",
    18, "s_heal",
    19, "s_heal",

    24, "s_allround",
])

stat_dot = enum([
    1, "m_vi",
    2, "m_da",
    3, "m_vo",
    4, "m_ba",
    5, "m_ba",
    6, "m_ba",
    7, "m_ba",
])

stat_en = enum([
    1, "This card's highest stat is Visual",
    2, "This card's highest stat is Dance",
    3, "This card's highest stat is Vocal",
    4, "This card's stats are mostly balanced",
    5, "This card's stats are mostly balanced (Visual high)",
    6, "This card's stats are mostly balanced (Dance high)",
    7, "This card's stats are mostly balanced (Vocal high)"
])

floor_rarity = enum([
    1, "n",
    2, "n",
    3, "r",
    4, "r",
    5, "sr",
    6, "sr",
    7, "ssr",
    8, "ssr",
])

he_event_class = enum([
    models.EVENT_TYPE_TOKEN, "hev_token",
    models.EVENT_TYPE_CARAVAN, "hev_caravan",
    models.EVENT_TYPE_GROOVE, "hev_groove",
    models.EVENT_TYPE_PARTY, "hev_party",
    models.EVENT_TYPE_TOUR, "hev_tour",
])

# TODO need enum defs for
# constellation
# blood_type
# hand
# personality
# home_town
