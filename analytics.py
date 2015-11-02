class Analytics(object):
    """ Called by most endpoints. Log, analyze, whatever here. """
    def analyze_request(self, request: tornado.httputil.HTTPServerRequest,
                        endpoint_class: str, cpar: dict = None):
        pass
