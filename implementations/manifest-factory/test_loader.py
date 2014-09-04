from factory import DataError, StructuralError, RequirementError, ConfigurationError, PresentationError
from loader import SerializationError, ManifestReader

import urllib, os, sys
import difflib
import json


class TestError(PresentationError):
	pass

def print_warnings(reader):
	warns = reader.get_warnings()
	if warns:
		for m in warns:
			print m[:-1]	

def do_test(data, failmsg, excexp):
	debug_tests = 0
	reader = ManifestReader(data)
	if excexp == None:
		# Should pass
		try:
			what = reader.read()
			js = what.toJSON()
			print_warnings(reader)
			return 1
		except Exception, e:		
			print_warnings(reader)
			if debug_tests:
				print "%s:  %s" % (e.__class__.__name__, e)
			raise TestError(failmsg)
	else:
		try:
			what = reader.read()
			js = what.toJSON()
			if debug_tests:
				print "Loaded okay, should have failed"
				print json.dumps(js, sort_keys=True, indent=2)
			print_warnings(reader)
			raise TestError(failmsg)
		except excexp, e:
			if debug_tests:
				print "%s caused by %r for test: '%s'" % (e.__class__.__name__, e.resource, failmsg)
			print_warnings(reader)
			return 1
		except:
			raise


errorList = [SerializationError,SerializationError,SerializationError, SerializationError,
SerializationError, RequirementError, StructuralError, ConfigurationError, ConfigurationError,
RequirementError, DataError, StructuralError, StructuralError,StructuralError,StructuralError,
StructuralError,StructuralError,StructuralError,StructuralError,StructuralError,StructuralError,
StructuralError, RequirementError, ConfigurationError, RequirementError, DataError, RequirementError,
DataError, RequirementError, DataError, StructuralError, StructuralError, StructuralError,
RequirementError, DataError, StructuralError, StructuralError, StructuralError, StructuralError,
RequirementError, StructuralError, RequirementError, ConfigurationError, DataError, DataError, 
DataError, DataError, DataError, DataError, DataError, DataError, RequirementError]

errorMap = {}
for x in range(len(errorList)):
	errorMap["http://iiif.io/api/presentation/2.0/example/errors/%s/manifest.json" % x] = errorList[x]


HOMENAME = "users" if sys.platform == "darwin" else "home"



def test_remote():
	urls = [
	 #"http://dms-data.stanford.edu/data/manifests/Walters/qm670kv1873/manifest.json",
	 #"http://manifests.ydc2.yale.edu/manifest/Admont23.json",
	 #"http://oculus-dev.lib.harvard.edu/manifests/drs:5981093",
	 #"http://iiif-dev.bodleian.ox.ac.uk/metadata/bib_germ_1485_d1/bib_germ_1485_d1.json",
	 #"http://iiif-dev.bodleian.ox.ac.uk/metadata/ms_auct_t_inf_2_1/ms_auct_t_inf_2_1.json",
	 #"http://demos.biblissima-condorcet.fr/iiif/metadata/ark:/12148/btv1b84473026/manifest.json",
	 #"http://demos.biblissima-condorcet.fr/iiif/metadata/ark:/12148/btv1b84473026/manifest-ranges.json",
	 #"http://demos.biblissima-condorcet.fr/mirador/data/add_ms_10289_edited_8v-9r.json",
	 #"http://demos.biblissima-condorcet.fr/iiif/metadata/ark:/12148/btv1b8438674r/manifest.json",
	 #"http://demos.biblissima-condorcet.fr/iiif/metadata/BVH/B410186201_LI03/manifest.json"
	 #"http://sanddragon.bl.uk/IIIFMetadataService/add_ms_10289.json"
	 #"http://sr-svx-93.unifr.ch/metadata/iiif/bbb-0218/manifest.json"
	 # "http://www.shared-canvas.org/impl/demo1d/res/manifest.json"
	]
	for u in urls:
		fh = urllib.urlopen(u)
		data = fh.read()
		fh.close()
		try:
			print "------"
			print u
			reader = ManifestReader(data)
			nmfst = reader.read()
			js = nmfst.toJSON()
		except Exception, e:
			print "   => %s: %s" % (e.__class__.__name__, e)

def test_fixtures():
	top = '/%s/azaroth/Dropbox/Rob/Development/iiif/iiif.io/source/api/presentation/2.0/example/fixtures/collection.json' % HOMENAME
	fh = file(top)
	data = fh.read()
	fh.close()

	reader = ManifestReader(data)
	ncoll = reader.read()
	# And walk the manifests
	mfsts = []
	for manifest in ncoll.manifests:
		mfid = manifest.id
		fn = mfid.replace('http://iiif.io/', '/%s/azaroth/Dropbox/Rob/Development/iiif/iiif.io/source/' % HOMENAME)
		fh = file(fn)
		data = fh.read()
		fh.close()
		print "Manifest: %s" % mfid 
		reader = ManifestReader(data)
		nman = reader.read()
		data2 = nman.toString(compact=False)
		if len(data) != len(data2):
			print mfid
			print "in: %s  out: %s" % (len(data), len(data2))
			print "- is in, + is out"
			for x in difflib.unified_diff(data.split('\n'), data2.split('\n')):
				print x
			raise TestError("Did not get everything!")
			# print "~~~~~~~~~"
		mfsts.append(nman)


def test_errors():
	top = '/%s/azaroth/Dropbox/Rob/Development/iiif/iiif.io/source/api/presentation/2.0/example/errors/collection.json' % HOMENAME
	fh = file(top)
	data = fh.read()
	fh.close()

	reader = ManifestReader(data)
	ncoll = reader.read()
	# And walk the manifests
	mfsts = []

	passes = 0

	for manifest in ncoll.manifests:
		mfid = manifest.id
		fn = mfid.replace('http://iiif.io/', '/%s/azaroth/Dropbox/Rob/Development/iiif/iiif.io/source/' % HOMENAME)
		fh = file(fn)
		data = fh.read()
		fh.close()
		try:
			passes += do_test(data, manifest.label, errorMap[mfid])
		except TestError, e:
			print "Failed for: %s" % manifest.label
		except:
			raise	

