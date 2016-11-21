from . import en

def char_voices(va_data_t, id):
    # title call entry
    # use type -4 so it doesn't take the string of USE_TYPE__T_4.
    # in endpoints.audio this gets converted back to a positive int.
    yield va_data_t(id, 4, 13, 1, "アイドルマスター シンデレラガールズ スターライトステージ!", 414)
    # live end; fail
    yield va_data_t(id, 2, 1, 1, en.NO_STRING_FMT.format(id, 2, 1), 21)
    # live end; full combo
    yield va_data_t(id, 2, 2, 1, en.NO_STRING_FMT.format(id, 2, 2), 22)
    # live end; score rank S->D
    yield va_data_t(id, 2,  3, 1, en.NO_STRING_FMT.format(id, 2,  3),  23)
    yield va_data_t(id, 2,  4, 1, en.NO_STRING_FMT.format(id, 2,  4),  24)
    yield va_data_t(id, 2,  5, 1, en.NO_STRING_FMT.format(id, 2,  5),  25)
    yield va_data_t(id, 2,  6, 1, en.NO_STRING_FMT.format(id, 2,  6),  26)
    yield va_data_t(id, 2,  7, 1, en.NO_STRING_FMT.format(id, 2,  7),  27)
    # producer lv up
    yield va_data_t(id, 2,  8, 1, en.NO_STRING_FMT.format(id, 2,  8),  28)
    # name
    yield va_data_t(id, 4,  1, 1, en.NO_STRING_FMT.format(id, 4,  1),  41)
    yield va_data_t(id, 4,  2, 1, en.NO_STRING_FMT.format(id, 4,  2),  41)
    # saying "producer"
    yield va_data_t(id, 4,  3, 1, en.NO_STRING_FMT.format(id, 4,  3),  43)
    # on lesson
    yield va_data_t(id, 4,  4, 1, en.NO_STRING_FMT.format(id, 4,  4),  44)
    # on star lesson
    yield va_data_t(id, 4,  5, 1, en.NO_STRING_FMT.format(id, 4,  5),  45)
    # generic success?
    yield va_data_t(id, 4,  6, 1, en.NO_STRING_FMT.format(id, 4,  6),  46)
    yield va_data_t(id, 4,  7, 1, en.NO_STRING_FMT.format(id, 4,  7),  46)
    yield va_data_t(id, 4,  8, 1, en.NO_STRING_FMT.format(id, 4,  8),  46)
    # generic failure?
    yield va_data_t(id, 4,  9, 1, en.NO_STRING_FMT.format(id, 4,  9),  49)
    yield va_data_t(id, 4, 10, 1, en.NO_STRING_FMT.format(id, 4, 10),  49)
    yield va_data_t(id, 4, 11, 1, en.NO_STRING_FMT.format(id, 4, 11),  49)

def card_voices(va_data_t, id, chain_id):
    if id == chain_id:
        # live start
        yield va_data_t(id, 6, 1, 1, en.NO_STRING_FMT.format(id, 6, 1), 61)
        yield va_data_t(id, 6, 2, 1, en.NO_STRING_FMT.format(id, 6, 2), 61)

        # live skill proc
        yield va_data_t(id, 6, 3, 1, en.NO_STRING_FMT.format(id, 6, 3), 62)
        yield va_data_t(id, 6, 4, 1, en.NO_STRING_FMT.format(id, 6, 4), 62)
        yield va_data_t(id, 6, 5, 1, en.NO_STRING_FMT.format(id, 6, 5), 62)

        # live end
        yield va_data_t(id, 6, 6, 1, en.NO_STRING_FMT.format(id, 6, 6), 63)
        yield va_data_t(id, 6, 7, 1, en.NO_STRING_FMT.format(id, 6, 7), 63)