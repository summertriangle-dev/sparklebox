# coding: utf-8
import re

ROMAJI = r"([aiueo]|(?:(?:[kgsztdhbpmnyrfj]{1,2})|sh|ts|dz|ny|jy)(?:[aiueo])|n(?:n)?)"
TL_A = ("a   i   u   e   o   "
        "ka  ki  ku  ke  ko  "
        "ga  gi  gu  ge  go  "
        "sa  shi si  su  se  so  "
        "za  zu  ze  zo  "
        "ta  chi ti  tsu tu  te  to  "
        "da  di  de  do  "
        "ha  hi  fu  hu  he  ho  "
        "ba  bi  bu  be  bo  "
        "pa  pi  pu  pe  po  "
        "ma  mi  mu  me  mo  "
        "na  ni  nu  ne  no  "
        "ya  yu  yo          "
        "ra  ri  ru  re  ro  "
        "wa  wo  ")
TL_B = ("あ   い   う   え   お   "
        "か   き   く   け   こ   "
        "が   ぎ   ぐ   げ   ご   "
        "さ   し   し   す   せ   そ   "
        "ざ   ず   ぜ   ぞ   "
        "た   ち   ち   つ   つ   て   と   "
        "だ   ぢ   で   ど   "
        "は   ひ   ふ   ふ   へ   ほ   "
        "ば   び   ぶ   べ   ぼ   "
        "ぱ   ぴ   ぷ   ぺ   ぽ   "
        "ま   み   む   め   も   "
        "な   に   ぬ   ね   の   "
        "や   ゆ   よ           "
        "ら   り   る   れ   ろ   "
        "わ   を   ")

TL_EXT_A = ("zu  dzu du   "
            "sya syu syo sha shu sho  "
            "kya kyu kyo "
            "ja  jya ju  jyu jo  jyo ji   "
            "nya nyu nyo n    "
            "mya myu myo "
            "rya ryu ryo ")
TL_EXT_B = ("づ   づ   づ    "
            "しゃ  しゅ  しょ  しゃ  しゅ  しょ   "
            "きゃ  きゅ  きょ  "
            "じゃ  じゃ  じゅ  じゅ  じょ  じょ  じ    "
            "にゃ  にゅ  にょ  ん    "
            "みゃ  みゅ  みょ  "
            "りゃ  りゅ  りょ  ")
SMALL_LETTERS = "ぁぃぅぇぉゃゅょゎゕゖー"

def get_run(table, ind):
    ret = []
    while table[ind] != " ":
        ret.append(table[ind])
        ind += 1
    return "".join(ret)

def lookup_letter_group(letter_group, tables=((TL_A, TL_B), (TL_EXT_A, TL_EXT_B))):
    # special case for extended consonants (e.g. "gakkou")
    if len(letter_group) == 3 and letter_group[0] == letter_group[1]:
        try:
            char = lookup_letter_group(letter_group[1:], ((TL_A, TL_B),))
        except ValueError:
            # raise the correct error message
            raise ValueError("A transliteration for the letter group '{0}' was not found.".format(letter_group))
        else:
            return "っ" + char

    for en_tbl, ja_tbl in tables:
        try:
            return get_run(ja_tbl, en_tbl.index(letter_group + " "))
        except ValueError:
            continue
    else:
        raise ValueError("A transliteration for the letter group '{0}' was not found.".format(letter_group))

def lookup_letter_group2(letter_group, tables=((TL_B, TL_A), (TL_EXT_B, TL_EXT_A))):
    # special case for extended consonants (e.g. "gakkou")
    if letter_group.startswith("っ"):
        try:
            char = lookup_letter_group2(letter_group[1:], ((TL_B, TL_A),))
        except ValueError:
            # raise the correct error message
            raise ValueError("A transliteration for the letter group '{0}' was not found.".format(letter_group))
        else:
            return char[0] + char
    # for extended vowel too
    if letter_group.endswith("ー"):
        try:
            char = lookup_letter_group2(letter_group[:-1], ((TL_B, TL_A),))
        except ValueError:
            # raise the correct error message
            raise ValueError("A transliteration for the letter group '{0}' was not found.".format(letter_group))
        else:
            return char + char[-1]

    for en_tbl, ja_tbl in tables:
        try:
            return get_run(ja_tbl, en_tbl.index(letter_group + " "))
        except ValueError:
            continue
    else:
        raise ValueError("A transliteration for the letter group '{0}' was not found.".format(letter_group))

def consume_romaji(string):
    letter_groups = re.findall(ROMAJI, string)
    return "".join(( map(lambda x: lookup_letter_group(x.strip()), filter(bool, letter_groups)) ))

def _consume_hiragana(string):
    groups = []
    mygroup = []
    for char in string:
        if char not in SMALL_LETTERS and mygroup != ["っ"]:
            if mygroup:
                yield "".join(mygroup)
            mygroup = [char]
        else:
            mygroup.append(char)
    if mygroup:
        yield "".join(mygroup)
def consume_hiragana(string):
    return "".join(( map(lambda x: lookup_letter_group2(x.strip()), _consume_hiragana(string)) ))
