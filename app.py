import locale
locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

import tornado.httpserver
import tornado.ioloop
import tornado.web
import os
import tornado.options
import json
import ipaddress
import functools
import subprocess
import user_agents
from collections import namedtuple

import models
import dispatch
import endpoints
import api_endpoints
import enums
import starlight
import analytics
import webutil
from starlight import private_data_path

def early_init():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    if not os.environ.get("DISABLE_HTTPS_ENFORCEMENT", "") and not os.environ.get("DEV", ""):
        # production mode: force https usage due to local storage issues
        # also we don't want the NSA knowing you play chinese cartoon games
        def _swizzle_RequestHandler_prepare(self):
            if self.request.protocol != "https":
                self.redirect(
                    "https://{0}{1}".format(self.request.host, self.request.uri))
        tornado.web.RequestHandler.prepare = _swizzle_RequestHandler_prepare

    if os.environ.get("BEHIND_CLOUDFLARE") == "1":
        cloudflare_ranges = []

        with open("cloudflare.txt", "r") as cf:
            for line in cf:
                cloudflare_ranges.append(ipaddress.ip_network(line.strip()))

        _super_RequestHandler_prepare2 = tornado.web.RequestHandler.prepare

        def _swizzle_RequestHandler_prepare2(self):
            for net in cloudflare_ranges:
                if ipaddress.ip_address(self.request.remote_ip) in net:
                    if "CF-Connecting-IP" in self.request.headers:
                        self.request.remote_ip = self.request.headers[
                            "CF-Connecting-IP"]
                    break
            _super_RequestHandler_prepare2(self)

        tornado.web.RequestHandler.prepare = _swizzle_RequestHandler_prepare2

    _super_RequestHandler_prepare3 = tornado.web.RequestHandler.prepare
    def _swizzle_RequestHandler_prepare3(self):
        self.request.is_low_bandwidth = 0
        if "User-Agent" in self.request.headers:
            ua = user_agents.parse(self.request.headers["User-Agent"])
            if ua.is_mobile or ua.is_tablet:
                self.request.is_low_bandwidth = 1

        _super_RequestHandler_prepare3(self)
    tornado.web.RequestHandler.prepare = _swizzle_RequestHandler_prepare3

def main():
    starlight.init()
    early_init()
    in_dev_mode = os.environ.get("DEV")
    image_server = os.environ.get("IMAGE_HOST", "")
    tornado.options.parse_command_line()
    application = tornado.web.Application(dispatch.ROUTES,
        template_path="webui",
        static_path="static",
        image_host=image_server,
        debug=in_dev_mode,
        is_dev=in_dev_mode,

        tle=models.TranslationEngine(starlight),
        enums=enums,
        starlight=starlight,
        tlable=webutil.tlable,
        webutil=webutil,
        analytics=analytics.Analytics())
    http_server = tornado.httpserver.HTTPServer(application, xheaders=1)

    addr = os.environ.get("ADDRESS", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))

    http_server.listen(port, addr)
    print("Current APP_VER:", os.environ.get("VC_APP_VER",
        "1.9.1 (warning: Truth updates will fail in the future if an accurate VC_APP_VER "
        "is not set. Export VC_APP_VER to suppress this warning.)"))
    print("Ready.")
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
