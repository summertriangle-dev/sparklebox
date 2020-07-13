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

    15, "Concentration",
    16, "Encore",

    17, "Healer",
    18, "Healer",
    19, "Healer",

    20, "Skill Boost",

    21, "Cute Focus",
    22, "Cool Focus",
    23, "Passion Focus",

    24, "All-Round",
    25, "Life Sparkle",
    26, "Tricolor Synergy",
    27, "Coordinate",
    28, "Perfect Score Bonus",
    29, "Perfect Score Bonus",
    30, "Perfect Score Bonus",
    31, "Tuning",

    32, "Cute Ensemble",
    33, "Cool Ensemble",
    34, "Passion Ensemble",

    35, "Vocal Motif",
    36, "Dance Motif",
    37, "Visual Motif",

    38, "Tricolor Symphony",
    39, "Alternate",
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
    1, "scoreup",
    2, "scoreup",
    3, "scoreup",

    4, "cboost",

    5, "plock",
    6, "plock",
    7, "plock",
    8, "plock",

    9, "cguard",
    10, "cguard",
    11, "cguard",

    12, "hguard",
    13, "heal",
    14, "overload",

    15, "concentrate",
    16, "encore",

    17, "heal",
    18, "heal",
    19, "heal",

    20, "skillboost",

    21, "focus",
    22, "focus",
    23, "focus",

    24, "allround",
    25, "sparkle",
    26, "synergy",
    27, "focus_flat",
    28, "psb_hold",
    29, "psb_flick",
    30, "psb_slide",
    31, "tuning",

    32, "skillboost",
    33, "skillboost",
    34, "skillboost",
    35, "motif",
    36, "motif",
    37, "motif",

    38, "symphony",
    39, "alternate",
])

stat_dot = enum([
    1, "visual",
    2, "dance",
    3, "vocal",
    4, "balance",
    5, "balance",
    6, "balance",
    7, "balance",
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
