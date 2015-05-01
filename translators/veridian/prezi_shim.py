

import json

from bottle import Bottle, route, run, request, response, abort, error

import os, sys
import factory
from lxml import etree

import uuid
import urllib, urllib2, urlparse

from factory import ManifestFactory

fac = ManifestFactory()
fac.set_base_image_uri("http://showcase.iiif.io/shims/veridian/image")
fac.set_iiif_image_info(version="2.0", lvl="1")
fac.set_base_metadata_dir('/tmp/')
fac.set_base_metadata_uri("http://showcase.iiif.io/shims/veridian/prezi/")
fac.set_debug('error')

PFX = ""
INFO_CACHE = {}
CACHEDIR = '/tmp/'
VSERVER = "http://cdnc.ucr.edu/cgi-bin/cdnc"


class ManifestShim(object):

    def __init__(self):
        pass

    def fetch(self, url, format="json"):

        try:
            fh = urllib.urlopen(url)
            data = fh.read()
            fh.close()
            if format == "json":
                info = json.loads(data)
            elif format == "xml":
                try:
                    info = etree.XML(data)
                except:
                    data = data.replace('& ', '&amp; ')
                    info = etree.XML(data)
            else:
                info = data
        except:
            raise
        return info        

    def get_collection_titles(self):

        tgt = VSERVER + "?a=cl&cl=CL1&f=XML"
        dom = self.fetch(tgt, format="xml")
        pubs = dom.xpath('/VeridianXMLResponse/PublicationsResponse/ArrayOfPublication/Publication/PublicationMetadata')

        pubhash = {}
        for p in pubs:
            pid = p.xpath('./PublicationID/text()')[0]
            ptitle = p.xpath('./PublicationTitle/text()')[0]
            pubhash[pid] = ptitle
        return pubhash        

        
    def do_collections(self):

        pubhash = self.get_collection_titles()

        its = pubhash.items()
        its.sort()
        coll = fac.collection('top', label="All Publications")
        for (k,v) in its:
            coll.collection(ident=k, label=v)
        out = coll.toString(compact=False)
        response['content_type'] = 'application/json'
        return out

    def do_collection(self, identifier):

        tgt = VSERVER + "?a=cl&cl=CL1&f=XML&sp=%s" % (identifier)
        dom = self.fetch(tgt, format="xml")        
        docs = dom.xpath('/VeridianXMLResponse/DocumentsResponse/ArrayOfDocument/Document/DocumentMetadata')

        pubhash = self.get_collection_titles()
        clabel = pubhash.get(identifier, 'Unknown Publication')

        coll = fac.collection(ident=identifier, label=clabel)
        for d in docs:
            mfstid = d.xpath('./DocumentID/text()')[0]
            date = d.xpath('./DocumentDate/text()')[0]
            coll.manifest(ident="%s/manifest" % mfstid, label="%s Issue of %s" % (date, clabel))

        out = coll.toString(compact=False)
        response['content_type'] = 'application/json'
        return out 


    def do_manifest(self, identifier):

        tgt = VSERVER + "?a=d&f=XML&d=%s" % (identifier)
        dom = self.fetch(tgt, format="xml")

        name = dom.xpath('/VeridianXMLResponse/DocumentResponse/Document/PublicationMetadata/PublicationTitle/text()')[0]
        date = dom.xpath('/VeridianXMLResponse/DocumentResponse/Document/DocumentMetadata/DocumentDate/text()')[0]

        name = name + ', ' + date

        mfst = fac.manifest(ident=identifier, label=name)
        mfst.set_metadata({"Date":date})
        seq = mfst.sequence(label="Normal Order")

        pages = dom.xpath('/VeridianXMLResponse/DocumentResponse/Document/DocumentContent/ArrayOfPage/Page')

        for p in pages:
            # actually only need h/w info, can calculate rest of info for Canvas
            pageId = p.xpath('./PageMetadata/PageID/text()')[0]
            pageTitle = p.xpath('./PageMetadata/PageTitle/text()')[0]
            width = int(p.xpath('./PageMetadata/PageImageWidth/text()')[0])
            height = int(p.xpath('./PageMetadata/PageImageHeight/text()')[0])            
            cvs = seq.canvas(ident=pageId, label=pageTitle)
            cvs.set_hw(height, width)
            anno = cvs.annotation()
            img = anno.image(pageId ,iiif=True)

            # And add link for alto to anno converter
            # annol = cvs.annotationList(ident=baseIdent)

        # do article ranges here

        out = mfst.toString(compact=False)
        response['content_type'] = 'application/json'
        return out        

    def do_annoList(self, identifier, date, edition, sequence):
        # http://chroniclingamerica.loc.gov/lccn/sn85066387/1907-03-17/ed-1/seq-1/ocr.xml
        tgt = "http://chroniclingamerica.loc.gov/lccn/%s/%s/%s/%s/ocr.xml" % (identifier, date, edition, sequence)
        try:
            fh = urllib.urlopen(tgt)
            data = fh.read()
            fh.close()
            dom = etree.XML(data)
        except:
            raise

        xmlns = {'a' : 'http://schema.ccs-gmbh.com/ALTO'}
        lines = dom.xpath('/a:alto/a:Layout/a:Page/a:PrintSpace/a:TextBlock/a:TextLine', namespaces=xmlns)

        page = dom.xpath('/a:alto/a:Layout/a:Page', namespaces=xmlns)[0]
        ph = int(page.attrib['HEIGHT'])
        pw = int(page.attrib['WIDTH'])

        imgInfo = self.make_info(identifier,date,edition,sequence)        
        imgh = imgInfo['height']        
        imgw = imgInfo['width']

        ratio = int(imgh) / float(ph)

        baseIdent="lccn/%s/%s/%s/%s" % (identifier, date, edition, sequence)
        annol = fac.annotationList(ident=baseIdent)        

        for l in lines:
            text = []
            x = int(float(l.attrib['HPOS'])*ratio)
            y = int(float(l.attrib['VPOS'])*ratio)
            h = int(float(l.attrib['HEIGHT'])*ratio)
            w = int(float(l.attrib['WIDTH'])*ratio)
            for s in l:
                if s.tag == '{%s}String' % xmlns['a']:
                    text.append(s.attrib['CONTENT'])
                elif s.tag == '{%s}SP' % xmlns['a']:
                    text.append(' ')
            txt = ''.join(text)
            txt = txt.replace('"', "&quot;")

            # Maybe ignore, if obvious trash
            txt2 = txt.lower()
            junk = txt2.count('i') + txt2.count(',') + txt2.count('.') + txt2.count('l') + txt2.count('u') + txt2.count('!') + txt2.count("'") + txt2.count('1')
            txt2 = txt2.replace(' ', '')
            if junk / float(len(txt2)) > 0.45:
                # print "Junk: " + txt
                continue

            anno = annol.annotation()
            anno.text(txt)
            anno.on = fac.metadata_base + "canvas/" + baseIdent + (".json#xywh=%s,%s,%s,%s" % (x,y,w,h))

        out = annol.toString(compact=False)
        response['content_type'] = "application/json"
        return out


    def dispatch_views(self):

        self.app.route("/top.json", "GET", self.do_collections)
        self.app.route("/<identifier>.json", "GET", self.do_collection)
        self.app.route("/<identifier>/manifest.json", "GET", self.do_manifest)
        self.app.route("/<identifier>/list/<canvas>.json", "GET", self.do_annoList)

    def after_request(self):
        """A bottle hook to add CORS headers"""
        methods = 'GET'
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
    PFX = ""
    v = ManifestShim();
    return v.get_bottle_app()

def main():
    mr = ManifestShim()
    run(host='localhost', port=8080, app=mr.get_bottle_app())

if __name__ == "__main__":
    main()
else:
    application = apache()
