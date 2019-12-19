"""Test code for iiif-presentation-validator.py."""
import unittest
from mock import Mock
import imp
from bottle import Response, request, LocalRequest

try:
    # python3
    from urllib.request import URLError
except ImportError:
    # fall back to python2
    from urllib2 import URLError
import json

from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

# The validator isn't a module but with a little magic
# we can load it up as if it were in order to access
# the classes within
fh = open('iiif-presentation-validator.py', 'r')
try:
    val_mod = imp.load_module('ipv', fh, 'iiif-presentation-validator.py',
                              ('py', 'r', imp.PY_SOURCE))
finally:
    fh.close()


def read_fixture(fixture):
    """Read data from text fixture."""
    with open(fixture, 'r') as fh:
        data = fh.read()
    return(data)


class MockWSGI(object):
    """Mock WSGI object with data read from fixture."""

    def __init__(self, fixture):
        """Initialize mock object with fixture filename."""
        self.fixture = fixture

    def read(self, clen):
        """Read from fixture."""
        return read_fixture(self.fixture)


class MockWebHandle(object):
    """Mock WebHandle object with empty headers."""

    def __init__(self):
        """Initialize mock object with empty headers."""
        self.headers = {}


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
        """Test POST requests -- machine interaction with validator service."""
        v = val_mod.Validator()
        # FIXME - nasty hack to mock data for bottle.request
        m = MockWSGI('fixtures/1/manifest.json')
        request.body = m
        request.environ['wsgi.input'] = m.read
        j = json.loads(v.do_POST_test())
        self.assertEqual(j['okay'], 1)

    def test05_do_GET_test(self):
        """Test GET requests -- typical user interaction with web form."""
        # Note that attempting to set request.environ['QUERY_STRING'] to mock
        # input data works only the first time. Instead create a new request
        # object to similate each web request, with data that sets request.environ
        v = val_mod.Validator()
        request = LocalRequest({'QUERY_STRING': 'url=https://example.org/a'})
        v.fetch = Mock(return_value=(read_fixture('fixtures/1/manifest.json'), MockWebHandle()))
        j = json.loads(v.do_GET_test())
        self.assertEqual(j['okay'], 1)
        self.assertEqual(j['url'], 'https://example.org/a')
        # fetch failure
        v = val_mod.Validator()
        request = LocalRequest({'QUERY_STRING': 'url=http://example.org/a'})
        v.fetch = Mock()
        v.fetch.side_effect = Exception('Fetch failed')
        j = json.loads(v.do_GET_test())
        self.assertEqual(j['okay'], 0)
        self.assertEqual(j['error'], 'Cannot fetch url')
        # bogus URL
        v = val_mod.Validator()
        request = LocalRequest({'QUERY_STRING': 'url=not_http://a.b.c/'})
        v.fetch = Mock(return_value=(read_fixture('fixtures/1/manifest.json'), MockWebHandle()))
        j = json.loads(v.do_GET_test())
        self.assertEqual(j['okay'], 0)
        # another bogus URL
        v = val_mod.Validator()
        request = LocalRequest({'QUERY_STRING': 'url=httpX://a.b/'})
        v.fetch = Mock(return_value=(read_fixture('fixtures/1/manifest.json'), MockWebHandle()))
        j = json.loads(v.do_GET_test())
        self.assertEqual(j['okay'], 0)

    def test06_index_route(self):
        """Test index page."""
        v = val_mod.Validator()
        html = v.index_route()
        self.assertTrue(html.startswith('<!DOCTYPE html>'))

    def test07_check_manifest3(self):
        v = val_mod.Validator()
        # good manifests
        for good in ['fixtures/3/simple_video.json',
                     'fixtures/3/full_example.json',
                     'fixtures/3/choice.json',
                     'fixtures/3/collection.json',
                     'fixtures/3/collection_of_collections.json',
                     'fixtures/3/version2image.json',
                     'fixtures/3/annoPage.json',
                     'fixtures/3/anno_pointselector.json',
                     'fixtures/3/annoPageMultipleMotivations.json'
                     ]:
            with open(good, 'r') as fh:
                data = fh.read()
                j = json.loads(v.check_manifest(data, '3.0'))
                if j['okay'] != 1:
                    self.printValidationerror(good, j['errorList'])

                self.assertEqual(j['okay'], 1)

        for bad_data in ['fixtures/3/broken_simple_image.json',
                         'fixtures/3/broken_choice.json',
                         'fixtures/3/broken_collection.json',
                         'fixtures/3/broken_embedded_annos.json']:
            with open(bad_data, 'r') as fh:
                data = fh.read()
                j = json.loads(v.check_manifest(data, '3.0'))

                if j['okay'] == 1:
                    print ("Expected {} to fail validation but it passed....".format(bad_data))
                
                self.assertEqual(j['okay'], 0)


    def printValidationerror(self, filename, errors):                
        print ('Failed to validate: {}'.format(filename))
        errorCount = 1
        for err in errors:
            print(err['title'])
            print(err['detail'])
            print('\n Path for error: {}'.format(err['path']))
            print('\n Context: {}'.format(err['context']))
            errorCount += 1

if __name__ == '__main__':
    unittest.main()
