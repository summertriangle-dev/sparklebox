import subprocess
import os
from time import time
from tornado import ioloop

import starlight
from . import apiclient
from . import acquisition
from threading import Lock

update_lock = Lock()
last_version_check = 0

def do_preswitch_tasks(new_db_path, old_db_path):
    subprocess.call(["toolchain/name_finder.py",
        starlight.private_data_path("enamdictu"),
        new_db_path,
        starlight.transient_data_path("names.csv")])

    if not os.getenv("DISABLE_HISTORY_UPDATES", None):
        subprocess.call(["toolchain/update_rich_history.py", new_db_path])

    if old_db_path:
        subprocess.call(["toolchain/make_contiguous_gacha.py", old_db_path, new_db_path])

async def update_to_res_ver(res_ver):
    global last_version_check
    mdb_path = starlight.ark_data_path("{0}.mdb".format(res_ver))
    if not os.path.exists(mdb_path):
        new_path = await acquisition.get_master(res_ver,
            starlight.transient_data_path("{0}.mdb".format(res_ver)))

    last_version_check = time()

    if new_path:
        old_path = None
        if starlight.data:
            old_path = starlight.transient_data_path("{0}.mdb".format(starlight.data.version))

        try:
            do_preswitch_tasks(new_path, old_path)
        except Exception as e:
            print("do_preswitch_tasks croaked, update aborted.")
            raise

        starlight.hand_over_to_version(res_ver)
        apiclient.ApiClient.shared().res_ver = str(res_ver)

async def async_version_check(release):
    response, msg = await apiclient.versioncheck()
    if not msg:
        print("Update check failed.")
        release()
        return

    res_ver = msg.get(b"data_headers", {}).get(b"required_res_ver", b"-1").decode("utf8")
    if not starlight.data or res_ver != starlight.data.version:
        if res_ver != "-1":
            print("Proceeding with update to version", res_ver, "...")
            await update_to_res_ver(res_ver)
        else:
            print("No required_res_ver, we're either on latest or app is outdated")

    release()

def _watchdog_check():
    if not update_lock.acquire(blocking=False):
        print("warning: update lock was held for more than 5 minutes - forcibly releasing.")
        update_lock.release()
    else:
        update_lock.release()

### PUBLIC API STARTS HERE ################################
### EVERYTHING ABOVE IS PRIVATE ###########################

def is_currently_updating():
    return update_lock.locked()

def check_version():
    """Dispatch a version check if needed, and return whether we did."""

    global last_version_check
    if time() - last_version_check >= 3600 or time() < last_version_check:
        if not apiclient.is_usable():
            return False

        if not update_lock.acquire(blocking=False):
            return False

        # usually updates happen on the hour so this keeps our
        # schedule on the hour too
        t = time()
        last_version_check = t - (t % 3600)

        loop = ioloop.IOLoop.current()
        h = loop.call_later(5 * 60, _watchdog_check)

        def release():
            print("Done, releasing lock.")
            loop.remove_timeout(h)
            update_lock.release()

        loop.add_callback(async_version_check, release)
        return True
    return False
