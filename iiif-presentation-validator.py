#!/usr/bin/env python
# encoding: utf-8
"""IIIF Presentation Validation Service."""

import argparse
import codecs
import json
import os
from gzip import GzipFile
from io import BytesIO

try:
    # python3
    from urllib.request import urlopen, HTTPError, Request
    from urllib.parse import urlparse
except ImportError:
    # fall back to python2
    from urllib2 import urlopen, HTTPError, Request
    from urlparse import urlparse

from bottle import Bottle, request, response, run
from schema import schemavalidator

egg_cache = "/path/to/web/egg_cache"
os.environ['PYTHON_EGG_CACHE'] = egg_cache

from iiif_prezi.loader import ManifestReader

IIIF_HEADER = "application/ld+json;profile=http://iiif.io/api/presentation/{iiif_version}/context.json"


class Validator(object):
    """Validator class that runs with Bottle."""

    def __init__(self):
        """Initialize Validator with default_version."""
        self.default_version = "2.1"

    def fetch(self, url, accept_header):
        """Fetch manifest from url."""
        req = Request(url)
        req.add_header('Accept-Encoding', 'gzip')

        if accept_header:
            req.add_header('Accept', accept_header)

        try:
            wh = urlopen(req)
        except HTTPError as wh:
            pass
        data = wh.read()
        wh.close()

        if wh.headers.get('Content-Encoding') == 'gzip':
            with GzipFile(fileobj=BytesIO(data)) as f:
                data = f.read()

        try:
            data = data.decode('utf-8')
        except:
            pass
        return(data, wh)

    def check_manifest(self, data, version, url=None, warnings=[]):
        """Check manifest data at version, return JSON."""
        infojson = {}
        # Check if 3.0 if so run through schema rather than this version...
        if version == '3.0':
            infojson = schemavalidator.validate(data, version, url)
        else:
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
            infojson = {
                'received': data,
                'okay': okay,
                'warnings': warnings,
                'error': str(err),
                'url': url
            }
        return self.return_json(infojson)

    def return_json(self, js):
        """Set header and return JSON response."""
        response.content_type = "application/json"
        return json.dumps(js)

    def do_POST_test(self):
        """Implement POST request to test posted data at default version."""
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
        """Implement GET request to test url at version."""
        url = request.query.get('url', '')
        version = request.query.get('version', self.default_version)
        accept = request.query.get('accept')
        accept_header = None
        url = url.strip()
        parsed_url = urlparse(url)

        if accept and accept == 'true':
            if version in ("2.0", "2.1"):
                accept_header = IIIF_HEADER.format(iiif_version=2)
            elif version in ("3.0",):
                accept_header = IIIF_HEADER.format(iiif_version=3)
            else:
                accept_header = "application/json"

        if (parsed_url.scheme != 'http' and parsed_url.scheme != 'https'):
            return self.return_json({'okay': 0, 'error': 'URLs must use HTTP or HTTPS', 'url': url})

        try:
            (data, webhandle) = self.fetch(url, accept_header)
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

        content_encoding = webhandle.headers.get('Content-Encoding', '')
        if content_encoding != 'gzip':
            warnings.append('The remote server did not use the requested gzip'
                            ' transfer compression, which will slow access.'
                            ' (Content-Encoding: %s)' % content_encoding)
        elif 'Accept-Encoding' not in webhandle.headers.get('Vary', ''):
            warnings.append('gzip transfer compression is enabled but the Vary'
                            ' header does not include Accept-Encoding, which'
                            ' can cause compatibility issues')

        return self.check_manifest(data, version, url, warnings)

    def index_route(self):
        """Read and return index page."""
        with codecs.open(os.path.join(os.path.dirname(__file__), 'index.html'), 'r', 'utf-8') as fh:
            data = fh.read()
        return data

    def dispatch_views(self):
        """Set up path mappings."""
        self.app.route("/", "GET", self.index_route)
        self.app.route("/validate", "OPTIONS", self.empty_response)
        self.app.route("/validate", "GET", self.do_GET_test)
        self.app.route("/validate", "POST", self.do_POST_test)

    def after_request(self):
        """Used with after_request hook to set response headers."""
        methods = 'GET,POST,OPTIONS'
        headers = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = methods
        response.headers['Access-Control-Allow-Headers'] = headers
        response.headers['Allow'] = methods

    def empty_response(self, *args, **kwargs):
        """Empty response."""

    def get_bottle_app(self):
        """Return bottle instance."""
        self.app = Bottle()
        self.dispatch_views()
        self.app.hook('after_request')(self.after_request)
        return self.app


def apache():
    """Run as WSGI application."""
    v = Validator()
    return v.get_bottle_app()


def main():
    """Parse argument and run server when run from command line."""
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
