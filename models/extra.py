from collections import namedtuple

HISTORY_TYPE_EVENT = 2
HISTORY_TYPE_GACHA = 3
HISTORY_TYPE_ADD_N = 4
HISTORY_TYPE_EVENT_END = 5
HISTORY_TYPE_GACHA_END = 6

EVENT_TYPE_TOKEN = 0
EVENT_TYPE_CARAVAN = 1
EVENT_TYPE_GROOVE = 2
EVENT_TYPE_PARTY = 3
EVENT_TYPE_TOUR = 4

EVENT_ATTR_NONE = 0
EVENT_ATTR_CU = 1
EVENT_ATTR_CO = 2
EVENT_ATTR_PA = 3

EVENT_STAT_NONE = 0
EVENT_STAT_VO = 1
EVENT_STAT_VI = 2
EVENT_STAT_DA = 3

unknown_gacha_t = namedtuple("unknown_gacha_t", ("name"))
Gap = namedtuple("Gap", ("start", "end"))

class Availability(object):
    """mutable class so we can meld stuff"""
    _TYPE_GACHA = 1
    _TYPE_EVENT = 2

    def __init__(self, type, name, start, end, gaps, limited):
        self.type = type
        self.name = name
        self.start = start
        self.end = end
        self.gaps = gaps
        self.limited = limited

    def __repr__(self):
        return "models.Availability({0})".format(
            ", ".join(repr(getattr(self, x)) for x in ["type", "name", "start", "end", "gaps"])
        )

def combine_availability(l):
    """Take a list of discrete Availability and turn any small lapses <= 3 days
       into a Gap on the parent object.
       Returns in place because of gacha_availability()"""
    if not l:
        return

    new_list = []
    prev = l[0]
    for availability in l[1:]:
        bet = availability.start - prev.end
        # max 3 day gap, and both descriptions must be limited/non-limited
        if bet.seconds > 0 and bet.days <= 3 and prev.limited == availability.limited:
            # prev.gaps.append(Gap(prev.end, availability.start))
            prev.end = availability.end
        else:
            new_list.append(prev)
            prev = availability
    new_list.append(prev)
    l[:] = new_list
