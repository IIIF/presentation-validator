"""Test the schema validator"""
import unittest
import json
import os, sys

sys.path.insert(0,'.')

from schema import schemavalidator

class TestSchema(unittest.TestCase):

    def test_valid_manifests(self):
        for root, subdirs, files in os.walk("fixtures/3/valid"):
            for f in files:
                if f.endswith(".json"):
                    filename = os.path.join(root, f)

                    with open(filename, 'r') as fh:
                        print ('Testing: {}'.format(filename))
                        data = fh.read()
                        j = schemavalidator.validate(data, '3.0')

                        if j['okay'] != 1:
                            if 'errorList' in j:
                                self.printValidationerror(filename, j['errorList'])
                            else:
                                print ('Failed to find errors but manifest {} failed validation'.format(filename))
                                print (j)

                        self.assertEqual(j['okay'], 1, 'Expected manifest {} to pass validation but it failed'.format(filename))

    def test_broken_image(self):
        filename = 'fixtures/3/invalid/broken_simple_image.json'
        response = self.validateFile(filename)

        errorPaths = [ 
            "/provider[0]/logo[0]/['id' is a required property]",
            "/provider[0]/seeAlso[0]/['id' is a required property]",
            # Canvas requires id:
            "/items[0]/['id' is a required property]", 
            # IIIF Context missing
            "/@context"
        ] 

        self.checkValidationErrors(filename, response, errorPaths)

    def test_broken_choice(self):
        filename = 'fixtures/3/invalid/broken_choice.json'
        response = self.validateFile(filename)

        # Missing height
        errorPaths = [ "/items[0]/['height' is a dependency of 'width']" ] 

        self.checkValidationErrors(filename, response, errorPaths)

    def test_broken_collection(self):
        filename = 'fixtures/3/invalid/broken_collection.json'
        response = self.validateFile(filename)

        # Collection requires label
        errorPaths = [ "/['label' is a required property]" ] 

        self.checkValidationErrors(filename, response, errorPaths)

    def test_broken_embedded_annos(self):
        filename = 'fixtures/3/invalid/broken_embedded_annos.json'
        response = self.validateFile(filename)

        # Expected annotations not allowed in AnnotationPage
        errorPaths = [ '/items[0]/items[0]/' ] 

        self.checkValidationErrors(filename, response, errorPaths)

    def test_broken_license(self):
        filename = "fixtures/3/invalid/non_cc_license.json"
        response = self.validateFile(filename)

        errorPaths = [ '/rights/' ]

        self.checkValidationErrors(filename, response, errorPaths)

    def test_collection_of_canvases(self):
        filename = "fixtures/3/invalid/collection_of_canvases.json"
        
        response = self.validateFile(filename)

        errorPaths = [
            '/items[0]', # a canvas shouldn't be allowed in a collection
            '/items[1]'  # a range shouldn't be allowed in a collection
        ]

        self.checkValidationErrors(filename, response, errorPaths)

    def test_broken_service(self):
        filename = 'fixtures/3/invalid/broken_service.json'
        response = self.validateFile(filename)

        errorPaths = [
            '/thumbnail[0]/service', # Service needs to be an array
            '/items[0]/items[0]/items[0]/body/service' # service needs to be an array
        ]

        self.checkValidationErrors(filename, response, errorPaths)

    def test_brokenLabel(self):
        filename = 'fixtures/3/invalid/old_format_label.json'
        response = self.validateFile(filename)

        errorPaths = [
            '/label', # label needs to be an object
            '/label', # label needs to be an object
            '/' # Not allowed to have extra props at root. For example sequences 
        ]

        self.checkValidationErrors(filename, response, errorPaths)

    def test_lang_rights(self):
        filename = 'fixtures/3/invalid/rights_lang_issues.json'
        response = self.validateFile(filename)

        errorPaths = [
            '/items[0]/label[0]', # Can't use @none as a language
            '/items[0]/', # Canvas require items, (height and width) or (duration) or (height, width and duration)
            '/items[0]/',
            "/label/", # Can't use @none as a language
            '/items[0]/items[0]/items[0]/body/label/', # Can't use @none as a language
            '/rights',   # Can't use https link to license 
            '/metadata[0]/label/', # Can't use @none as a language 
            '/metadata[0]/value/', # Can't use @none as a language
            '/metadata[1]/label/', # Can't use @none as a language
            '/metadata[1]/value/', # Can't use @none as a language
            '/metadata[2]/label/', # Can't use @none as a language
            '/metadata[2]/value/', # Can't use @none as a language
            '/metadata[3]/label/', # Can't use @none as a language
            '/metadata[3]/value/', # Can't use @none as a language
            '/metadata[4]/label/', # Can't use @none as a language
            '/metadata[4]/value/', # Can't use @none as a language
            '/metadata[5]/label/', # Can't use @none as a language
            '/metadata[5]/value/', # Can't use @none as a language
            '/metadata[6]/label/', # Can't use @none as a language
            '/metadata[6]/value/', # Can't use @none as a language
            '/metadata[7]/label/', # Can't use @none as a language
            '/metadata[7]/value/', # Can't use @none as a language
            '/metadata[8]/label/', # Can't use @none as a language
            '/metadata[8]/value/', # Can't use @none as a language
            '/metadata[9]/label/', # Can't use @none as a language
            '/metadata[9]/value/'  # Can't use @none as a language
        ]

        self.checkValidationErrors(filename, response, errorPaths)

    def validateFile(self, filename):
       with open(filename, 'r') as fh:
            print ('Testing: {}'.format(filename))
            data = fh.read()
            return schemavalidator.validate(data, '3.0') 

    def printValidationerror(self, filename, errors):                
        print ('Failed to validate: {}'.format(filename))
        errorCount = 1
        for err in errors:
            print(err['title'])
            print(err['detail'])
            print('\n Path for error: {}'.format(err['path']))
            print('\n Context: {}'.format(err['context']))
            errorCount += 1                        

    def checkValidationErrors(self, filename, response, errorPaths):       
        self.assertEqual(response['okay'], 0, 'Expected {} to fail validation but it past. Errors: {}'.format(filename, self.errorAsString(response['errorList'])))
        self.assertEqual(len(response['errorList']), len(errorPaths), 'Expected {} validation errors but found {} for file {}\n{}'.format(len(errorPaths), len(response['errorList']), filename, self.errorAsString(response['errorList'])))
            
        for error in response['errorList']:
            foundPath = False
            for path in errorPaths:
                if error['path'].startswith(path):
                    foundPath=True

            self.assertTrue(foundPath, 'Unexpected path: {} in file {}. Errors: {}'.format(error['path'], filename, self.errorAsString(response['errorList']))) 

    def errorAsString(self, error):
        if type(error) == list:
            response = "\n\n"
            for err in error:
                response += self.errorAsString(err)
                response += "\n****************************\n\n"
        else:                
            response = error['title']
            response += '\n' + error['detail']
            response += '\nPath: ' + error['path']
            response += '\nContext: ' + str(error['context'])

        return response

if __name__ == '__main__':
    unittest.main()