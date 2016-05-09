import os
import json
from datetime import datetime
from time import time as _time
from sqlalchemy.exc import OperationalError
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


class TranslationSQL(object):
    def __init__(self, use_satellite):
        self.really_connected = 0
        self.session_nest = []

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
            transient = aliased(TranslationEntry)
            result = s.query(TranslationEntry).filter(
                s.query(func.count(transient.id))
                .filter(transient.submit_utc >= TranslationEntry.submit_utc)
                .filter(transient.key == TranslationEntry.key)
                .order_by(transient.id.desc())
                .correlate(TranslationEntry)
                .as_scalar() == 1).filter(TranslationEntry.key.in_(key)).all()
        done(result)

    @retry(5)
    def set_translation(self, key, eng, sender):
        with self as s:
            s.add(TranslationEntry(key=key, english=eng,
                                   submitter=sender, submit_utc=time()))
            s.commit()

    @retry(5)
    def push_history(self, dt, payload):
        with self as s:
            s.add(HistoryEntry(time=dt, payload=payload))
            s.commit()

    @retry(5)
    def get_history(self, nent):
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
