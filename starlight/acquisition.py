import os
import sqlite3
import lz4
import io
from time import time
from email.utils import mktime_tz, parsedate_tz
from collections import namedtuple
from tornado import httpclient

try:
    lz4_decompress = lz4.loads
    print("Warning: You're using an outdated LZ4 library. Please update it with pip.")
except AttributeError:
    import lz4.block
    lz4_decompress = lz4.block.decompress

DBMANIFEST = "https://asset-starlight-stage.akamaized.net/dl/{0}/manifests"
ASSETBBASEURL = "https://asset-starlight-stage.akamaized.net/dl/resources/AssetBundles"
SOUNDBASEURL = "https://asset-starlight-stage.akamaized.net/dl/resources/Sound"
SQLBASEURL = "https://asset-starlight-stage.akamaized.net/dl/resources/Generic/{1}/{0}"
CACHE = os.path.join(os.path.dirname(__file__), "__manifestloader_cache")
try:
    os.makedirs(CACHE, 0o755)
except FileExistsError:
    pass

def extra_acquisition_headers():
    return {"X-Unity-Version": os.environ.get("VC_UNITY_VER", "5.4.5p1")}

def filename(version, platform, asset_qual, sound_qual):
    return "{0}_{1}_{2}_{3}".format(version, platform, asset_qual, sound_qual)

async def read_manifest(version, platform, asset_qual, sound_qual):
    dest_file = os.path.join(CACHE, filename(version, platform, asset_qual, sound_qual))
    if not os.path.exists(dest_file):
        path = await acquire_manifest(version, platform, asset_qual, sound_qual, dest_file)
    else:
        path = dest_file

    if not path:
        return None

    return sqlite3.connect(path)

manifest_selector_t = namedtuple("manifest_selector_t", ("filename", "md5", "platform", "asset_qual", "sound_qual"))
async def acquire_manifest(version, platform, asset_qual, sound_qual, dest_file):
    cl = httpclient.AsyncHTTPClient()
    meta = "/".join(( DBMANIFEST.format(version), "all_dbmanifest" ))
    try:
        meta = await cl.fetch(meta, headers=extra_acquisition_headers())
    except Exception as e:
        print("acquire_manifest: unhandled error while getting meta:", e)
        return None

    m = meta.body.decode("utf8")
    mp = map(lambda x: manifest_selector_t(* x.split(",")), filter(bool, m.split("\n")))
    get_file = None
    for selector in mp:
        if selector.platform == platform and \
           selector.asset_qual == asset_qual and \
           selector.sound_qual == sound_qual:
            get_file = selector.filename
            break
    else:
        print("No candidate found for", platform, asset_qual, sound_qual)
        return None

    abso = "/".join(( DBMANIFEST.format(version), get_file ))
    try:
        mani = await cl.fetch(abso, headers=extra_acquisition_headers())
    except Exception as e:
        print("acquire_manifest: unhandled error while getting meta:", e)
        return None

    buf = mani.buffer.read()
    bio = io.BytesIO()
    bio.write(buf[4:8])
    bio.write(buf[16:])
    data = lz4_decompress(bio.getvalue())
    with open(dest_file, "wb") as write_db:
        write_db.write(data)
    return dest_file

async def get_master(res_ver, to_path):
    manifest = await read_manifest(res_ver, "Android", "High", "High")
    if not manifest:
        return None

    cur = manifest.execute("SELECT hash, attr FROM manifests WHERE name = ?", ("master.mdb",))
    hash, attr = cur.fetchone()
    manifest.close()

    url = SQLBASEURL.format(hash, hash[0:2])
    cl = httpclient.AsyncHTTPClient()

    try:
        mashttp = await cl.fetch(url, headers=extra_acquisition_headers())
    except Exception as e:
        print("get_master: unhandled error while getting master:", e)
        return None

    buf = mashttp.buffer.read()
    bio = io.BytesIO()
    bio.write(buf[4:8])
    bio.write(buf[16:])
    data = lz4_decompress(bio.getvalue())
    with open(to_path, "wb") as write_db:
        write_db.write(data)

    mdate = mashttp.headers.get("Last-Modified")
    if mdate:
        tt = parsedate_tz(mdate)
        mtime = mktime_tz(tt) if tt else int(time())
    else:
        mtime = int(time.time())
    os.utime(to_path, (-1, mtime))
    return to_path
