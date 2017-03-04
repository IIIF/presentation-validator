"""Test code for iiif-presentation-validator.py."""
import unittest
from mock import Mock
import imp
from bottle import Response, request
try:
    # python3
    from urllib.request import URLError
except ImportError:
    # fall back to python2
    from urllib2 import URLError
import json

# The validator isn't a module but with a little magic
# we can load it up as if it were in order to access
# the classes within
fh = open('iiif-presentation-validator.py', 'r')
try:
    val_mod = imp.load_module('ipv', fh, 'iiif-presentation-validator.py',
                              ('py','r',imp.PY_SOURCE))
finally:
    fh.close()


def read_fixture(fixture):
    with open(fixture, 'r') as fh:
        data = fh.read()
    return(data)


class MockWSGI(object):

    def __init__(self, fixture):
        self.fixture = fixture

    def read(self, clen):
        return read_fixture(self.fixture)

class MockWebHandle(object):

    def __init__(self):
        self.headers={}


class TestAll(unittest.TestCase):

    def test01_get_bottle_app(self):
        v = val_mod.Validator()
        self.assertTrue(v.get_bottle_app())

    def test02_fetch(self):
        v = val_mod.Validator()
        (data, wh) = v.fetch('file:fixtures/1/manifest.json')
        self.assertTrue(data.startswith('{'))
        self.assertRaises(URLError, v.fetch, 'file:DOES_NOT_EXIST')

    def test03_check_manifest(self):
        v = val_mod.Validator()
        # good manifests
        for good in ('fixtures/1/manifest.json',
                     'fixtures/2/manifest.json'):
            with open(good, 'r') as fh:
                data = fh.read()
                j = json.loads(v.check_manifest(data, '2.1'))
                self.assertEqual(j['okay'], 1)
        # bad manifests
        for bad_data in ('', '{}'):
            j = json.loads(v.check_manifest(bad_data, '2.1'))
            self.assertEqual(j['okay'], 0)

    def test04_do_POST_test(self):
        v = val_mod.Validator()
        # FIXME - nasty hack to mock data for bottle.request
        m = MockWSGI('fixtures/1/manifest.json')
        request.body = m
        request.environ['wsgi.input'] = m.read
        j = json.loads(v.do_POST_test())
        self.assertEqual(j['okay'], 1)

    def test05_do_GET_test(self):
        # FIXME - hack to mock data for bottle.request
        v = val_mod.Validator()
        request.environ['QUERY_STRING'] = 'url=http://example.org/a'
        v.fetch = Mock(return_value=(read_fixture('fixtures/1/manifest.json'),MockWebHandle()))
        j = json.loads(v.do_GET_test())
        self.assertEqual(j['okay'], 1)
        # bogus URL
        v = val_mod.Validator()
        request.environ['QUERY_STRING'] = 'url=not_http://a.b.c/'
        v.fetch = Mock(return_value=('',MockWebHandle()))
        j = json.loads(v.do_GET_test())
        self.assertEqual(j['okay'], 0)
        # bogus URL but not caught
        v = val_mod.Validator()
        request.environ['QUERY_STRING'] = 'url=httpX://a.b/'
        v.fetch = Mock(return_value=(read_fixture('fixtures/1/manifest.json'),MockWebHandle()))
        j = json.loads(v.do_GET_test())
        self.assertEqual(j['okay'], 1)  #FIXME!

    def test06_index_route(self):
        v = val_mod.Validator()
        html = v.index_route()
        self.assertTrue(html.startswith('<!DOCTYPE html>'))
