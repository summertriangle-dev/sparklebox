import os
from time import time as _time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, UnicodeText
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy import func
import multiprocessing
from tornado.ioloop import IOLoop

time = lambda: int(_time())
Base = declarative_base()


class TranslationEntry(Base):
    __tablename__ = "ss_translation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(UnicodeText(collation="utf8_bin"))
    english = Column(UnicodeText(collation="utf8_bin"))
    submitter = Column(String(50))
    submit_utc = Column(Integer)

    def __repr__(self):
        return "<TL entry {x.id} '{x.english}' by {x.submitter} @{x.submit_utc}>".format(x=self)


class TranslationSQL(object):
    def __init__(self, use_satellite):
        self.engine = create_engine(os.getenv("DATABASE_CONNECT"), echo=True)
        self.really_connected = 0
        self.session_nest = []

    def __enter__(self):
        if not self.really_connected:
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

    def all_for_key(self, key):
        with self as s:
            result = s.query(TranslationEntry).filter(TranslationEntry.key == key).order_by(TranslationEntry.submit_utc).all()
        return result

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

    def set_translation(self, key, eng, sender):
        with self as s:
            s.add(TranslationEntry(key=key, english=eng,
                                   submitter=sender, submit_utc=time()))
            s.commit()

# this doesn't work. see TranslationSQL
class TranslationSQLServer(object):
    def __init__(self, use_satellite):
        self.use_satellite = use_satellite
        if use_satellite:
            self.pool = multiprocessing.Pool(1)
        self.sql = TranslationSQL()

    def translate(self, done, *key):
        if self.use_satellite:
            def _finish(result):
                IOLoop.instance().add_callback(lambda: done(result))
            self.pool.apply_async(self.sql.translate, key, callback=_finish)
        else:
            IOLoop.instance().add_callback(lambda: done(self.sql.translate(*key)))

    def set_translation(self, key, eng, sender):
        if self.use_satellite:
            self.pool.apply_async(self.sql.set_translation, key, eng, sender)
        else:
            self.sql.set_translation(key, eng, sender)


class TranslationEngine(TranslationSQL):
    def __init__(self, names_db, use_satellite):
        super().__init__(use_satellite)
        self.k2r = {x.kanji: x.conventional for _, x in names_db.items()}

    def translate_name(self, kanji):
        k = self.k2r.get(kanji, kanji)
        return k
