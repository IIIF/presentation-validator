# BL Flickr TSV + JSON to IIIF Metadata
# Data available here: https://github.com/BL-Labs/imagedirectory

import sys, os, re
import glob
import ljson
from factory import ManifestFactory

fac = ManifestFactory()
fac.set_base_metadata_uri("https://github.com/BL-Labs/imagedirectory/iiif")
fac.set_base_metadata_dir('/Users/azaroth/Development/bl/imagedirectory/iiif')

fh = file('book_metadata.json')
data = fh.read()
fh.close()
books = ljson.loads(data)

# volume / Publisher / Title / Author / ? / pub place / book id / book ARK / flickr_url / 
#          image_idx / page / flickr_id / f_small / f_s_height / f_s_width / medium / large / original


# Can be images from the same book in multiple TSV files, as based on image size so build in parallel and sort
manifests = {}

files = glob.glob("*.tsv")
files.sort()
for f in files:
	fh = file(f)
	data = fh.read()
	fh.close()
	lines = data.split('\r\n')
	keys = lines[0].split('\t')
	keys = [x.lower() for x in keys]
	lines = lines[1:]
	for l in lines:
		if l:
			fields = l.split('\t')
			linfo = dict(zip(keys, fields))
			bkid = linfo['book_identifier']
			bookinfo = books[bkid]

			try:
				manifest = manifests[bkid]
				seq = manifest.sequences[0]
			except:
				manifest = fac.manifest(bkid, label=linfo['title'])
				manifest.set_metadata({'Author': linfo['first_author'], 'Place of Publication': linfo['pubplace'],
					'Publisher': linfo['publisher'], "Date": linfo['date'], "Shelfmarks" : bookinfo['shelfmarks'],
					'Issuance': bookinfo['issuance']})
				manifest.attribution = "British Library"
				manifest.seeAlso = bookinfo['flickr_url_to_book_images'] 
				seq = manifest.sequence("s1", label="Regular Order")
				manifests[bkid] = manifest

			cvs = seq.canvas(linfo['flickr_id'], label="p. %03d (detail)" % int(linfo['page']))
			anno = cvs.annotation("%s-image" % linfo['flickr_id'])

			imgs = []
			if linfo['flickr_original_source']:
				orig = fac.image(linfo['flickr_original_source'])
				orig.set_hw(int(linfo['flickr_original_height']), int(linfo['flickr_original_width']))
				imgs.append(orig)

			if linfo['flickr_large_source']:
				large = fac.image(linfo['flickr_large_source'])
				large.set_hw(int(linfo['flickr_large_height']), int(linfo['flickr_large_width']))
				imgs.append(large)

			if linfo['flickr_medium_source']:
				medium = fac.image(linfo['flickr_medium_source'])
				medium.set_hw(int(linfo['flickr_medium_height']), int(linfo['flickr_medium_width']))
				imgs.append(medium)

			if linfo['flickr_small_source']:
				small = fac.image(linfo['flickr_small_source'])
				small.set_hw(int(linfo['flickr_small_height']), int(linfo['flickr_small_width']))
				imgs.append(small)		

			for x in imgs:
				x.format = "image/jpeg"

			if len(imgs) == 1:
				anno.resource = imgs[0]
			elif len(imgs) > 1:
				anno.choice(imgs[0], imgs[1:])
			cvs.set_hw(imgs[0].height, imgs[0].width)

# Sort the Sequences, hence 03d in label for sortability
# then serialize
for mf in manifests.values():
	mf.sequences[0].canvases.sort(key= lambda x: x.label)
	mf.toFile()	



