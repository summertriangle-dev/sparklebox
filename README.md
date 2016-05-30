# sparklebox (2.0!)

https://starlight.kirara.ca/

##### Getting started

Make a virtualenv (the app is actively used with Python 3.3 and 3.5):

    virtualenv --python=python3 .env
    source .env/bin/activate
    pip install -r requirements.txt

Grab a copy of ENAMDICT from http://www.csse.monash.edu.au/~jwb/enamdict_doc.html ,
then convert it to UTF-8 so name_finder can use it:

    zcat enamdict.gz | iconv -f eucjp -t utf8 > _data/private/enamdictu

Then configure the environment variables (I suggest saving these to a file as
you go, so you can restore them later).

    # Development mode disables Tornado's internal caching as well as
    # HTTPS enforcement.
    export DEV=1
    export TRANSIENT_DATA_DIR="_data/transient"

    mkdir -p $TRANSIENT_DATA_DIR
    # Note the lack of $. This is the name of the variable that has
    # the transient data dir.
    export TRANSIENT_DIR_POINTER=TRANSIENT_DATA_DIR
    export DATABASE_CONNECT='sqlite:///'$TRANSIENT_DATA_DIR'/ss.sqlite3'
    export TLABLE_SALT='bang on the keyboard for a random string'
    export IMAGE_HOST='https://static.myderesutesite.com'

If you do not know values for `VC_ACCOUNT`, `VC_AES_KEY`, and `VC_SID_SALT`,
start the app with a version number as the first argument.

    python3 app.py [59234863]

That's obviously not the correct version number, but you can find it on
[any](https://starlight.kirara.ca/) of the [sites](http://usamin.info/) which
have [them](https://boards.4chan.org/vg/catalog#s=idolm@ster). Alternatively,
you can sniff network traffic using a proxy like Charles.

Otherwise, set those environment variables and run.

    python3 app.py

The server will download the current truth automatically, then exit.
You will then be able to run the app.

##### Configuration

The following environment variables are used:

```
$DEV - enables various development features, such as
    * /tl_debug, /db/... endpoints
    * No caching of templates
    * No HTTPS enforcement
    * No static file caching

$TLABLE_SALT - Security salt for translation tokens. It prevents users from
    spamming /send_tl endpoint with strings that never occur.

$DATABASE_CONNECT - Connection string for the translation database. Follows
    SQLAlchemy syntax, and you must have the right package installed to talk to
    the particular kind of database engine you use.

$IMAGE_HOST - Prepended to all static content, discussed below.

$ADDRESS - IP address to bind to. Usually you want 0.0.0.0 to bind all interfaces.

$PORT - Port to listen on (for HTTP/HTTPS). Defaults to 5000.

$VC_ACCOUNT - Credentials for automatic updating, in the form user_id:viewer_id:udid.

$VC_SID_SALT, $VC_AES_KEY - Client secrets used for automatic updating.

$VC_APP_VER - Game version (not data version), e.g. "1.9.1". Used for automatic updating.
    The game will reject version checks with an outdated client, so it's important to
    keep this up to date.

$TLE_DISABLE_CACHES - Disable local caching of TranslationEngine data. Set this to a
    non-blank string if DB query speed doesn't matter (e.g. you use SQLite, or mysqld
    is running on the same server as the app)

$DISABLE_AUTO_UPDATES - Disables the automatic updater even if VC_* are set.

$TLE_TABLE_PREFIX - Prefix for table names in TranslationSQL. Defaults to 'ss'.

```

For the `IMAGE_HOST` environment variable, you should use one of these
in most cases:

- `https://hoshimoriuta.kirara.ca` (the public image server for starlight.kirara.ca)

The styles are written in Less. If the environment variable DEV is set,
changes to the less files will be rendered live using less.js;
you don't need to run lessc until you're done changing things.

##### Build static directory

GX is no longer part of this repo. Use SBJK to push deltas to cdn going forward.

### License

Unless the file says otherwise, the files in this repo are released
under the BSD license:

Copyright (c) 2015 - 2016, The Holy Constituency of the Summer Triangle.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright
  notice, this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.
* Neither the name of the Holy Constituency of the Summer Triangle nor the
  names of its contributors may be used to endorse or promote products
  derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE HOLY CONSTITUENCY OF THE SUMMER TRIANGLE
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
