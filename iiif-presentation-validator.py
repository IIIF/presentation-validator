#!/usr/bin/env python
# encoding: utf-8
"""IIIF Presentation Validation Service"""

import argparse
import json
import os
import sys
try:
    # python3
    from urllib.request import urlopen, HTTPError
    from urllib.parse import urlparse
except ImportError:
    # fall back to python2
    from urllib2 import urlopen, HTTPError
    from urlparse import urlparse

from bottle import Bottle, abort, request, response, run

egg_cache = "/path/to/web/egg_cache"
os.environ['PYTHON_EGG_CACHE'] = egg_cache

from iiif_prezi.loader import ManifestReader


class Validator(object):

    def __init__(self):
        self.default_version = "2.1"

    def fetch(self, url):
        # print url
        try:
            wh = urlopen(url)
        except HTTPError as wh:
            pass
        data = wh.read()
        wh.close()
        try:
            data = data.decode('utf-8')
        except:
            pass
        return (data, wh)

    def check_manifest(self, data, version, warnings=[]):
        # Now check data
        reader = ManifestReader(data, version=version)
        err = None
        try:
            mf = reader.read()
            mf.toJSON()
            # Passed!
            okay = 1
        except Exception as e:
            # Failed
            err = e
            okay = 0

        warnings.extend(reader.get_warnings())
        infojson = {'received': data, 'okay': okay, 'warnings': warnings, \
            'error': str(err)}
        return self.return_json(infojson)

    def return_json(self, js):
        response.content_type = "application/json"
        return json.dumps(js)

    def do_POST_test(self):
        data = request.json
        if not data:
            b = request._get_body_string()
            try:
                b = b.decode('utf-8')
            except:
                pass
            data = json.loads(b)
        return self.check_manifest(data, self.default_version)

    def do_GET_test(self):
        url = request.query.get('url', '')
        version = request.query.get('version', self.default_version)
        url = url.strip()

        parsed_url = urlparse(url)
        if not parsed_url.scheme.startswith('http'):
            return self.return_json({'okay': 0, 'error': 'URLs must use HTTP or HTTPS', 'url': url})

        try:
            (data, webhandle) = self.fetch(url)
        except:
            return self.return_json({'okay': 0, 'error': 'Cannot fetch url', 'url': url})

        # First check HTTP level
        ct = webhandle.headers.get('content-type', '')
        cors = webhandle.headers.get('access-control-allow-origin', '')

        warnings = []
        if not ct.startswith('application/json') and not ct.startswith('application/ld+json'):
            # not json
            warnings.append("URL does not have correct content-type header: got \"%s\", expected JSON" % ct)
        if cors != "*":
            warnings.append("URL does not have correct access-control-allow-origin header:"
                            " got \"%s\", expected *" % cors)

        return self.check_manifest(data, version, warnings)

    def index_route(self):
        with open(os.path.join(os.path.dirname(__file__),'index.html'), 'r', encoding='utf-8') as fh:
            data = fh.read()
        return data

    def dispatch_views(self):
        self.app.route("/", "GET", self.index_route)
        self.app.route("/validate", "OPTIONS", self.empty_response)
        self.app.route("/validate", "GET", self.do_GET_test)
        self.app.route("/validate", "POST", self.do_POST_test)

    def after_request(self):
        methods = 'GET,POST,OPTIONS'
        headers = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = methods
        response.headers['Access-Control-Allow-Headers'] = headers
        response.headers['Allow'] = methods

    def empty_response(self, *args, **kwargs):
        """Empty response"""

    def get_bottle_app(self):
        """Returns bottle instance"""
        self.app = Bottle()
        self.dispatch_views()
        self.app.hook('after_request')(self.after_request)
        return self.app


def apache():
    v = Validator()
    return v.get_bottle_app()


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip(),
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--hostname', default='localhost',
                        help='Hostname or IP address to bind to (use 0.0.0.0 for all)')
    parser.add_argument('--port', default=8080, type=int,
                        help='Server port to bind to. Values below 1024 require root privileges.')

    args = parser.parse_args()

    v = Validator()
    run(host=args.hostname, port=args.port, app=v.get_bottle_app())

if __name__ == "__main__":
    main()
else:
    application = apache()
