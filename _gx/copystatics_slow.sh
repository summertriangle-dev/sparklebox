#!/bin/bash
# test if $1 older than $2
inline_mtime_chk() {
    return $(python3 - $@ <<EOF
import os
import sys
try:
    sys.exit(0 if os.path.getmtime(sys.argv[1]) < os.path.getmtime(sys.argv[2]) else 1)
except:
    sys.exit(0)
EOF
    )
}

anc() {
    #echo $@ "..."
    $@
}

FROM=$1; shift
TO=$1; shift

mkdir -p "$TO/card_frame"
mkdir -p "$TO/spread"
mkdir -p "$TO/icon"
mkdir -p "$TO/chara"

for SRC in "$FROM/card/"card_*_xl.png; do
    DEST="$TO/card/$(echo $(basename $SRC) | egrep -o '[0-9]+').png"
    inline_mtime_chk $DEST $SRC && anc cp -p $SRC $DEST
done

for FILE in "$FROM/card/"bg_*.png; do
    DEST="$TO/spread/$(echo $(basename $FILE) | egrep -o '[0-9]+').png"
    inline_mtime_chk $DEST $FILE && anc cp $FILE $DEST
done

for FILE in "$FROM/cardsm/"card_*_s.png; do
    DEST="$TO/icon/$(echo $(basename $FILE) | egrep -o '[0-9]+').png"
    inline_mtime_chk $DEST $FILE && anc convert $FILE -resize 48x48 $DEST
done

for FILE in "$FROM/chara/"chara_*_base.png; do
    DEST="$TO/chara/$(echo $(basename $FILE) | sed -E -e 's,chara_0*([0-9]+)_0*([0-9]+)_base,\1/\2,')"
    mkdir -p $(dirname $DEST)
    inline_mtime_chk $DEST $FILE && anc convert $FILE -trim $DEST
done
