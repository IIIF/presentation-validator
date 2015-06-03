
import urllib
from factory import ManifestFactory
import os, sys, re
from lxml import etree
import time
import json

try:
	from bsddb3 import db as bdb
except:
	from bsddb import db as bdb

OAINS = "http://www.openarchives.org/OAI/2.0/"
OAIDCNS = "http://www.openarchives.org/OAI/2.0/oai_dc/"
DCNS = "http://purl.org/dc/elements/1.1/"
ALLNS = {'o':OAINS, 'odc':OAIDCNS, 'dc':DCNS}

BASE_MD_URL = "http://dlss-dev-azaroth.stanford.edu/prezi/cdm"
BASE_IMG_URL = "http://dlss-dev-azaroth.stanford.edu/services/cdm"

# Note Well: MUST be version 6, and MUST have OAI enabled

# Known ContentDM servers
CDM_SERVERS = [ 'econtent.unm.edu' ]
#, 'digital.tcl.sc.edu', 'ccdl.libraries.claremont.edu', 'libcdm1.uncg.edu',
#				'digital-library.usma.edu', 'content.lib.utah.edu', 'dig.library.vcu.edu',
#				'images.ulib.csuohio.edu', 'photos.salemhistory.net', 'cslib.cdmhost.com',
#				'idahohistory.cdmhost.com', 'digitalmarquette.cdmhost.com', 'idahodocs.cdmhost.com',
#				'cplorg.cdmhost.com', 'bplonline.cdmhost.com', 'gettysburg.cdmhost.com',
#				'gvsu.cdmhost.com', 'gvsu.cdmhost.com', 'twudigital.cdmhost.com',
#				'cgsc.cdmhost.com', 'bellevueulibrary.cdmhost.com', 'maca.cdmhost.com',
#				'digitalcollections-wmich.cdmhost.com', 'digitalstatelibnc.cdmhost.com',
#				'digitalmetro.cdmhost.com', 'mtholyoke.cdmhost.com', 'oshkoshpub.cdmhost.com',
#				'smcm.cdmhost.com', 'trinity.cdmhost.com', 'ttclibrary.cdmhost.com',
#				'wcudigitalcollection.cdmhost.com']

SETS_TO_DO = ['dignews', 'Books', 'acpa', 'abqmuseum', 'chavezgraph', 'CobbMem', 'Manuscripts', 
				'navtrans', 'indaffairs', 'tucker', 'parkhurst', 'iaia']


def get_xml(url, retry=2):
	print "Getting: %s" % url
	sys.stdout.flush()

	try:
		fh = urllib.urlopen(url)
		data = fh.read()
		fh.close()
	except:
		if retry:
			time.sleep(5)
			return get_xml(url, retry-1)
		else:
			return None
	try:
		dom = etree.XML(data)	
		return dom
	except:
		return None


def get_json(url, retry=2):
	try:
		fh = urllib.urlopen(url)
		data = fh.read()
		fh.close()
	except:
		if retry:
			time.sleep(5)
			return get_json(url, retry-1)
		else:
			return {}
	try:
		js = json.loads(data)
		return js	
	except:
		raise
		return {}

def do_record(rec, rx, host, s, cxn, sequence, lastrec):
	deleted = rec.xpath('./o:header/@status', namespaces=ALLNS)
	if deleted:
		return
	format = rec.xpath('./o:metadata/odc:dc/dc:format/text()', namespaces=ALLNS)
	# Strip out non images
	skip = 0
	for f in format:
		if f.find('/') > -1 and (not f.startswith('image/') or f.endswith('/pdf')):
			skip = 1
			break
	if skip:
		return

	# request info to see if we're compound object (cpd)
	# if we are, then work backwards from current ID to find records for individual pages
	# Then reverse the order and call it a Manifest :)

	identifier = rec.xpath('./o:header/o:identifier/text()', namespaces=ALLNS)[0]
	idx = int(identifier[identifier.rfind('/')+1:])
	ajaxinfo = get_json('http://%s/utils/ajaxhelper/?action=1&CISOROOT=%s&CISOPTR=%s' % (host, s, idx))
	try:
		if not ajaxinfo['imageinfo'].has_key('type'):
			return
	except:
		print 'http://%s/utils/ajaxhelper/?action=1&CISOROOT=%s&CISOPTR=%s' % (host, s, idx)
		print ajaxinfo
		raise


	if ajaxinfo['imageinfo']['type'] == 'cpd':
		# Compound Object to process separately
		# Walk backwards through images until hit previous entry in OAI list
		# make a folder...
		print "--- Compound Object: %s" % idx
		sys.stdout.flush()
		if os.path.exists('%s/%s/manifest.json' % (s,idx)):
			return

		try:
			os.mkdir("%s/%s" % (s, idx))
		except:
			pass
		os.chdir("%s/%s" % (s, idx))
		if rx == 0:
			# Need to check last record of previous chunk
			if lastrec:
				previd = lastrec.xpath('./o:header/o:identifier/text()', namespaces=ALLNS)[0]
				start_image = int(previd[previd.rfind('/')+1:])+1
			else:
				start_image = 1
		else:
			prev = recs[rx-1]
			previd = prev.xpath('./o:header/o:identifier/text()', namespaces=ALLNS)[0]
			start_image = int(previd[previd.rfind('/')+1:])+1

		pages = []
		for imgid in range(start_image, idx):
			pinfo = {'id': imgid}
			# get H/W from ajax
			iajax = get_json('http://%s/utils/ajaxhelper/?action=1&CISOROOT=%s&CISOPTR=%s' % (host, s, imgid))
			if not iajax['imageinfo'].has_key('height'):
				continue
			pinfo['h'] = iajax['imageinfo']['height']
			pinfo['w'] = iajax['imageinfo']['width']
			if (int(pinfo['h']) == 0 or int(pinfo['w']) == 0):
				continue
			try:
				pinfo['title'] = iajax['imageinfo']['title']['0']
			except:
				pinfo['title'] = "Image %s" % imgid
			cxn.put("%s::%s::%s" % (host, s, imgid), "%s,%s" % (pinfo['w'], pinfo['h']))
			pages.append(pinfo)

		if not pages:
			# back to host directory
			os.chdir('../..')
			return
		title = rec.xpath('./o:metadata/odc:dc/dc:title/text()', namespaces=ALLNS)
		creator = rec.xpath('./o:metadata/odc:dc/dc:creator/text()', namespaces=ALLNS)
		date = rec.xpath('./o:metadata/odc:dc/dc:date/text()', namespaces=ALLNS)
		description = rec.xpath('./o:metadata/odc:dc/dc:description/text()', namespaces=ALLNS)
		language = rec.xpath('./o:metadata/odc:dc/dc:language/text()', namespaces=ALLNS)

		# reinstantiate factory for subdir. not great but ...

		cfac = ManifestFactory()
		cfac.set_base_metadata_uri(BASE_MD_URL + "/%s/%s/%s/" % (host, s, idx))
		cfac.set_base_image_uri(BASE_IMG_URL + "/%s/%s/" % (host, s))
		cfac.set_base_metadata_dir(os.getcwd())
		cfac.set_iiif_image_info("2.0", "1")
		fac.set_debug('error')


		cmanifest = cfac.manifest(label=title[0])

		try:
			cmanifest.set_metadata({"Creator": creator[0]})
		except:
			pass
		try:
			cmanifest.set_metadata({"Date": date[0]})
		except:
			pass
		try:
			cmanifest.set_metadata({"Language": language[0]})
		except:
			pass
		try:
			cmanifest.description = description[0]
		except:
			pass
		cmanifest.viewingHint = "paged"
		cseq = cmanifest.sequence()
		for p in pages:
			cvs = cseq.canvas(ident="p%s" % p['id'], label=p['title'])
			cvs.set_hw(int(p['h']), int(p['w']))
			anno = cvs.annotation()
			img = anno.image(str(p['id']), iiif=True)
			img.height = p['h']
			img.width = p['w']

		try:
			cmanifest.toFile(compact=False)
		except:
			print "FAILED TO WRITE %s/%s/manifest.json" % (s, idx)
		# back to host directory
		os.chdir('../..')
	else:
		# We're just a collection of images

		h = ajaxinfo['imageinfo']['height']
		w = ajaxinfo['imageinfo']['width']
		if int(h) == 0 or int(w) == 0:
			return
		ttl = ajaxinfo['imageinfo']['title']['0']
		cxn.put("%s::%s::%s" % (host, s, idx), "%s,%s" % (w, h))

		cvs = sequence.canvas(ident="p%s" % idx, label=ttl)
		cvs.set_hw(int(h), int(w))
		anno = cvs.annotation()
		img = anno.image(str(idx), iiif=True)
		img.height = h
		img.width = w



# CRAWL....

for host in CDM_SERVERS:
	try:
		os.mkdir(host)
	except:
		# file exists
		pass
	os.chdir(host)

	# Make a per host bdb for caching image info
	cxn = bdb.DB()            
	cxn.set_cachesize(0, 1024*1024*8, 1)
	ofn = "img_cache.bdb"
	if os.path.exists(ofn):
		cxn.open(ofn)
	else:
		cxn.open(ofn, dbtype=bdb.DB_BTREE, flags = bdb.DB_CREATE, mode=0660)

	dom = get_xml('http://%s/oai/oai.php?verb=ListSets' % host)

	sets = []

	setsdom = dom.xpath('/o:OAI-PMH/o:ListSets/o:set', namespaces=ALLNS)
	for s in setsdom:
		sid = s.xpath('./o:setSpec/text()', namespaces=ALLNS)[0]
		sname = s.xpath('./o:setName/text()', namespaces=ALLNS)[0]
		try:
			sdesc = s.xpath('./o:setDescription/odc:dc/dc:description/text()', namespaces=ALLNS)[0]
		except:
			sdesc = ""
		sets.append({'id': sid, 'name': sname, 'desc':sdesc})

	rt = dom.xpath('/o:OAI-PMH/o:ListSets/o:resumptionToken/text()', namespaces=ALLNS)
	while rt:
		dom = get_xml('http://%s/oai/oai.php?verb=ListSets&resumptionToken=%s' % (host, rt[0]))
		setsdom = dom.xpath('/o:OAI-PMH/o:ListSets/o:set', namespaces=ALLNS)
		for s in setsdom:
			sid = s.xpath('./o:setSpec/text()', namespaces=ALLNS)[0]
			sname = s.xpath('./o:setName/text()', namespaces=ALLNS)[0]
			try:
				sdesc = s.xpath('./o:setDescription/odc:dc/dc:description/text()', namespaces=ALLNS)[0]
			except:
				sdesc = ""
			sets.append({'id': sid, 'name': sname, 'desc':sdesc})
		rt = dom.xpath('/o:OAI-PMH/o:ListSets/o:resumptionToken/text()', namespaces=ALLNS)	

	# Found all of the sets, walk through them and gather records.
	sets.sort(key=lambda x: x['id'])

	for sinfo in sets:

		s = sinfo['id']

		if SETS_TO_DO and not s in SETS_TO_DO:
			print "skipping %s / %s" % (s , sinfo['name'])
			continue

		try:
			print "Processing Set: %s" % sinfo['name']
		except:
			print "Processing Set: %s" % s
		sys.stdout.flush()
		if os.path.exists(s):
			continue
		os.mkdir(s)

		fac = ManifestFactory()
		fac.set_base_metadata_uri(BASE_MD_URL + "/%s/%s/" % (host, s))
		fac.set_base_metadata_dir(os.path.join(os.getcwd(), s))
		fac.set_base_image_uri(BASE_IMG_URL + "/%s/%s/" % (host, s))
		fac.set_iiif_image_info("2.0", "1")
		fac.set_debug('error')

		manifest = fac.manifest(label=sinfo['name'])
		if sinfo['desc']:
			manifest.description = str(sinfo['desc'])
		manifest.attribution = "Converted from http://%s/" % host
		manifest.viewingHint = "individuals"

		sequence = manifest.sequence()
		dom = get_xml('http://%s/oai/oai.php?verb=ListRecords&set=%s&metadataPrefix=oai_dc' % (host, s))
		recs = dom.xpath('/o:OAI-PMH/o:ListRecords/o:record', namespaces=ALLNS)
		lastrec = None
		for rx in range(len(recs)):
			rec = recs[rx]
			do_record(rec, rx, host, s, cxn, sequence, lastrec)
		rt = dom.xpath('/o:OAI-PMH/o:ListRecords/o:resumptionToken/text()', namespaces=ALLNS)
		while rt:
			lastrec = recs[-1]
			dom = get_xml('http://%s/oai/oai.php?verb=ListRecords&resumptionToken=%s' % (host, rt[0]))
			recs = dom.xpath('/o:OAI-PMH/o:ListRecords/o:record', namespaces=ALLNS)
			for rx in range(len(recs)):
				rec = recs[rx]
				do_record(rec, rx, host, s, cxn, sequence, lastrec)
			rt = dom.xpath('/o:OAI-PMH/o:ListRecords/o:resumptionToken/text()', namespaces=ALLNS)

		# write collection manifest
		if sequence.canvases:
			try:
				manifest.toFile(compact=False)
			except:
				print "FAILED TO WRITE %s/manifest.json" % s

		# make sure we're synced
		cxn.sync()

	cxn.close()
	os.chdir('..')
	break

