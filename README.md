# sparklebox

https://starlight.kirara.ca/

Start a virtualenv (the app is actively used with Python 3.3 and 3.5):
- `virtualenv .env`
- `source .env/bin/activate`
- `pip install -r requirements.txt`

Then configure the environment (see below) and `python3 app.py`.
Set the `VC_ACCOUNT`, `VC_AES_KEY` and `VC_SID_SALT` environment variables
and the server will download the current truth automatically. (It may then
crash. Just start it again.)

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
```

For the `IMAGE_HOST` environment variable, you should use one of these
in most cases:

- `https://hoshimoriuta.kirara.ca` (the public image server for starlight.kirara.ca)

The styles are written in Less. If the environment variable DEV is set,
changes to the less files will be rendered live using less.js;
you don't need to run lessc until you're done changing things.

##### Build static directory

GX is no longer part of this repo. Use SBJK to push deltas to cdn going forward.
