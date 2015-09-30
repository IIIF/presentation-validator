#!/usr/bin/python
# -*- coding: utf-8 -*-

from factory import ManifestFactory
from lxml import etree
import os
import urllib
import json

url = "https://commons.wikimedia.org/w/api.php?action=featuredfeed&feed=potd&feedformat=atom&language=en"

fh = urllib.urlopen(url)
data = fh.read()
fh.close()

nss = {'atom': 'http://www.w3.org/2005/Atom'}

dom = etree.XML(data)
subs = dom.xpath('//atom:summary[@type="html"]/text()', namespaces=nss)

fac = ManifestFactory()
fac.set_base_metadata_uri("http://iiif-dev.localhost/prezi/mw/")
fac.set_base_image_uri("http://dlss-dev-azaroth.stanford.edu/services/iiif/")
fac.set_base_metadata_dir("/Users/azaroth/Dropbox/Rob/Web/iiif-dev/prezi/mw")
fac.set_iiif_image_info(2.0, 2)
fac.set_debug("error") # warn will warn for recommendations, by default

label = "Wikimedia Pictures of the Day"

mf = fac.manifest(ident="manifest", label=label)
mf.viewingHint = "individuals"
seq = mf.sequence(ident="normal", label="Normal Order")


c = 0
for s in subs:
	hdom = etree.HTML(s)

	title = hdom.xpath('//span')[0]
	title = etree.tostring(title)
	title = title.replace('&#160;', '')
	url = hdom.xpath('//img/@src')[0]

	url = url.replace('thumb/', '')
	f = url.find('/300px-')
	if f > -1:
		url = url[:f]

	cvs = seq.canvas(ident="canvas{0}".format(c), label=title)
	# Use quick submit image to IIIFifi
	fh = urllib.urlopen("http://dlss-dev-azaroth.stanford.edu/services/iiif/submit?url={0}".format(url))
	data = fh.read()
	fh.close()
	js = json.loads(data)
	imgurl = js['url']
	(server, imgid) = os.path.split(imgurl)
	cvs.set_image_annotation(imgid)
	c += 1

	print "{0}: {1} to {2}".format(title, url, imgid)

mf.toFile()
