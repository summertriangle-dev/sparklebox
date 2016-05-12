#!/usr/bin/env python3
# coding: utf-8

# name_finder uses ENAMDICT to split character names.
# It is currently unsure about ~7% of names in the current StarlightStage
# ark (12 Oct 2015.)
# Copyright 2015 The Holy Constituency of the Summer Triangle.
# All rights reserved.

import locale
locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

from collections import namedtuple, Counter
import re
import sys
import csvloader
import csv
import to_roma
import sqlite3
from pprint import pprint

CLASS_FAMILY_NAME = set("sup")
CLASS_GIVEN_NAME = set("mfgu")
AX_PARSE = re.compile(r"/\(([a-z\,]+)\) (.+)/")
FIX_PAT = re.compile(r"([きぎしじずずちぢひびぴみにゆり][ゅょゃ]|[こごそぞとどほぼぽものよろゆ])う")
Word = namedtuple("Word", ["kanji", "kana", "classifier", "roman"])
_Search = namedtuple("Search", ["kanji", "kana", "real_kanji"])

HIRA_FUZZY_COMPARE_TABLE = ["か   き   く   け   こ   ",
                            "が   ぎ   ぐ   げ   ご   ",
                            "さ   し   す   せ   そ   ",
                            "ざ   じ   ず   ぜ   ぞ   ",
                            "た   ち   つ   て   と   ",
                            "だ   ぢ   づ   で   ど   ",
                            "は   ひ   ふ   へ   ほ   ",
                            "ば   び   ぶ   べ   ぼ   ",
                            "は   ひ   ふ   へ   ほ   ",
                            "ぱ   ぴ   ぷ   ぺ   ぽ   "]
KATA_TABLE = set(map(chr, range(0x30A1, 0x3100)))

def make_table(table_in):
    i = iter(table_in)
    for l1, l2 in zip(i, i):
        for v, k in zip(l1, l2):
            yield (k, v)

HIRA_FUZZY_COMPARE_TABLE = {k: v for k, v in make_table(HIRA_FUZZY_COMPARE_TABLE)}

def Search(kanji, kana):
    return _Search(re.compile("".join((kanji[0],) + tuple(x + "?" for x in kanji[1:]))), kana, kanji)

class EnamdictHandle(object):
    def __init__(self, file):
        self.filename = file

    @staticmethod
    def parse_word(line):
        piv = line.index("/")
        assert piv > 0

        content = line[:piv - 1]
        ax = line[piv:]
        if "[" in content:
            kanji, kana = content.split(" ")
            kana = kana[1:-1]
        else:
            kanji = content
            kana = content

        ax_info = AX_PARSE.match(ax)
        if not ax_info:
            return None

        classifier = set(ax_info.group(1).split(","))
        roman = ax_info.group(2)
        return Word(kanji, kana, classifier, roman)

    @staticmethod
    def is_word_matching(word, search, classi):
        t = search.kanji.match(word.kanji)
        if word.classifier & classi and word.kanji in search.real_kanji:
            if word.kana and search.kana[:len(word.kana)] == word.kana:
                return 1
            else:
                return 0
            return 1

    def find_surname_candidates(self, kanji_str, kana_str):
        search = Search(kanji_str, kana_str)
        positive_results = []
        with open(self.filename, "r") as dictionary:
            t = iter(dictionary)
            # discard first line (header line)
            next(t)

            has_seen = 0
            for line in t:
                # make search faster by discarding unwanted result
                if line[0] != kanji_str[0]:
                    if has_seen:
                        break
                    continue
                has_seen = 1
                word = self.parse_word(line.strip())
                if word and self.is_word_matching(word, search, CLASS_FAMILY_NAME):
                    positive_results.append(word)

        # we should filter on exact kana, since we have it anyway
        really_positive_results = []
        for word in positive_results:
            if kana_str[:len(word.kana)] == word.kana:
                really_positive_results.append(word)
        return really_positive_results or positive_results

    def find_given_name_candidates(self, kanji_str, kana_str):
        with open(self.filename, "r") as dictionary:
            t = iter(dictionary)
            # discard first line (header line)
            next(t)

            has_seen = 0
            has_result = 0
            for line in t:
                # make search faster by discarding unwanted result
                if line[0] != kanji_str[0]:
                    if has_seen:
                        break
                    continue
                has_seen = 1
                word = self.parse_word(line.strip())
                if word and kanji_str == word.kanji and (word.kana == kana_str or word.kanji == kana_str):
                    yield word._replace(kana=kana_str)
                    has_result = 1

        if not has_result:
            #print("warning: no given names found! yielding inferred word...")
            yield Word(kanji_str, kana_str, set("i"), "")

    def find_name(self, kanji_str, kana_str):
        possible = []
        for candy in sorted(self.find_surname_candidates(kanji_str, kana_str), key=lambda x: len(x.kanji), reverse=1):
            for given in self.find_given_name_candidates(kanji_str[len(candy.kanji):], kana_str[len(candy.kana):]):
                possible.append((candy, given))

        # if there is a non-inferred given name in there, delete all inferred matches
        # this is so we don't provide guesses when real data is available
        if not all(map(lambda x: "i" in x[1].classifier, possible)):
            return list(filter(lambda x: "i" not in x[1].classifier, possible))
        else:
            return possible

def final_fixups(string):
    return FIX_PAT.sub(lambda match: match.group(1), string)

chara_stub_t = namedtuple("chara_stub_t", ("name", "name_kana"))
def load_from_db(new_db):
    a = sqlite3.connect(new_db)
    c = a.execute("SELECT chara_id, name, name_kana FROM chara_data")
    ret = {}
    for r in c:
        ret[r[0]] = chara_stub_t(*r[1:])
    a.close()
    return ret

if __name__ == '__main__':
    new_db = sys.argv[2]
    name_tab = sys.argv[3]

    charas = load_from_db(new_db)

    try:
        have_names = csvloader.load_keyed_db_file(name_tab)
    except IOError:
        have_names = {}

    missing = set(charas.keys()) - set(have_names.keys())

    f = open(name_tab, "w")
    c = csv.writer(f, delimiter=",", quotechar="\"", quoting=csv.QUOTE_NONNUMERIC, lineterminator="\n")
    c.writerow(("chara_id", "kanji", "kanji_spaced", "kana_spaced", "conventional"))

    for key in sorted(missing):
        chara = charas[key]
        print("---", chara.name, "----------")
        res = EnamdictHandle(sys.argv[1]).find_name(chara.name, chara.name_kana)

        if not res:
            print("warning: No solution found at all")
            res = [(Word(chara.name, chara.name_kana, set(), ""),)]

        try:
            # get rid of u vowel in certain conditions to stay in line with official romanization...
            roma = " ".join(to_roma.consume_hiragana(final_fixups(x.kana)) for x in res[0])
        except ValueError as e:
            print("warning: transliteration failed, possibly due to data consistency issues.")
            print("exception:", e)
            roma = "???"

        for word in res[0]:
            if set(word.kanji) < KATA_TABLE:
                print("warning: string '{0}' contains katakana - romanization will probably be inaccurate"
                    .format(word.kanji))
                roma += "?"

        print("ROMAJI:      ", roma.title())
        print("KANA_SPACED: ", " ".join(x.kana for x in res[0]))
        print("KANJI_SPACED:", " ".join(x.kanji for x in res[0]))

        have_names[key] = (key, chara.name, " ".join(x.kanji for x in res[0]), " ".join(x.kana for x in res[0]), roma.title())

    for key in sorted(have_names.keys()):
        c.writerow(have_names[key])
