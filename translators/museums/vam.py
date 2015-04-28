
import os, sys
import urllib
import json
from factory import ManifestFactory

baseq = "http://www.vam.ac.uk/api/json/museumobject/search?images=1&"
baseo = "http://www.vam.ac.uk/api/json/museumobject/" # + O 123456
baseimg = "http://media.vam.ac.uk/media/thira/collection_images/" # + pid[:6] + / + pid .jpg
destdir = "/path/to/images/vam"

fac = ManifestFactory()
fac.set_base_image_uri("http://localhost/iiif")
fac.set_iiif_image_info(version="2.0")
basemd = "http://localhost/prezi/vam/"
basedir = "/path/to/htdocs/prezi/vam/" 
fac.set_base_metadata_uri(basemd)
fac.set_base_metadata_dir(basedir)

# before=date&after=date&q=term
# offset=n

q1 = baseq + "before=1200&after=1100&q=manuscript"
# 126 objects


def fetch(q, offset=0):
	if offset:
		q += "&offset=%s" % offset
	fh = urllib.urlopen(q)
	data = fh.read()
	fh.close()
	js = json.loads(data)
	return js


def fetch_all(q, name):
	cachefn = 'cache/%s.json' % name
	if os.path.exists(cachefn):
		fh = file(cachefn)
		data = fh.read()
		fh.close()
		return json.loads(data)
	all_recs = []
	total=1
	while len(all_recs) < total:
		res = fetch(q, len(all_recs))
		total = res['meta']['result_count']
		all_recs.extend(res['records'])

	fh = file(cachefn, 'w')
	fh.write(json.dumps(all_recs))
	fh.close()
	return all_recs
	
def fetch_content(q, name):
	recs = fetch_all(q, name)
	pairs = []
	for rec in recs:
		# Metadata
		objn = rec['fields']['object_number']
		if not os.path.exists('cache/%s.json' % objn):
			mduri = baseo + objn
			dest = "cache/%s.json" % objn
			fh = urllib.urlopen(mduri)
			data = fh.read()
			fh.close()
			fh = file(dest, 'w')
			fh.write(data)
			fh.close()

		# Image
		imgid = rec['fields']['primary_image_id']
		imguri = baseimg + imgid[:6] + '/' + imgid + '.jpg'
		limgid = 'vam_' + imgid + '.jpg'
		destimg = os.path.join(destdir, limgid)
		if not os.path.exists(destimg):
			fh = urllib.urlopen(imguri)
			data = fh.read()
			fh.close()
			if data:
				fh = file(destimg, 'w')
				fh.write(data)
				fh.close()

		pairs.append((objn, limgid[:-4]))
	return pairs

pairs = fetch_content(q1, 'q1')

# Make a manifest
mfst = fac.manifest(label="12th Century Manuscripts")
mfst.attribution = "Victoria and Albert Museum"
seq = mfst.sequence()

# Some objects have many images in image_set, skip if >2 and make new object
for (objn, imgid) in pairs:
	# build per canvas metadata
	fh = file('cache/%s.json' % objn)
	data = fh.read()
	fh.close()
	rec = json.loads(data)[0]
	fields = rec['fields']

	if len(fields['image_set']) > 2:
		continue

	objectType = fields.get('object').lower()
	if objectType.find('illuminated') < 0 and objectType.find('manuscript') < 0:
		print "Skipping non MS: %s" % objectType
		continue

	cvs = seq.canvas(ident=objn)

	# Get a label
	label = fields.get('title')
	if not label:
		label = fields.get('label', '')
		label = label.split('\n')[0]
	if not label:
		label = fields.get('object')
	if not label:
		label = fields.get('slug', '')
		label = label.replace("-", ' ')
		label = label.title()
	if not label:
		label = fields.get('descriptive_line')
	cvs.label = label


	# Get descriptions
	phys = fields.get('physical_description')
	label = fields.get('label')
	dline  = fields.get('descriptive_line')
	pubdesc = fields.get('public_access_description')
	hist = fields.get('history_note')
	prod = fields.get('production_note')
	hist_ctxt = fields.get('historical_context_note')
	bib = fields.get('bibliography')

	# Create metadata here...


	# add image to canvas
	anno = cvs.annotation()
	image = anno.image(imgid, iiif=True)
	image.set_hw_from_iiif()
	cvs.set_hw(image.height, image.width) 

mfst.toFile(compact=False)




