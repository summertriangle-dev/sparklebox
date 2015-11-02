#!/bin/bash

shopt -s nullglob
set -e
OUTPUT=$1; shift
SCRIPT_PATH=`dirname "$0"`; SCRIPT_PATH=`eval "cd \"$SCRIPT_PATH\" && pwd"`

# I need the following executables in this directory.
# Not included in the repo, but you will find them close by.
LZ4ER="$SCRIPT_PATH/lz4er"
DISUNITY="$SCRIPT_PATH/disunity.jar"
AHFF2PNG="$SCRIPT_PATH/ahff2png"

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

    echo "[-] disunitying $FILE."
    java -jar $DISUNITY extract -d $OUTPUT $FILE

    if [ $FILE_TAINTED -eq 1 ]; then
        rm $FILE
    fi

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

mkdir -p $OUTPUT
while (( $# )); do
    rip_file $1
    shift
done
