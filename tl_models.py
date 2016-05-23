import os
import json
from datetime import datetime
from time import time as _time
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, UnicodeText, LargeBinary
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy import func
import multiprocessing
from tornado.ioloop import IOLoop
from functools import partial

time = lambda: int(_time())
Base = declarative_base()

def retry(n):
    def _wrapper(f):
        def __wrapper(*args, **kwargs):
            for _ in range(n):
                try:
                    return f(*args, **kwargs)
                except OperationalError as e:
                    continue
        return __wrapper
    return _wrapper

def utext():
    # hack
    if os.getenv("DATABASE_CONNECT").startswith("sqlite:"):
        return UnicodeText()
    else:
        return UnicodeText(collation="utf8_bin")

class TranslationEntry(Base):
    __tablename__ = "ss_translation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(utext())
    english = Column(utext())
    submitter = Column(String(50))
    submit_utc = Column(Integer)

    def __repr__(self):
        return "<TL entry {x.id} '{x.english}' by {x.submitter} @{x.submit_utc}>".format(x=self)

class TranslationCache(Base):
    __tablename__ = "ss_translation_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(utext())
    english = Column(utext())

    def __repr__(self):
        return "<TL entry {x.id} '{x.english}'>".format(x=self)

class HistoryEntry(Base):
    __tablename__ = "ss_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(Integer)
    payload = Column(LargeBinary)

    def dt_string(self):
        return self.datetime().strftime("%Y-%m-%d")

    def datetime(self):
        return datetime.fromtimestamp(self.time)

    def asdict(self):
        return json.loads(self.payload.decode("ascii"))

class GachaRewardEntry(Base):
    __tablename__ = "ss_gacha_available_ex"

    gacha_id = Column(Integer, primary_key=True, nullable=False, autoincrement=False)
    step_num = Column(Integer)
    reward_id = Column(Integer, primary_key=True, nullable=False, autoincrement=False)
    recommend_order = Column(Integer)
    limited_flag = Column(Integer, primary_key=True, autoincrement=False)

class GachaPresenceEntry(Base):
    __tablename__ = "ss_gacha_contiguous_presence"

    rowid = Column(Integer, primary_key=True)
    card_id = Column(Integer, nullable=False)
    gacha_id_first = Column(Integer, nullable=False)
    gacha_id_last = Column(Integer, nullable=False)
    avail_start = Column(Integer, nullable=False)
    avail_end = Column(Integer, nullable=False)

class TranslationSQL(object):
    def __init__(self, use_satellite):
        self.really_connected = 0
        self.session_nest = []
        self.history_cache = []
        self.history_is_all_loaded = 0
        self.history_cache_key = None

    def __enter__(self):
        if not self.really_connected:
            self.engine = create_engine(os.getenv("DATABASE_CONNECT"), echo=False,
                connect_args={"ssl": {"dummy": "yes"}})

            try:
                Base.metadata.create_all(self.engine)
            except TypeError:
                self.engine = create_engine(os.getenv("DATABASE_CONNECT"), echo=False)
                Base.metadata.create_all(self.engine)

            self.Session = sessionmaker(self.engine)
            self.really_connected = 1

        self.session_nest.append(self.Session())
        return self.session_nest[-1]

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_value:
            self.session_nest[-1].rollback()
        self.session_nest[-1].close()
        self.session_nest.pop()

    @retry(5)
    def all(self):
        with self as s:
            transient = aliased(TranslationEntry)
            result = s.query(TranslationEntry).filter(
                s.query(func.count(transient.id))
                .filter(transient.submit_utc >= TranslationEntry.submit_utc)
                .filter(transient.key == TranslationEntry.key)
                .order_by(transient.id.desc())
                .correlate(TranslationEntry)
                .as_scalar() == 1).all()
        return result

    @retry(5)
    def all_for_key(self, key):
        with self as s:
            result = s.query(TranslationEntry).filter(TranslationEntry.key == key).order_by(TranslationEntry.submit_utc).all()
        return result

    @retry(5)
    def translate(self, done, *key):
        with self as s:
            result = s.query(TranslationCache).filter(TranslationCache.key.in_(key)).limit(len(key)).all()
        done(result)

    @retry(5)
    def set_translation(self, key, eng, sender):
        with self as s:
            s.add(TranslationEntry(key=key, english=eng,
                                   submitter=sender, submit_utc=time()))
            try:
                thing_to_update = s.query(TranslationCache).filter(TranslationCache.key == key).one()
            except NoResultFound:
                thing_to_update = TranslationCache(key=key, english=eng)
            thing_to_update.english = eng
            s.add(thing_to_update)
            s.commit()

    @retry(5)
    def push_history(self, dt, payload):
        with self as s:
            s.add(HistoryEntry(time=dt, payload=payload))
            s.commit()
        self.history_cache = []

    @retry(5)
    def update_caches(self):
        with self as s:
            transient = aliased(TranslationEntry)
            result = s.query(TranslationEntry).filter(
                s.query(func.count(transient.id))
                .filter(transient.submit_utc >= TranslationEntry.submit_utc)
                .filter(transient.key == TranslationEntry.key)
                .order_by(transient.id.desc())
                .correlate(TranslationEntry)
                .as_scalar() == 1).all()
            s.query(TranslationCache).delete()
            cache_ents = [TranslationCache(key=x.key, english=x.english)
                for x in result if x.key != x.english]
            s.add_all(cache_ents)
            s.commit()

    def get_history(self, nent, key):
        if key != self.history_cache_key:
            self.history_cache = []
            self.history_is_all_loaded = 0
            self.history_cache_key = key

        if self.history_is_all_loaded or (nent and nent <= len(self.history_cache)):
            return self.history_cache[:nent]

        self.history_cache = list(self._get_history(nent))
        if not nent:
            self.history_is_all_loaded = 1
        return self.history_cache

    @retry(5)
    def _get_history(self, nent):
        print("trace _get_history")
        with self as s:
            rows = s.query(HistoryEntry).order_by(HistoryEntry.time.desc())

            if nent:
                rows = rows.limit(nent)
            gv = rows.all()
            yield from gv

class TranslationEngine(TranslationSQL):
    def __init__(self, data_source, use_satellite):
        super().__init__(use_satellite)
        self.dsrc = data_source
        self.k2rid = -1
        self.k2r = {}

    def translate_name(self, kanji):
        if self.k2rid != id(self.dsrc.data.names):
            self.k2r = {x.kanji: x.conventional for _, x in self.dsrc.data.names.items()}

        k = self.k2r.get(kanji, kanji)
        return k
