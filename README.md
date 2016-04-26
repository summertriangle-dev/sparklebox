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

$DISABLE_AUTO_UPDATES - Disables the automatic updater even if VC_* are set.
```

For the `IMAGE_HOST` environment variable, you should use one of these
in most cases:

- `https://hoshimoriuta.kirara.ca` (the public image server for starlight.kirara.ca)

The styles are written in Less. If the environment variable DEV is set,
changes to the less files will be rendered live using less.js;
you don't need to run lessc until you're done changing things.

##### Build static directory

GX is no longer part of this repo. Use SBJK to push deltas to cdn going forward.
