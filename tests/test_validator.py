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

from schema.error_processor import IIIFErrorParser

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
        self.assertTrue(j['error'].startswith('Cannot fetch url'))
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

    def test08_errortrees(self):
        with open('fixtures/3/broken_service.json') as json_file:
            iiif_json = json.load(json_file)

        schema_file = 'schema/iiif_3_0.json'
        with open(schema_file) as json_file:
            schema = json.load(json_file)

        errorParser = IIIFErrorParser(schema, iiif_json)

        # annotationPage
        path = [u'allOf', 1, u'oneOf', 2, u'allOf', 1, u'properties', u'items', u'items', u'allOf', 1, u'properties', u'type', u'pattern']
        iiifPath = [u'items', 0, u'type']
        self.assertFalse(errorParser.isValid(path, iiifPath), 'Matched manifest to annotation page incorrectly')

        # annotationPage
        path = [u'allOf', 1, u'oneOf', 2, u'allOf', 1, u'properties', u'items', u'items', u'allOf', 1, u'required']
        iiifPath = [u'items', 0]
        self.assertFalse(errorParser.isValid(path, iiifPath), 'Matched manifest to annotation page incorrectly')

        # annotationPage
        path = [u'allOf', 1, u'oneOf', 2, u'allOf', 1, u'properties', u'type', u'pattern']
        iiifPath = [u'type']
        self.assertFalse(errorParser.isValid(path, iiifPath), 'Matched manifest to annotation page incorrectly')

        # annotationPage
        path = [u'allOf', 1, u'oneOf', 2, u'allOf', 1, u'additionalProperties']
        iiifPath = []
        self.assertFalse(errorParser.isValid(path, iiifPath), 'Matched manifest to annotation page incorrectly')

        # Collection
        path = [u'allOf', 1, u'oneOf', 1, u'allOf', 1, u'properties', u'thumbnail', u'items', u'oneOf']
        iiifPath = [u'thumbnail', 0]
        self.assertFalse(errorParser.isValid(path, iiifPath), 'Matched manifest to collection incorrectly')

        # Collection
        path = [u'allOf', 1, u'oneOf', 1, u'allOf', 1, u'properties', u'type', u'pattern']
        iiifPath = [u'type']
        self.assertFalse(errorParser.isValid(path, iiifPath), 'Matched manifest to collection incorrectly')

        # Collection
        path = [u'allOf', 1, u'oneOf', 1, u'allOf', 1, u'properties', u'items', u'items', u'oneOf']
        iiifPath = [u'items', 0]
        self.assertFalse(errorParser.isValid(path, iiifPath), 'Matched manifest to collection incorrectly')

        # annotationPage
        path = [u'allOf', 1, u'oneOf', 0, u'allOf', 1, u'properties', u'thumbnail', u'items', u'oneOf']
        iiifPath = [u'thumbnail', 0]
        self.assertTrue(errorParser.isValid(path, iiifPath), 'Should have caught the service in thumbnail needs to be an array.')

        # annotationPage
        path = [u'allOf', 1, u'oneOf', 0, u'allOf', 1, u'properties', u'items', u'items', u'allOf', 1, u'properties', u'items', u'items', u'allOf', 1, u'properties', u'items', u'items', u'allOf', 1, u'properties', u'body', u'oneOf']
        iiifPath = [u'items', 0, u'items', 0, u'items', 0, u'body']
        self.assertTrue(errorParser.isValid(path, iiifPath), 'Should have caught the service in the canvas needs to be an array')

        with open('fixtures/3/broken_simple_image.json') as json_file:
            iiif_json = json.load(json_file)
        errorParser = IIIFErrorParser(schema, iiif_json)
        # Provider as list example:
        path = ['allOf', 1, 'oneOf', 0, 'allOf', 1, 'properties', 'provider', 'items', 'allOf', 1, 'properties', 'seeAlso', 'items', 'allOf', 0, 'required']
        iiifPath = ['provider', 0, 'seeAlso', 0]
        self.assertTrue(errorParser.isValid(path, iiifPath))
    
    def test_version3errors(self):
        v = val_mod.Validator()

        filename = 'fixtures/3/broken_simple_image.json'
        errorPaths = [
            '/provider[0]/logo[0]',
            '/provider[0]/seeAlso[0]',
            '/items[0]'
        ]
        response = self.helperRunValidation(v, filename)
        self.helperTestValidationErrors(filename, response, errorPaths)

        filename = 'fixtures/3/broken_service.json'
        errorPaths = [
            '/thumbnail[0]/service',
            '/body[0]/items[0]/items[0]/items/items[0]/items[0]/items[0]/body/service'
        ]
        response = self.helperRunValidation(v, filename)
        self.helperTestValidationErrors(filename, response, errorPaths)


    def helperTestValidationErrors(self, filename, response, errorPaths):       
        self.assertEqual(response['okay'], 0, 'Expected {} to fail validation but it past.'.format(filename))
        self.assertEqual(len(response['errorList']), len(errorPaths), 'Expected {} validation errors but found {} for file {}'.format(len(errorPaths), len(response['errorList']), filename))

        for error in response['errorList']:
            foundPath = False
            for path in errorPaths:
                if error['path'].startswith(path):
                    foundPath=True
            self.assertTrue(foundPath, 'Unexpected path: {} in file {}'.format(error['path'], filename)) 

    def helperRunValidation(self, validator, iiifFile, version="3.0"):
        with open(iiifFile, 'r') as fh:
            data = fh.read()
            return json.loads(validator.check_manifest(data, '3.0'))

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
