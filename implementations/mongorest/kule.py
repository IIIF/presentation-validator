
# Derived from:
# https://github.com/fatiherikli/kule

try:
    import ljson as json
except:
    import json
from functools import partial
from bson import ObjectId
from pymongo import Connection

from bottle import Bottle, route, run, request, response, abort, error

import uuid
import datetime


class MongoEncoder(json.JSONEncoder):
    """
    Custom encoder for dumping MongoDB documents
    """
    def default(self, obj):

        if isinstance(obj, ObjectId):
            return str(obj)

        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()

        return super(MongoEncoder, self).default(obj)


class MongoRest(object):

    def __init__(self, database=None, host=None, port=None,
                 baseUrl="", sort_keys=True, 
                 compact_json=False, indent_json=2, json_ld=False,
                 url_prefix=""):

        # Mongo Connection
        self.mongo_host = host
        self.mongo_port = port
        self.mongo_db = database
        self.connection = self._connect(database, host, port)

        # baseUrl must NOT end in /
        if baseUrl.endswith('/'):
            baseUrl = baseUrl[:-1]
        self.baseUrl = baseUrl
        # prefix MUST end in /
        if not url_prefix.endswith('/'):
            url_prefix += "/"
        self.prefix = url_prefix

        # JSON Serialization options
        self.sort_keys = sort_keys
        self.compact_json = compact_json
        self.indent_json = indent_json
        self.json_ld = json_ld


        # May want to store non annotations, eg pre-constructed lists for order.
        # Predefine our collection <--> URI mapping here

        self.path_mapping = {
            "manifest" : 'manifests',
            'canvas' : 'canvases',
            'annotation' : 'annotations',
            'user' : 'users',
            'list' : 'lists'
        }


    def _jsonify(self, what, uri):
        try:
            mid = what['_id']
            del what['_id']
            what['@id'] = uri
        except:
            # Constructed objects do not have magic _id
            pass
        if self.compact_json:
            me = MongoEncoder(sort_keys=self.sort_keys, separators=(',',':'))
        else:
            me = MongoEncoder(sort_keys=self.sort_keys, indent=self.indent_json)
        return me.encode(what)

    def _connect(self, database, host=None, port=None):
        """Connects to MongoDB"""
        return Connection(host=host, port=port)[database]

    def _collection(self, rtype):
        if not self.connection:
            self.connection = self._connect(self.mongo_db, self.mongo_host, self.mongo_port)
        collection = self.path_mapping.get(rtype, rtype)
        return self.connection[collection]

    def _make_uri(self, identifier, rtype, name):
        if not name:
            return "%s/%s%s/%s" % (self.baseUrl, self.prefix, identifier, rtype)
        else:
            return "%s/%s%s/%s/%s.json" % (self.baseUrl, self.prefix, identifier, rtype, name)

    def _make_id(self, identifier, rtype, name):
        return "%s/%s" % (identifier, name)


    def get_annotation_list(self, identifier, name):
        rtype = "list"
        coll = self._collection('annotation')

        # prefix/book1/list/canvasName.json --> annotations on canvasName
        target = self._make_uri(identifier, 'canvas', name)
        query = {"$or": [{"on":target}, {"on":{"full":target}}, {"on":{"@id":target}}]}

        # Or... {"on": {"$regex":"^" + escape(q) + "#"}} ... fracking media fragments
        cursor = coll.find(query)
        objects = list(cursor.limit(1000))

        for what in objects:
            mid = what['_id']
            del what['_id']
            (myid, myname) = mid.split('/',1)
            what['@id'] = self._make_uri(identifier, 'annotation', myname)           
            try:
                del what['@context']
            except:
                pass

        uri = self._make_uri(identifier, 'list', name)
        resp = {"@context":"http://www.shared-canvas.org/ns/context.json",
            "@type": "sc:AnnotationList",
            "resources": objects}
        return self._jsonify(resp, uri)


    def get_single(self, identifier, rtype, name):
        """Returns a single document."""

        coll = self._collection(rtype)
        try:
            data = coll.find_one({"_id": self._make_id(identifier, rtype, name)})
        except:
            data = []
        if not data and rtype == 'list':
            return self.get_annotation_list(identifier, name)
        else:
            return abort(404)

        uri = self._make_uri(identifier, rtype, name)
        return self._jsonify(data, uri)

    def put_single(self, identifier, rtype, name):
        """Creates/Updates whole document."""

        coll = self._collection(rtype)
        try:
            js = request.json
        except:
            abort(400, message="JSON is not well formed")

        if js.has_key('_id'):
            del js['_id']
        if js.has_key('@id'):
            del js['@id']

        coll.update({"_id": self._make_id(identifier, rtype, name)}, js)
        response.status = 202
        uri = self._make_uri(identifier, rtype, name)
        return self._jsonify(js, uri)

    def post_single(self, identifier, rtype, name):
        abort(400)

    def patch_single(self, identifier, rtype, name):
        """Updates specific parts of the document."""
        coll = self._collection(rtype)
        coll.update({"_id": ObjectId(self._make_id(identifier, name))},
                          {"$set": request.json})
        response.status = 202
        return self.get_single(identifier, rtype, name)

    def delete_single(self, identifier, rtype, name):
        """Deletes a single document"""
        coll = self._collection(rtype)
        coll.remove({"_id": self._make_id(identifier, rtype, name)})
        response.status = 204

    def post_multiple(self, identifier, rtype):
        """Creates new SINGLE document with server assigned identifier in collection"""
        coll = self._collection(rtype)

        try:    
            js = request.json
        except:
            abort(400, "JSON is not well formed")
        if js.has_key('@id') or js.has_key('_id'):
            abort(400, "Cannot assign to an @id with POST")

        myname = "a%s" % uuid.uuid4()
        myid = self._make_id(identifier, rtype, myname)
        js["_id"] = myid
        inserted = coll.insert(js)
        response.status = 201
        uri = self._make_uri(identifier, rtype, myname)
        return self._jsonify(js, uri)


    def get_multiple(self, identifier, rtype):
        # ?_offset=N&_limit=M&key1=value1&key2=value2
        coll = self._collection(rtype)

        try:
            limit = int(request.query._limit)
            del request.query['_limit']
        except:
            limit = 500
        try:
            offset = int(request.query._offset)
            del request.query['_offset']
        except:
            offset = 0

        query = dict(request.query.items())
        cursor = coll.find(query)

        if not limit:
            objects = []
        else:
            objects = list(cursor.skip(offset).limit(limit))

            for what in objects:
                mid = what['_id']
                del what['_id']
                (myid, myname) = mid.split('/',1)
                what['@id'] = self._make_uri(identifier, rtype, myname)           
                try:
                    del what['@context']
                except:
                    pass

        resp = {"@context":"http://www.shared-canvas.org/ns/context.json",
                "@type": "sc:ResourceList",
                "sc:total_count" : cursor.count(),
                "resources": objects}

        uri = self._make_uri(identifier, rtype, "")
        return self._jsonify(resp, uri)


    def debug(self):
        return repr(self.app.routes)


    def dispatch_views(self):

        methods = ["get", "post", "put", "patch", "delete", "options"]

        self.app.route('/debugRoutes', ['get'], self.debug)

        for m in methods:
            self.app.route('/%s<identifier>/<rtype>/<name>.json' % self.prefix,
                [m], getattr(self, "%s_single" % m, self.not_implemented))
            self.app.route('/%s<identifier>/<rtype>/<name>' % self.prefix,
                [m], getattr(self, "%s_single" % m, self.not_implemented))
            self.app.route('/%s<identifier>/<rtype>' % self.prefix,
                [m], getattr(self, "%s_multiple" % m, self.not_implemented))


    def after_request(self):
        """A bottle hook for json responses."""
        if self.json_ld:
            response['content_type'] = "application/ld+json"
        else:
            response["content_type"] = "application/json"
        methods = 'PUT, PATCH, GET, POST, DELETE, OPTIONS'
        headers = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = methods
        response.headers['Access-Control-Allow-Headers'] = headers


    def not_implemented(self, *args, **kwargs):
        """Returns not implemented status."""
        abort(501)

    def empty_response(self, *args, **kwargs):
        """Empty response"""

    options_list = empty_response
    options_detail = empty_response


    def error(self, error, message=None):
        """Returns the error response."""
        return self._jsonify({"error": error.status_code,
                        "message": error.body or message}, "")

    def get_error_handler(self):
        """Customized errors"""
        return {
            500: partial(self.error, message="Internal Server Error."),
            404: partial(self.error, message="Document Not Found."),
            501: partial(self.error, message="Not Implemented."),
            405: partial(self.error, message="Method Not Allowed."),
            403: partial(self.error, message="Forbidden."),
            400: self.error
        }

    def get_bottle_app(self):
        """Returns bottle instance"""
        self.app = Bottle()
        self.dispatch_views()
        self.app.hook('after_request')(self.after_request)
        self.app.error_handler = self.get_error_handler()
        return self.app


    def run(self, *args, **kwargs):
        """Shortcut method for running kule"""
        kwargs.setdefault("app", self.get_bottle_app())
        run(*args, **kwargs)


def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--bind", dest="address",
                      help="Binds an address to listen")
    parser.add_option("--mongodb-host", dest="mongodb_host",
                      help="MongoDB host")
    parser.add_option("--mongodb-port", dest="mongodb_port",
                      help="MongoDB port")
    parser.add_option("-d", "--database", dest="database",
                      help="MongoDB database name")
    parser.add_option('-p', '--prefix', dest="url_prefix", 
                      help="URL Prefix in API pattern", default="")
    parser.add_option('-s', '--sort-keys', dest="sort_keys", default=True,
                       help="Should json output have sorted keys?")
    parser.add_option('--compact-json', dest="compact_json", default=False,
                       help="Should json output have compact whitespace?")
    parser.add_option('--indent-json', dest="indent_json", default=2,type=int,
                       help="Number of spaces to indent json output")
    parser.add_option('--json-ld', dest="json_ld", default=False,
                       help="Should return json-ld media type instead of json?")

    options, args = parser.parse_args()

    database = options.database
    if not database:
        parser.error("MongoDB database not given.")
    host, port = (options.address or 'localhost'), 8000
    if ':' in host:
        host, port = host.rsplit(':', 1)

    sort_keys = options.sort_keys in ['True', True, '1']
    compact_json = options.compact_json in ['True', True, '1']
    indent = options.indent_json
    jsonld = options.json_ld in ['True', True, '1']
    url_prefix = options.url_prefix

    mr = MongoRest(
        host=options.mongodb_host,
        port=options.mongodb_port,
        database=options.database,
        baseUrl = "http://%s:%s" % (host, port),
        sort_keys=sort_keys,
        compact_json=compact_json,
        indent_json=indent,
        json_ld=jsonld,
        url_prefix=url_prefix
    )

    run(host=host, port=port, app=mr.get_bottle_app())

if __name__ == "__main__":
    main()
