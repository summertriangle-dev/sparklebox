#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__) + "/.."))

import json
import sqlite3

from datetime import datetime
import locale
locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

from pytz import timezone, utc
from collections import namedtuple
import models

from starlight import JST, private_data_path
import csvloader

def main():
    if not os.path.exists("./app.py"):
        print("You can only run this program with the cwd set to the main code directory.")

    m = models.TranslationSQL()
    m.sync_event_lookup_table()

if __name__ == '__main__':
    main()
