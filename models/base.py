import os
import json
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, UnicodeText, LargeBinary, SmallInteger

def utext():
    # hack
    if not os.getenv("DATABASE_CONNECT").startswith("mysql"):
        return UnicodeText()
    else:
        return UnicodeText(collation="utf8_bin")

TABLE_PREFIX = os.getenv("TLE_TABLE_PREFIX", None)
if TABLE_PREFIX is None:
    print("Warning: env variable TLE_TABLE_PREFIX unset. Defaulting to 'ss'. "
        "(Set TLE_TABLE_PREFIX to silence this warning.)")
    TABLE_PREFIX = "ss"

Base = declarative_base()

class TranslationEntry(Base):
    __tablename__ = TABLE_PREFIX + "_translation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(utext())
    english = Column(utext())
    submitter = Column(String(50))
    submit_utc = Column(Integer)

    def __repr__(self):
        return "<TL entry {x.id} '{x.english}' by {x.submitter} @{x.submit_utc}>".format(x=self)

class TranslationCache(Base):
    __tablename__ = TABLE_PREFIX + "_translation_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(utext(), index=True)
    english = Column(utext())

    def __repr__(self):
        return "<TL entry {x.id} '{x.english}'>".format(x=self)

class GachaRewardEntry(Base):
    __tablename__ = TABLE_PREFIX + "_gacha_available_ex"

    gacha_id = Column(Integer, primary_key=True, nullable=False, autoincrement=False)
    step_num = Column(Integer)
    reward_id = Column(Integer, primary_key=True, nullable=False, autoincrement=False)
    recommend_order = Column(Integer)
    limited_flag = Column(Integer, primary_key=True, autoincrement=False)

class GachaPresenceEntry(Base):
    __tablename__ = TABLE_PREFIX + "_gacha_contiguous_presence"

    rowid = Column(Integer, primary_key=True)
    card_id = Column(Integer, nullable=False)
    gacha_id_first = Column(Integer, nullable=False)
    gacha_id_last = Column(Integer, nullable=False)
    avail_start = Column(Integer, nullable=False)
    avail_end = Column(Integer, nullable=False)

class HistoryEventEntry(Base):
    __tablename__ = TABLE_PREFIX + "_history_ex"

    # event type/id
    descriptor = Column(Integer, primary_key=True)
    extra_type_info = Column(SmallInteger)
    # card ids added, as a comma separated list
    added_cards = Column(utext())
    event_name = Column(utext())

    start_time = Column(Integer)
    end_time = Column(Integer)

    # the top 4 bits of .descriptor denote the type of history
    # event, the others are for the underlying event id, gacha id,
    # etc.

    def type(self):
        return (self.descriptor & 0xF0000000) >> 28

    # gacha id, event id, etc
    def referred_id(self):
        return self.descriptor & 0x0FFFFFFF

    def ensure_parsed_changelist(self):
        if not hasattr(self, "parsed_changelist"):
            if self.added_cards:
                self.parsed_changelist = json.loads(self.added_cards)
            else:
                self.parsed_changelist = {}

        return self.parsed_changelist

    def category_card_list(self, cat):
        return self.ensure_parsed_changelist().get(cat, [])

    def card_list(self):
        cl = self.ensure_parsed_changelist()

        ret = []
        for k in sorted(cl.keys()):
            ret.extend(cl[k])

        return ret

    def card_list_has_more_than_one_category(self):
        return len(self.ensure_parsed_changelist()) > 1

    def card_urlspec(self):
        return ",".join( map(str, self.card_list()) )

    def start_dt_string(self):
        return self.start_datetime().strftime("%Y-%m-%d")

    def end_dt_string(self):
        return self.end_datetime().strftime("%Y-%m-%d")

    def start_datetime(self):
        return datetime.fromtimestamp(self.start_time)

    def end_datetime(self):
        return datetime.fromtimestamp(self.end_time)

    def length_in_days(self):
        secs = (self.end_time - self.start_time)
        return secs / (60 * 60 * 24)

    # -- extra_type_info bitfields for events:
    # (these are binary digits, not hex)
    #      SSAA0000 TTTTTTTT
    # SS: Focus stat (for grooves), 0-4
    # AA: Attribute (for tokens), 0-4
    # TTT: Event type, 0-7

    def event_type(self):
        return self.extra_type_info & 0xFF

    # don't use these for now
    # def event_attribute(self):
    #     return (self.extra_type_info & 0x18) >> 3
    #
    # def groove_stat(self):
    #     return (self.extra_type_info & 0x60) >> 5

    # -- extra_type_info bitfields for gachas:
    # (these are binary digits, not hex)
    #      00000000 0000000L
    # L: limited?, 0-1

    def gacha_is_limited(self):
        return self.extra_type_info & 0x1
