from lxml import etree
import urllib
import os

from bottle import Bottle, route, run, request, response, abort, error

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

	# Don't cache here, only the results
	fh = urllib.urlopen(url)
	data = fh.read()
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


class AnnoListShim(object):

	def do_annoList(self, lid):

		# check cache

		cached = os.path.join('/path/to/data/list', "%s.json" % lid)
		if os.path.exists(cached):
			fh = file(cached)
			out = fh.read()
			fh.close()
		else:
			altoUrl = "http://hdl.handle.net/10107/%s-15" % lid
			adom = fetch(altoUrl)
			xmlns = {'a' : 'http://www.loc.gov/standards/alto/ns-v2#'}
			# might be header not a printspace, and some number of composedblocks
			try:
				lines = adom.xpath('/a:alto/a:Layout/a:Page//a:TextBlock/a:TextLine', namespaces=xmlns)
				page = adom.xpath('/a:alto/a:Layout/a:Page', namespaces=xmlns)[0]
			except:
				# uhoh
				raise

			cvsid = "http://showcase.iiif.io/shims/wales/potter/canvas/%s.json" % lid
			ratio = 3.0
			annol = fac.annotationList(ident="%s" % lid)        
			for l in lines:
				text = []
				x = int(int(l.attrib['HPOS']) / ratio)
				y = int(int(l.attrib['VPOS']) / ratio)
				h = int(int(l.attrib['HEIGHT']) / ratio)
				w = int(int(l.attrib['WIDTH']) / ratio)
				for s in l:
					if s.tag == '{%s}String' % xmlns['a']:
						text.append(s.attrib['CONTENT'])
					elif s.tag == '{%s}SP' % xmlns['a']:
						text.append(' ')
				txt = ''.join(text)
				txt = txt.replace('"', "&quot;")

				anno = annol.annotation()
				anno.text(txt)
				anno.on = cvsid + "#xywh=%s,%s,%s,%s" % (x,y,w,h)
			out = annol.toFile(compact=True)

		response['content_type'] = "application/json"
		return out

	def dispatch_views(self):
		self.app.route("/<lid>.json", "GET", self.do_annoList)

	def after_request(self):
		"""A bottle hook to add CORS headers"""
		methods = 'GET, HEAD, OPTIONS'
		headers = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
		response.headers['Access-Control-Allow-Origin'] = '*'
		response.headers['Access-Control-Allow-Methods'] = methods
		response.headers['Access-Control-Allow-Headers'] = headers
		response.headers['Allow'] = methods


	def error_msg(self, param, msg, status):
		abort(status, "Error with %s: %s" % (param, msg))

	def get_bottle_app(self):
		"""Returns bottle instance"""
		self.app = Bottle()
		self.dispatch_views()
		self.app.hook('after_request')(self.after_request)
		return self.app


	def run(self, *args, **kwargs):
		"""Shortcut method for running"""
		kwargs.setdefault("app", self.get_bottle_app())
		run(*args, **kwargs)


def apache():
    # Apache takes care of the prefix
    v = AnnoListShim();
    return v.get_bottle_app()

application = apache()
