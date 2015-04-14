

import json

from bottle import Bottle, route, run, request, response, abort, error

import os, sys
import factory
from lxml import etree

import uuid
import urllib, urllib2, urlparse

from factory import ManifestFactory

fac = ManifestFactory()
fac.set_base_image_uri("http://iiif-dev.localhost/services/chronam/")
fac.set_iiif_image_info(version="2.0", lvl="1")
fac.set_base_metadata_dir('/Users/azaroth/Dropbox/Rob/Web/iiif-dev/prezi/chronam/')
fac.set_base_metadata_uri("http://localhost:8080/")
# http://localhost:8080/list/lccn/sn99021999/1915-03-27/ed-1/seq-1.json
fac.set_debug('error')

PFX = ""
INFO_CACHE = {}
CACHEDIR = '/Users/azaroth/Dropbox/Rob/Web/iiif-dev/prezi/chronam/'

class ChronAmManifestShim(object):

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
                info = etree.XML(data)
            else:
                info = data
        except:
            raise
        return info        
        
    def make_info(self, identifier, date, edition, sequence):
        try:
            (imageW, imageH) = INFO_CACHE[tgt]
        except:
            tgt = "http://chroniclingamerica.loc.gov/lccn/%s/%s/%s/%s.rdf" % (identifier, date, edition, sequence)
            try:
                dom = self.fetch(tgt, "xml")
                imageW = int(dom.xpath('//exif:width/text()', namespaces={'exif':'http://www.w3.org/2003/12/exif/ns#'})[0])
                imageH = int(dom.xpath('//exif:height/text()', namespaces={'exif':'http://www.w3.org/2003/12/exif/ns#'})[0])
                INFO_CACHE[tgt] = (imageW, imageH)
            except:
                raise
                return {}
        info = {"width":imageW, "height":imageH}
        return info

    def do_top_collection(self):

        # create or serve cached top level collection
        cached = os.path.join(CACHEDIR, "top.json")
        if os.path.exists(cached):
            fh = file(cached)
            out = fh.read()
            fh.close()
        else:

            url = "http://chroniclingamerica.loc.gov/newspapers.txt"
            data = self.fetch(url, format="txt")
            lines = data.split('\n')[1:]

            perState = {}
            for l in lines:
                l = l.strip()
                if l:
                    bits = l.split(' | ')
                    state = bits[1].strip()
                    name = bits[2].strip()
                    lccn = bits[3].strip()
                    try:
                        perState[state].append([name, lccn])
                    except:
                        perState[state] = [[name, lccn]]

            top = fac.collection(ident="top", label="Newspapers by State")

            states = perState.keys()
            states.sort()

            for state in states:
                slug = state.lower().replace(" ", "_")
                scoll = top.collection(ident=slug, label="Newspapers in %s" % state)
                for np in perState[state]:
                    scoll.collection(ident="lccn/%s" % np[1], label=np[0])

                sout = scoll.toFile(compact=False)
            out = top.toFile(compact=False)

        response['content_type'] = 'application/json'
        return out

    def do_state_collection(self, identifier):
        cached = os.path.join(CACHEDIR, "%s.json" % identifier)
        if not os.path.exists(cached):
            # 404
            abort(404)
        else:
            fh = file(cached)
            out = fh.read()
            fh.close()
            response['content_type'] = 'application/json'
            return out            


    def do_collection(self, identifier):
        # http://chroniclingamerica.loc.gov/lccn/sn85066387.json

        url = "http://chroniclingamerica.loc.gov/lccn/" + identifier + ".json"
        info = self.fetch(url)

        name = info.get('name', 'Unnamed Publication')
        coll = fac.collection(ident="lccn/%s/collection" % identifier, label=name)

        mdhash = {}
        try:
            mdhash["Place of Publication"] = info['place_of_publication']
        except:
            pass
        try:
            mdhash['First Year'] = info['start_year']
        except:
            pass
        try:
            mdhash['Last Year'] = info['end_year']
        except:
            pass
        try:
            mdhash['Publisher'] = info['publisher']
        except:
            pass

        try:
            mdhash['Topic'] = info['subject']
        except:
            pass

        coll.set_metadata(mdhash)

        for iss in info['issues']:
            jurl = iss['url']
            issurl = jurl.replace('http://chroniclingamerica.loc.gov/', '')
            issurl = issurl.replace('.json', '/manifest')
            isslabel = "(%s) %s" % (iss['date_issued'], name)
            mfst = coll.manifest(ident=issurl, label=isslabel)

        out = coll.toString(compact=False)
        response['content_type'] = 'application/json'
        return out         

    def do_manifest(self, identifier, date, edition):
        # http://chroniclingamerica.loc.gov/lccn/sn85066387/1907-03-17/ed-1.json

        tgt = "http://chroniclingamerica.loc.gov/lccn/%s/%s/%s.json" % (identifier, date, edition)
        info = self.fetch(tgt)

        name = info['title']['name']
        name += " (%s)" % info['date_issued']

        mfst = fac.manifest(ident="lccn/%s/%s/%s/manifest" % (identifier, date, edition), label=name)
        mfst.set_metadata({"Volume":info['volume'], "Number": info['number'], "Edition":info['edition']})
        seq = mfst.sequence(label="Normal Order")
        for p in range(len(info['pages'])):
            # actually only need h/w info, can calculate rest of info for Canvas
            p += 1
            seqid = "seq-%s" % p
            baseIdent="lccn/%s/%s/%s/%s" % (identifier, date, edition, seqid)
            cvs = seq.canvas(ident=baseIdent, label="Page %s" % p)
            imgInfo = self.make_info(identifier,date,edition,seqid)
            cvs.set_hw(imgInfo['height'], imgInfo['width'])
            anno = cvs.annotation()
            img = anno.image("lccn/%s/%s/%s/%s" % (identifier, date, edition, seqid) ,iiif=True)

            # And add link for alto to anno converter
            annol = cvs.annotationList(ident=baseIdent)

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
        self.app.route("/lccn/<identifier>.json", "GET", self.do_collection)
        self.app.route("/lccn/<identifier>/<date>/<edition>/manifest.json", "GET", self.do_manifest)
        self.app.route("/list/lccn/<identifier>/<date>/<edition>/<sequence>.json", "GET", self.do_annoList)
        self.app.route("/top.json", "GET", self.do_top_collection)
        self.app.route("/<identifier>.json", "GET", self.do_state_collection)


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
    v = ChronAmManifestShim();
    return v.get_bottle_app()

def main():
    mr = ChronAmManifestShim()
    run(host='localhost', port=8080, app=mr.get_bottle_app())

if __name__ == "__main__":
    main()
else:
    application = apache()
