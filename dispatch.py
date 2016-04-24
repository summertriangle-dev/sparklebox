import tornado.web
import json
import os
import starlight

ROUTES = []

def conditional_route(yes, reason, *regexes):
    if yes:
        return route(*regexes)
    else:
        print(reason)
        return lambda func: func


def route(*regexes):
    def wrapper(handler):
        for regex in regexes:
            ROUTES.append((regex, handler))
        return handler
    return wrapper


def expose_static_json(path, an_object):
    precomputed = json.dumps(an_object)

    class ret(tornado.web.RequestHandler):
        def get(self):
            self.set_header("Content-Type", "application/json")
            self.set_header("Cache-Control", "no-cache")
            self.set_header("Expires", "0")
            self.write(precomputed)

    route(path)(ret)


def dev_mode_only(wrapped):
    if os.environ.get("DEV", ""):
        return wrapped

    class not_dev_error(tornado.web.RequestHandler):
        def get(self, *args):
            self.set_status(400)
            self.set_header("Content-Type", "text/plain; charset=utf-8")
            self.write(
                "The requested endpoint is only available in development mode.")

    return not_dev_error


class HandlerSyncedWithMaster(tornado.web.RequestHandler):
    def prepare(self):
        starlight.data.reset_statistics()
        starlight.check_version()
        super().prepare()
