
import json
from factory import ManifestFactory
import urllib
import os, sys

baseq = "http://data.fitzmuseum.cam.ac.uk/api/?size=1000&query="
q = "Marlay%20AND%20cutting%20AND%20Category:illuminated*"

destdir = "/path/to/images/fitzwilliam"

fac = ManifestFactory()
fac.set_base_image_uri("http://iiif-dev.localhost/services/2.0")
fac.set_iiif_image_info(version="2.0")
basemd = "http://localhost/prezi/fitz/"
basedir = "/path/to/htdocs/prezi/fitz/" 
fac.set_base_metadata_uri(basemd)
fac.set_base_metadata_dir(basedir)

fh = urllib.urlopen(baseq+q)
data = fh.read()
fh.close()
results = json.loads(data)

mfst = fac.manifest(label="Marlay Cuttings")
seq = mfst.sequence()

for res in results['results']:
	if not res.has_key('image'):
		continue
	ident = res.get('identifier')
	name = res.get('Name')
	title = res.get('Title', name)
	img = res['image']['thumbnailURI']

	# And grab the thumbnail, such as it is...
	dest = "fitz_%s.jpg" % ident
	destfn = os.path.join(destdir, dest)
	if not os.path.exists(destfn):
		print "Fetching %s: %s" % (title, img)
		fh = urllib.urlopen(img)
		data = fh.read()
		fh.close()
		if data:
			fh = file(os.path.join(destdir, dest), 'w')
			fh.write(data)
			fh.close()

	cvs = seq.canvas(ident=ident, label=title)

	anno = cvs.annotation()
	image = anno.image(dest[:-4], iiif=True)
	image.set_hw_from_iiif()
	cvs.set_hw(image.height, image.width) 

mfst.toFile(compact=False)
