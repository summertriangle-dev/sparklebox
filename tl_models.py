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
        def __wrapper(*args):
            for _ in range(n):
                try:
                    return f(*args)
                except OperationalError as e:
                    if "lost connection" in str(e).lower():
                        continue
                    else:
                        raise
        return __wrapper
    return _wrapper

class TranslationEntry(Base):
    __tablename__ = "ss_translation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(UnicodeText(collation="utf8_bin"))
    english = Column(UnicodeText(collation="utf8_bin"))
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
            pl = json.dumps(payload).encode("utf8")
            s.add(HistoryEntry(time=dt, payload=pl))
            s.commit()

    @retry(5)
    def get_history(self, nent):
        with self as s:
            rows = s.query(HistoryEntry).order_by(HistoryEntry.time.desc())

            if nent:
                rows = rows.limit(nent)
        yield from rows.all()

class TranslationEngine(TranslationSQL):
    def __init__(self, names_db, use_satellite):
        super().__init__(use_satellite)
        self.k2r = {x.kanji: x.conventional for _, x in names_db.items()}

    def translate_name(self, kanji):
        k = self.k2r.get(kanji, kanji)
        return k
