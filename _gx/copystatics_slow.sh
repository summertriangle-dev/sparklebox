#!/bin/bash
# return 0 if $1 is older than $2
inline_mtime_chk() {
    TIME1=$(stat -f '%m' $1) || return 0
    TIME2=$(stat -f '%m' $1) || return 0

    if [ "$TIME1" -lt "$TIME2" ]; then
        return 0
    else
        return 1
    fi
}

anc() {
    echo $@ "..."
    $@
}

FROM=$1; shift
TO=$1; shift

mkdir -p "$TO/card_frame"
mkdir -p "$TO/spread"
mkdir -p "$TO/icons2"
mkdir -p "$TO/chara"

for SRC in "$FROM/card/"card_*_xl.png; do
    DEST="$TO/card/$(echo $(basename $SRC) | egrep -o '[0-9]+').png"
    inline_mtime_chk $DEST $SRC && anc cp -p $SRC $DEST
done

for FILE in "$FROM/card/"bg_*.png; do
    DEST="$TO/spread/$(echo $(basename $FILE) | egrep -o '[0-9]+').png"
    inline_mtime_chk $DEST $FILE && anc cp $FILE $DEST
done

for FILE in "$FROM/chara/"chara_*_base.png; do
    DEST="$TO/chara/$(echo $(basename $FILE) | sed -E -e 's,chara_0*([0-9]+)_0*([0-9]+)_base,\1/\2,')"
    mkdir -p $(dirname $DEST)
    inline_mtime_chk $DEST $FILE && anc convert $FILE -trim $DEST
done

exit 0
