#!/bin/bash

shopt -s nullglob
set -e
OUTPUT=$(realpath "$1"); shift
STA=$(realpath "$1"); shift

SCRIPT_PATH=`dirname "$0"`; SCRIPT_PATH=`eval "cd \"$SCRIPT_PATH\" && pwd"`

# I need the following executables in this directory.
# Not included in the repo, but you will find them close by.
LZ4ER="$SCRIPT_PATH/lz4er"
DISUNITY="$SCRIPT_PATH/disunity.jar"
AHFF2PNG="$SCRIPT_PATH/ahff2png"

UNACB="$SCRIPT_PATH/un_acb.exe"
HCA_DECODER="$SCRIPT_PATH/hca_decoder"
FFMPEG_OPTIONS="-i /dev/stdin"

py_mangle_fn() {
    python3 - $1 <<EOF
def audio(object_id, use, index, *_):
    a = (object_id << 40) | ((use & 0xFF) << 24) | ((index & 0xFF) << 16) | 0x11AB
    # make everything 8 bytes long for reasons
    a &= 0xFFFFFFFFFFFFFFFF
    a ^= 0x1042FC1040200700
    basename = hex(a)[2:]
    print(basename)

import re
import sys
args = [int(x) for x in re.findall("0*[0-9]+", sys.argv[1])]
audio(*args)
EOF
}

acb_extract() {
    local OUTPUT=$1; shift
    local FILE=$1; shift
    local TMPD=$(mktemp -d -t "reeeeee")

    echo "[-] unacb $FILE."
    mono $UNACB $FILE $TMPD false

    echo $TMPD

    if [[ -z "$TMPD/"*.hca ]]; then
        echo "[-] The file didn't yield any ahff files to process."
    else
        WHERE=$(pwd)
        cd $TMPD # this is a work around for hca_decoder not accepting paths with slashes in them.
        for HCA in *.hca; do
            echo "[-] Converting $HCA to mp3."
            local FN="$OUTPUT/$(basename $HCA).mp3"
            $HCA_DECODER $HCA -o /dev/stdout | ffmpeg $FFMPEG_OPTIONS $FN >> /dev/null 2>&1 || true

            case $(basename "$FN") in
            voice_*.mp3)
                local F=$(py_mangle_fn $(basename "$FN"))
                cp $FN "$STA/va2/$F.mp3"
                ;;
            esac
        done
        cd $WHERE
    fi

    rm -rf $TMPD
}

sql_extract() {
    local OUTPUT=$1; shift
    local FILE=$1; shift

    echo "[-] unpacking sql $FILE."
    sqlite3 $FILE 'SELECT name FROM blobs' | while read fullname; do
        echo "[>] $fullname to $OUTPUT"
        sqlite3 $FILE "SELECT data FROM blobs WHERE name = '$fullname'" > "$OUTPUT/$(basename $fullname)"
    done
}

disunity_extract() {
    local OUTPUT=$1; shift
    local FILE=$1; shift

    echo "[-] disunitying $FILE."
    java -jar $DISUNITY extract -d $OUTPUT $FILE

    if [[ -z "$OUTPUT/*.ahff" ]]; then
        echo "[-] The file didn't yield any ahff files to process."
    else
        for AHFF in $OUTPUT/*.ahff; do
            echo "[-] Converting $AHFF to PNG."
            $AHFF2PNG $AHFF
            rm $AHFF
        done
    fi
}

extract() {
    case $2 in
        *.acb)      acb_extract    $@ ;;
        *.bdb*)     sql_extract      $@ ;;
        *.unity3d*) disunity_extract $@ ;;
        *)          echo "??? $2"       ;;
    esac
}

rip_file() {
    local FILE_TAINTED=0
    local FILE=$1
    case $FILE in
    *.lz4)
        echo "[-] Unzipping lz4 packed file $FILE."
        local UNPK_FILE=$(basename $FILE)
        $LZ4ER $FILE > $OUTPUT/${UNPK_FILE%.lz4}
        FILE=$OUTPUT/${UNPK_FILE%.lz4}
        FILE_TAINTED=1
        ;;
    esac

    extract $OUTPUT $FILE

    if [ $FILE_TAINTED -eq 1 ]; then
        rm $FILE
    fi
}

mkdir -p $OUTPUT
while (( $# )); do
    rip_file $1
    shift
done
