
from lxml import etree
import urllib
import os

CACHEDIR = "./cache"

namespaces = {
	"mets":"http://www.loc.gov/METS/",
	"premis":"info:lc/xmlns/premis-v2",
	"dc":"http://purl.org/dc/elements/1.1/", 
	"fedora-model":"info:fedora/fedora-system:def/model#",
	"fedora":"info:fedora/fedora-system:def/relations-external#",
	"nlw":"http://dev.llgc.org.uk/digitisation/identifiers/",
	"oai":"http://www.openarchives.org/OAI/2.0/",
	"rdf":"http://www.w3.org/1999/02/22-rdf-syntax-ns#",
	"oai_dc":"http://www.openarchives.org/OAI/2.0/oai_dc/",
	"xsi":"http://www.w3.org/2001/XMLSchema-instance",
	"mix":"http://www.loc.gov/mix/v20",
	"xlink":"http://www.w3.org/1999/xlink", 
	"mods":"http://www.loc.gov/mods/v3",
	"rights":"http://cosimo.stanford.edu/sdr/metsrights/"}

from factory import ManifestFactory

fac = ManifestFactory()
fac.set_base_image_uri("http://dams.llgc.org.uk/iiif/image/")
fac.set_iiif_image_info(version="1.1", lvl="1")
fac.set_base_metadata_dir('/path/to/data')
fac.set_base_metadata_uri("http://showcase.iiif.io/shims/wales/potter/")
fac.set_debug('error')


def xpath(dom, path):
	return dom.xpath(path, namespaces=namespaces)

def fetch(url, type="XML", retry=0):

	# Cache everything
	fn = os.path.split(url)[1]
	cached = os.path.join(CACHEDIR, fn)
	if os.path.exists(cached):
		fh = file(cached)
		data = fh.read()
		fh.close()
	else:
		fh = urllib.urlopen(url)
		data = fh.read()
		fh.close()
		fh = file(cached, 'w')
		fh.write(data)
		fh.close()

	if type == "XML":
		try:
			data = etree.XML(data)
		except:
			if not retry:
				return fetch(url, type="XML", retry=1)
			else:
				raise
	return data


# Fetch top level METS
paperid = "3100020"
paperMets = "http://dams.llgc.org.uk/behaviour/llgc-id:%s/fedora-sdef:mets/mets" % paperid
dom = fetch(paperMets)

# Extract metadata
label = xpath(dom, "/mets:mets/@LABEL")[0]
title = xpath(dom, '/mets:mets/mets:dmdSec[@ID="dmdSec_MODS"]/mets:mdWrap[@MDTYPE="MODS"]/mets:xmlData/mods:mods/mods:titleInfo/mods:title/text()')[0]
uri = xpath(dom, '/mets:mets/mets:dmdSec[@ID="dmdSec_MODS"]/mets:mdWrap[@MDTYPE="MODS"]/mets:xmlData/mods:mods/mods:identifier[@type="uri"]/text()')[0]

# Fetch and parse rightsMD
rmduri = xpath(dom, '/mets:mets/mets:amdSec/mets:rightsMD/mets:mdRef[@OTHERMDTYPE="METSRightsMD"]/@xlink:href')[0]
rmdom = fetch(rmduri)
rdecl_cy = xpath(rmdom, '/rights:RightsDeclarationMD/rights:RightsDeclaration[@xml:lang="cy"]/text()')[0]
rdecl_en = xpath(rmdom, '/rights:RightsDeclarationMD/rights:RightsDeclaration[@xml:lang="en"]/text()')[0]

# SourceMD
srcDom = xpath(dom, '/mets:mets/mets:amdSec/mets:sourceMD/mets:mdWrap[@MDTYPE="MODS"]/mets:xmlData/mods:mods')[0]
title2 = xpath(srcDom, './mods:titleInfo/mods:title/text()')[0]
genre = xpath(srcDom, './mods:genre[@authority=""]/text()')[0]
place = xpath(srcDom, './mods:originInfo/mods:place/mods:placeTerm[@type="text"]/text()')[0]
publisher = xpath(srcDom, './mods:originInfo/mods:publisher/text()')[0]
freq = xpath(srcDom, './mods:originInfo/mods:frequency/text()')[0]
lang = xpath(srcDom, './mods:language/mods:languageTerm/text()')[0]
desc_cy = xpath(srcDom, './mods:abstract[@lang="cy"]/text()')[0]
desc_en = xpath(srcDom, './mods:abstract[@lang="en"]/text()')[0]

subjects = xpath(srcDom, './mods:subject')
subjs = []
for subj in subjects:
	st = xpath(subj, './/text()')
	nst = []
	for t in st:
		strp = t.strip()
		if strp:
			nst.append(strp)
	subjs.append(', '.join(nst))

relDom = xpath(srcDom, './mods:relatedItem')[0]
reltyp = xpath(relDom, './@type')[0]
reltxt = xpath(relDom, './mods:titleInfo/mods:title/text()')

mdhash = {"Identifier": uri, "Genre" : genre, "Place of Publication": place, 
		  "Publisher": publisher, "Frequency": freq, "Language": lang, 
		  reltyp : reltxt}

# Make the top level collection
coll = fac.collection(ident="top", label=label)
coll.set_metadata(mdhash)
coll.set_metadata({"label": "Rights", "value": [{"en": rdecl_en, "cy": rdecl_cy}]})
coll.set_description({"en": desc_en, "cy": desc_cy})
coll.set_metadata({"Subject" : subjs})

# And the structmap for issues
issues = xpath(dom, '/mets:mets/mets:structMap//mets:div[@TYPE="ISSUE"]/mets:mptr/@xlink:href')

# Make collection per year
yearcolls = {}

for issurl in issues:
	dom = fetch(issurl)

	date = xpath(dom, '/mets:mets/mets:dmdSec[@ID="dmdSec_MODS"]/mets:mdWrap/mets:xmlData/mods:mods/mods:part/mods:date/text()')[0]

	year = date[:4]
	try:
		ycoll = yearcolls[year]
	except:
		ycoll = coll.collection(year, label = "%s (%s)" % (label, date))
		ycoll.set_metadata(mdhash)
		yearcolls[year] = ycoll

	manifest = ycoll.manifest(date, label="%s (%s)" % (label, date))
	manifest.set_metadata(mdhash)

	articles = xpath(dom, '/mets:mets/mets:dmdSec[./mets:mdWrap/mets:xmlData/mods:mods/mods:genre/text()="article"]')
	articleHash = {}
	for art in articles:
		aid = xpath(art, "./@ID")[0]
		amods = xpath(art, "./mets:mdWrap/mets:xmlData/mods:mods")[0]
		atype = xpath(amods, './mods:genre[@type="articleCategory"]/text()')[0]
		auri = xpath(amods, './mods:identifier[@type="uri"]/text()')[0]
		try:
			atitle = xpath(amods, './mods:titleInfo/mods:title/text()')[0]
		except:
			atitle = ''
		try:
			adesc = xpath(amods, './mods:abstract/text()')[0]
		except:
			adesc = ''
		articleHash[aid] = {'type': atype, 'uri': auri, 'title': atitle, 'desc': adesc}

	imageNodes = xpath(dom, '/mets:mets/mets:fileSec/mets:fileGrp[@USE="archive"]/mets:file')
	# strip off -10 and lose the non-existant handle
	images = {}
	invImages = {}
	for img in imageNodes:
		imgHdl = xpath(img, './mets:FLocat/@xlink:href')[0]
		imgId = xpath(img, '@ID')[0]
		imgfn = os.path.split(imgHdl)[1]
		images[imgId] = imgfn[:-3]
		invImages[imgfn[:-3]] = imgId

	altoNodes = xpath(dom,  '/mets:mets/mets:fileSec/mets:fileGrp[@USE="ALTO"]/mets:file')
	altos = {}
	for alt in altoNodes:
		altoUri = xpath(alt, './mets:FLocat/@xlink:href')[0]
		altoId = xpath(alt, '@ID')[0]		
		altos[altoId] = altoUri

	# blind faith that the order in the file is the same as the ORDER attribute
	# because NLW are not idiotic or malicious :)
	seqmap = xpath(dom, '/mets:mets/mets:structMap[@TYPE="physical"]/mets:div[@TYPE="ISSUE"]/mets:div/mets:mptr/@xlink:href')
	seqmap = [os.path.split(x)[1][:-2] for x in seqmap]

	rangenodes = xpath(dom, '/mets:mets/mets:structMap[@TYPE="logical"]/mets:div/mets:div[@TYPE="article"]')
	ranges = []
	imageAltoMap = {}
	for rnode in rangenodes:
		dmid = xpath(rnode, "./@DMDID")[0]
		zones = xpath(rnode, './mets:div/mets:div[@TYPE="article-zone"]')
		bits = []
		for z in zones:
			zimgid = xpath(z, './mets:fptr/mets:area[@SHAPE="RECT"]/@FILEID')[0]
			zcoords = xpath(z, './mets:fptr/mets:area[@SHAPE="RECT"]/@COORDS')[0]
			ztxtid = xpath(z, './mets:fptr/mets:area[@BETYPE="IDREF"]/@FILEID')[0]
			ztxtfrag = xpath(z, './mets:fptr/mets:area[@BETYPE="IDREF"]/@BEGIN')[0]
			bits.append({'image': (zimgid, zcoords), 'text': (ztxtid, ztxtfrag)})
			# Not explicit elsewhere just repeatedly add here
			imageAltoMap[zimgid] = ztxtid
		ranges.append(bits)

	# Only thing in page level METS is the page label, which (almost certainly) is just the order number

	seq = manifest.sequence()
	x = 1
	for cvsid in seqmap:
		cvs = seq.canvas(cvsid, label="%s" % x)

		# hard coded but fetching ALTO for the size is very very slow
		ph = 24045 / 3
		pw = 14550 / 3

		cvs.set_hw(ph, pw)
		anno = cvs.annotation()
		image = anno.image(ident=cvsid, iiif=True)
		annol = cvs.annotationList(ident="%s" % cvsid)        
		# AnnotationList is built on demand by list_shim.py

		x += 1
	manifest.toFile(compact=True)

for yc in yearcolls.values():
	yc.toFile(compact=True)
coll.toFile(compact=True)
