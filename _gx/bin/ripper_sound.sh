#!/bin/bash

shopt -s nullglob
set -e
OUTPUT=$(realpath "$1"); shift
STAVOICE=$(realpath "$1"); shift
SCRIPT_PATH=`dirname "$0"`; SCRIPT_PATH=`eval "cd \"$SCRIPT_PATH\" && pwd"`

# I need the following executables in this directory.
# Not included in the repo, but you will find them close by.
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

rip_file() {
    local FILE=$1
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
            $HCA_DECODER $HCA -o /dev/stdout | ffmpeg $FFMPEG_OPTIONS $FN || true

            case $(basename "$FN") in
            voice_*.mp3)
                local F=$(py_mangle_fn $(basename "$FN"))
                cp $FN "$STAVOICE/$F.mp3"
                ;;
            esac
        done
        cd $WHERE
    fi

    rm -rf $TMPD
}

mkdir -p $OUTPUT
while (( $# )); do
    rip_file $1
    shift
done
