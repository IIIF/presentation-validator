"""Test code for iiif-presentation-validator.py."""
import unittest
import imp
from bottle import Response

# The validator isn't a module but with a little magic
# we can load it up as if it were in order to access
# the classes within
fh = open('iiif-presentation-validator.py', 'r')
try:
    val_mod = imp.load_module('ipv', fh, '.', ('py','r',imp.PY_SOURCE))
finally:
    fh.close()

class TestAll(unittest.TestCase):

    def test01_get_bottle_app(self):
        v = val_mod.Validator()
        self.assertTrue(v.get_bottle_app())
