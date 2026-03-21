"""Test code for iiif-presentation-validator.py."""
import unittest
from unittest.mock import Mock
import importlib
from pathlib import Path

from bottle import Response, request, LocalRequest

from urllib.request import URLError
import json

from presentation_validator.validator import check_manifest
from presentation_validator.v3.error_processor import IIIFErrorParser

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

    def test_good_manifests_v2(self):
        # good manifests
        for good in ('fixtures/1/manifest.json',
                     'fixtures/2/manifest.json'):
            with open(good, 'r') as fh:
                data = fh.read()
                result = check_manifest(data, '2.1')
                self.assertTrue(result.passed)

    def test_bad_manifests_v2(self):
        # bad manifests
        for bad_data in ('', '{}'):
            result = check_manifest(bad_data, '2.1')
            self.assertFalse(result.passed)

    def test_good_manifests_v3(self):
        # good manifests
        for good in ['fixtures/3/simple_video.json',
                     'fixtures/3/full_example.json',
                     'fixtures/3/choice.json',
                     'fixtures/3/collection.json',
                     'fixtures/3/collection_of_collections.json',
                     'fixtures/3/version2image.json',
                     'fixtures/3/annoPage.json',
                     'fixtures/3/anno_pointselector.json',
                     'fixtures/3/annoPageMultipleMotivations.json',
                     'fixtures/3/old_cc_license.json',
                     'fixtures/3/rightsstatement_license.json',
                     'fixtures/3/extension_anno.json',
                     'fixtures/3/multi_bodies.json',
                     'fixtures/3/publicdomain.json',
                     'fixtures/3/navPlace.json',
                     'fixtures/3/anno_source.json',
                     'fixtures/3/range_range.json',
                     'fixtures/3/accompanyingCanvas.json',
                     'fixtures/3/placeholderCanvas.json',
                     'fixtures/3/point_selector.json',
                     'fixtures/3/annotation_full.json',
                     'fixtures/3/content_state.json'
                     ]:
            with open(good, 'r') as fh:
                print ('Testing: {}'.format(good))
                data = fh.read()
                result = check_manifest(data, '3.0')
                if not result.passed:
                    if 'errorList' in result.errorList:
                        self.printValidationerror(good, result.errorList)
                    else:
                        print ('Failed to find errors but manifest {} failed validation'.format(good))
                        print (result)

                self.assertTrue(result.passed, 'Expected manifest {} to pass validation but it failed'.format(good))

    def test_bad_manifests_v3(self):
        for bad_data in ['fixtures/3/broken_simple_image.json',
                         'fixtures/3/broken_choice.json',
                         'fixtures/3/broken_collection.json',
                         'fixtures/3/broken_embedded_annos.json',
                         'fixtures/3/non_cc_license.json',
                         'fixtures/3/collection_of_canvases.json']:
            with open(bad_data, 'r') as fh:
                data = fh.read()
                result = check_manifest(data, '3.0')

                if result.passed:
                    print("Expected {} to fail validation but it passed....".format(bad_data))
                
                self.assertFalse(result.passed)

    def test_good_manifests_v4(self):
        base = Path("fixtures/4/ok")
        data = []
        for path in base.rglob("*.json"):
            with path.open("r", encoding="utf-8") as f:
                print ('Testing: {}'.format(path))
                data = json.load(f)
        
                result = check_manifest(data, '4.0')
                if not result.passed:
                    if 'errorList' in result.errorList:
                        self.printValidationerror(path, result.errorList)
                    else:
                        print ('Failed to find errors but manifest {} failed validation'.format(path))
                        print (json.dumps(result.json(), indent=2))

                self.assertTrue(result.passed, 'Expected manifest {} to pass validation but it failed'.format(path))            
                
    def test_bad_manifests_v4(self):
        base = Path("fixtures/4/bad")
        data = []
        for path in base.rglob("*.json"):
            with path.open("r", encoding="utf-8") as f:
                print ('Testing: {}'.format(path))
                data = json.load(f)

                result = check_manifest(data, '3.0')

                if result.passed:
                    print(f"Expected {path} to fail validation but it passed....")
                
                self.assertFalse(result.passed)
    

    def printValidationerror(self, filename, errors):
        print('Failed to validate: {}'.format(filename))
        
    def test_errortrees(self):
        with open('fixtures/3/broken_service.json') as json_file:
            iiif_json = json.load(json_file)

        schema_file = 'schema/iiif_3_0.json'
        with open(schema_file) as json_file:
            schema = json.load(json_file)

        errorParser = IIIFErrorParser(schema, iiif_json)

        #print (errorParser)
        # annotationPage
        path = [ u'oneOf', 2, u'allOf', 1, u'properties', u'items', u'items', u'properties', u'type', u'pattern']
        iiifPath = [u'items', 0, u'type']
        self.assertFalse(errorParser.isValid(path, iiifPath), 'Matched manifest to annotation page incorrectly')

        # annotationPage
        path = [u'oneOf', 2, u'allOf', 1, u'properties', u'items', u'items', u'required']
        iiifPath = [u'items', 0]
        self.assertFalse(errorParser.isValid(path, iiifPath), 'Matched manifest to annotation page incorrectly')

        # annotationPage
        path = [u'oneOf', 2,u'allOf', 1,  u'properties', u'type', u'pattern']
        iiifPath = [u'type']
        self.assertFalse(errorParser.isValid(path, iiifPath), 'Matched manifest to annotation page incorrectly')

        # annotationPage
        path = [u'oneOf', 2,u'allOf', 1,  u'additionalProperties']
        iiifPath = []
        self.assertFalse(errorParser.isValid(path, iiifPath), 'Matched manifest to annotation page incorrectly')

        # Collection
        path = [u'oneOf', 1, u'allOf', 1, u'properties', u'thumbnail', u'items', u'oneOf']
        iiifPath = [u'thumbnail', 0]
        self.assertFalse(errorParser.isValid(path, iiifPath), 'Matched manifest to collection incorrectly')

        # Collection
        path = [u'oneOf', 1, u'allOf', 1, u'properties', u'type', u'pattern']
        iiifPath = [u'type']
        self.assertFalse(errorParser.isValid(path, iiifPath), 'Matched manifest to collection incorrectly')

        # Collection
        path = [u'oneOf', 1, u'allOf', 1, u'properties', u'items', u'items', u'oneOf']
        iiifPath = [u'items', 0]
        self.assertFalse(errorParser.isValid(path, iiifPath), 'Matched manifest to collection incorrectly')

        # annotationPage
        path = [u'oneOf', 0, u'allOf', 1, u'properties', u'thumbnail', u'items', u'oneOf']
        iiifPath = [u'thumbnail', 0]
        self.assertTrue(errorParser.isValid(path, iiifPath), 'Should have caught the service in thumbnail needs to be an array.')

        # annotationPage
        path = [u'oneOf', 0, u'allOf', 1, u'properties', u'items', u'items', u'allOf', 1, u'properties', u'items', u'items',  u'allOf', 1, u'properties',  u'items', u'items', u'properties', u'body', u'anyOf']
        iiifPath = [u'items', 0, u'items', 0, u'items', 0, u'body']
        self.assertTrue(errorParser.isValid(path, iiifPath), 'Should have caught the service in the canvas needs to be an array')

        with open('fixtures/3/broken_simple_image.json') as json_file:
            iiif_json = json.load(json_file)
        errorParser = IIIFErrorParser(schema, iiif_json)
        # Provider as list example:
        path = ['oneOf', 0, 'allOf', 1, 'properties', 'provider', 'items', 'allOf', 1, 'properties', 'seeAlso', 'items', 'allOf', 0, 'required']
        iiifPath = ['provider', 0, 'seeAlso', 0]
        self.assertTrue(errorParser.isValid(path, iiifPath))
    
    def test_version3errors(self):
        filename = 'fixtures/3/broken_simple_image.json'
        errorPaths = [
            '/provider[0]/logo[0]',
            '/provider[0]/seeAlso[0]',
            '/items[0]'
        ]
        response = self.helperRunValidation(filename)
        self.helperTestValidationErrors(filename, response, errorPaths)

        filename = 'fixtures/3/broken_service.json'
        errorPaths = [
            '/thumbnail[0]/service',
            '/items[0]/items[0]/items[0]/body/'
        ]
        response = self.helperRunValidation(filename)
        self.helperTestValidationErrors(filename, response, errorPaths)

        filename = 'fixtures/3/old_format_label.json'
        errorPaths = [
            '/label',
            '/'
        ]
        response = self.helperRunValidation(filename)
        self.helperTestValidationErrors(filename, response, errorPaths)

    def test_lang_rights(self):
        filename = 'fixtures/3/rights_lang_issues.json'
        errorPaths = [
            '/label',
            '/items[0]/label[0]',
            '/items[0]/',
            '/items[0]/items[0]/items[0]/body/',
            '/rights',
            '/metadata[0]/label/',
            '/metadata[0]/value/',
            '/metadata[1]/label/',
            '/metadata[1]/value/',
            '/metadata[2]/label/',
            '/metadata[2]/value/',
            '/metadata[3]/label/',
            '/metadata[3]/value/',
            '/metadata[4]/label/',
            '/metadata[4]/value/',
            '/metadata[5]/label/',
            '/metadata[5]/value/',
            '/metadata[6]/label/',
            '/metadata[6]/value/',
            '/metadata[7]/label/',
            '/metadata[7]/value/',
            '/metadata[8]/label/',
            '/metadata[8]/value/',
            '/metadata[9]/label/',
            '/metadata[9]/value/'
        ]
        response = self.helperRunValidation(filename)
        self.helperTestValidationErrors(filename, response, errorPaths)

    def formatErrors(self, errorList):
        response = ''
        for error in errorList:
            response += f"Title: {error.title}\n"
            response += f"Path: {error.path}\n"
            response += f"Context: {error.context}\n"
            response += "****************************\n"

        return response

    def helperTestValidationErrors(self, filename, response, errorPaths):       
        self.assertFalse(response.passed, 'Expected {} to fail validation but it past.'.format(filename))
        self.assertEqual(len(response.errorList), len(errorPaths), 'Expected {} validation errors but found {} for file {}\n{}'.format(len(errorPaths), len(response.errorList), filename, self.formatErrors(response.errorList)))
            

        for error in response.errorList:
            foundPath = False
            for path in errorPaths:
                if error.path.startswith(path):
                    foundPath=True
            self.assertTrue(foundPath, 'Unexpected path: {} in file {}'.format(error.path, filename)) 

    def helperRunValidation(self, iiifFile, version="3.0"):
        with open(iiifFile, 'r') as fh:
            data = fh.read()
            return check_manifest(data, '3.0')

        #errorCount = 1

        #for err in errors:
        #    print(err['title'])
        #    print(err['detail'])
        #    print('\n Path for error: {}'.format(err['path']))
        #    print('\n Context: {}'.format(err['context']))
        #    errorCount += 1


if __name__ == '__main__':
    unittest.main()
