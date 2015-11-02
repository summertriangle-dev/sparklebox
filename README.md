# sparklebox

https://starlight.kirara.ca/

To get started, you need to put data in `_data`. The recommended order:
- Download and extract truth to `_data/ark`
- Download and extract storydata to `_data/stories`
- Write the current truth version to `_data/private/masters_version.txt`
- Use `name_finder` to romanize names to `_data/private/names.csv`
- `touch _data/private/history.json`

Then start a virtualenv (the app is actively used with Python 3.2 and 3.5):
- `virtualenv .env`
- `source .env/bin/activate`
- `pip install -r requirements.txt`

Then configure the environment (see below) and `python3 app.py`.

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
```

For the `IMAGE_HOST` environment variable, you should use one of these
in most cases:

- `/static/xxx`, where xxx is a symlink to GX's _static directory
- `https://hoshimoriuta.kirara.ca` (the public image server for starlight.kirara.ca)

The styles are written in Less. If the environment variable DEV is set,
changes to the less files will be rendered live using less.js;
you don't need to run lessc until you're done changing things.

##### Build static directory

... something ...
