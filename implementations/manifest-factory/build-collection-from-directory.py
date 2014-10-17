
from loader import ManifestReader
from factory import ManifestFactory
import os

where = "/Users/azaroth/Dropbox/Rob/Web/iiif-dev/prezi"

fac = ManifestFactory()
fac.set_base_metadata_uri("http://iiif-dev.localhost/prezi/")
fac.set_base_metadata_dir("/Users/azaroth/Dropbox/Rob/Web/iiif-dev/prezi/")

c = fac.collection()
c.label = "Museum Objects"

dirs = os.listdir(where)
for d in dirs:
	d = os.path.join(where, d)
	fn = os.path.join(d, 'manifest.json')
	if os.path.exists(fn):
		fh = file(fn)
		data = fh.read()
		fh.close()
		mr = ManifestReader(data)	
		mfst = mr.read()
		print "Found: %s" % mfst.label
		c.add_manifest(mfst)

c.toFile(compact=False)


