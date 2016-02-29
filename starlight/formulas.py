from .dataloader import *
from datetime import datetime
from pytz import utc, timezone
import re

_JST = timezone("Asia/Tokyo")

# redefined due to nested imports
ark_data_path = functools.partial(os.path.join, "_data", "ark")
dur_def = csvloader.load_keyed_db_file(
    ark_data_path("available_time_type.csv"))
prob_def = csvloader.load_keyed_db_file(ark_data_path("probability_type.csv"))

# reverse engineered from uh, 1.2.0?
def _real_scale_skill_value(max_, min_, lv):
    return (min_ + ((max_ - min_) / 9) * lv) / 100.0


def _scale_skill_value(max_, min_, lv):
    val = _real_scale_skill_value(max_, min_, lv)
    # if the decimal part is too small, just remove it
    if val - int(val) < 0.01:
        return int(val)
    else:
        return val


def skill_chance(typ):
    maxv, minv = prob_def[typ].probability_max, prob_def[typ].probability_min
    return "{0}..{1}".format(_scale_skill_value(maxv, minv, 0),
                             _scale_skill_value(maxv, minv, 9))


def skill_dur(typ):
    maxv, minv = dur_def[typ].available_time_max, dur_def[
        typ].available_time_min
    return "{0}..{1}".format(_scale_skill_value(maxv, minv, 0),
                             _scale_skill_value(maxv, minv, 9))


def JST(date, to_utc=1):
    time = _JST.localize(datetime.strptime(date.replace("-02-29 ", "-03-01 "), "%Y-%m-%d %H:%M:%S"))
    if to_utc:
        return time.astimezone(utc)
    else:
        return time