#!/home/cheshire/install/bin/python -i

import sys, os, re
import ljson as json
import random

from factory import ManifestFactory

# Javascript data file parser
# -----------------------------------------------------------
wre = re.compile('this\.origwidth[ ]*=[ ]*([0-9]+);')
hre = re.compile('this\.origheight[ ]*=[ ]*([0-9]+);')
are = re.compile('this.area([0-9]+) = new Array\((.+)\);')
dre = re.compile('this.data([0-9]+) = "(.+)";')
colare = re.compile('this.cola = new Array\((.+)\);')
colbre = re.compile('this.colb = new Array\((.+)\);')

abre = re.compile('ab{(.*?):(.*?)}')
casere = re.compile('case{(.*?):(.*?)}')
jre = re.compile('j{(.*?)}')
numre = re.compile('num{(.*?):(.*?)}')

replaces = {'\\' : '',
            '&duav;' : 'v',
            '&dvau;' : 'u',
            '&djai;' : 'i',
            '&diaj;' : 'j',
            '&adap;' : "'",
            '&apos;' : "'",
            '&adfs;' :'.',
            '&adcom;' : ',',
            '&adfg;' : "'",
            '&adog;' : "'",
            '&adem;' : '!',
            '&adqm;' : '?',
            '&adcol;' : ':' 
            }

def parse_js_file(f, rv):
    # Read javascript data
    folio = 'f%s%s' % (f, rv)
    fh = file(jsDirectory + '%s.js' % folio)
    data = fh.readlines()
    fh.close()
    width = 0
    height = 0
    areas = {}
    datas = {}
    cola = ''
    colb = ''
    for l in data:
        if not width:
            m = wre.search(l)
            if m:
                width = int(m.groups()[0])
            continue
        if not height:
            m = hre.search(l)
            if m:
                height = int(m.groups()[0])
            continue
        if cola:
            # only look for colb
            m = colbre.search(l)
            if m:
                colb = m.groups()[0]
                break
            else:
                continue
        if datas:
            # only look for data, cola
            m = dre.search(l)
            if m:
                (n, val) = m.groups()
                datas[int(n)] = val
            else:
                # cola
                m = colare.search(l)
                if m:
                    cola = m.groups()[0]
        # look for areas
        m = are.search(l)
        if m:
            (n, val) = m.groups()
            areas[int(n)] = val
 
        else:
            # look for datas
            m = dre.search(l)
            if m:
                (n, val) = m.groups()
                datas[int(n)] = val   
                
    return (cola, colb, areas, datas)

def fix_js_text(txt):
    for (k,v) in replaces.items():
        txt = txt.replace(k, v)
    txt = numre.sub('\\1', txt)
    txt = casere.sub('\\1', txt)
    txt = abre.sub('\\1', txt)
    txt = jre.sub('\\1', txt) 
    return txt
    


# -----------------------------------------------------------------------------

imageDirectory = "/Users/azaroth/Dropbox/SharedCanvasData/m804/images/"
jsDirectory = "/Users/azaroth/Dropbox/SharedCanvasData/m804/js/"
# resDirectory = "/Users/azaroth/Dropbox/SharedCanvas/impl/demo1d/res_random/"
resDirectory = "/Users/azaroth/Dropbox/IIIF/demos/mirador/data/"
minFolio= 1
maxFolio = 258


fac = ManifestFactory()
fac.set_base_metadata_uri("http://www.shared-canvas.org/impl/demo1d/res_human/")
fac.set_base_image_uri("http://www.shared-canvas.org/iiif/")
fac.set_base_metdata_dir("/Users/azaroth/Dropbox/SharedCanvas/impl/demo1d/res_human/")
fac.set_iiif_image_conformance(1.1, 2)
fac.set_debug("error") # warn will warn for recommendations, by default

rubricCss = ".red {color: red}"
initialCss = ".bold {font-weight: bold}"

mf = fac.manifest(ident="manifest", label="Pierpont Morgan MS.804")
mf.set_metadata({"Dates": "Author's version circa 1380, scribed circa 1400, illuminations circa 1420"})
mf.attribution = "Held at the Pierpont Morgan Library"
mf.viewingHint = "paged"
mf.viewingDirection = "left-to-right"

seq = mf.sequence(ident="normal", label="Normal Order")

for f in range(minFolio, maxFolio+1):
    for rv in ['r', 'v']:
        # View in Sequence
        folio = 'f%s%s' % (f, rv)

        if folio == "f258v":
            # Ends at 258r, skip
            continue

        rvfull = "recto" if rv == 'r' else "verso"
        imagefile = imageDirectory + ("%s.jpg" % folio)

        cvs = seq.canvas(ident=folio, label="f. %s %s" % (f, rvfull))
        anno = cvs.annotation()
        img = anno.image(folio, iiif=True)
        img.set_hw_from_file(imagefile)
        cvs.height = img.height
        cvs.width = img.width

        if folio == 'f16r':
            # Add Detail Image
            ifn = "f16r.d"
            anno2 = cvs.annotation(label="Detail Image")
            img = anno2.image(ifn, iiif=True)
            img.set_hw_from_file(imageDirectory + ifn + ".jpg")

            frag = '#xywh=640,780,590,410'
            anno2.on += frag
        
        if folio in ['f1r', 'f25r', 'f44v', 'f117r', 'f128r', 'f176v', 'f182r']:

            # Add Image Choice
            img1 = fac.image(ident="%s.c" % folio, label="Color", iiif=True)
            img1.set_hw_from_file(imageDirectory + ("%s.c.jpg" % folio))
            img2 = anno.resource
            img2.set_label("Black and White")
            anno.choice(img1, [img2])


        # Add Text Annotation List
        annol = cvs.annotationList("text-%s" % folio)

        # Text Annotations per Line
        (cola, colb, areas, texts) = parse_js_file(f,rv)
        lineids = texts.keys()
        lineids.sort()
                        
        for lid in lineids:
            try:
                a = areas[lid]
            except:
                print "No area for line %s on %s" % (lid, folio)
                continue
            bits = a.split(',')
            if len(bits) != 5 or bits[-1].strip() != '3':
                (x1,y1,x2,y2) = [int(b) for b in bits[:4]]
                frag = "#xywh=%s,%s,%s,%s" % (x1,y1,x2-x1,y2-y1)
                txt = fix_js_text(texts[lid])

                anno = annol.annotation()
                anno.on += frag
                anno.text(txt, language="fr")
                
                # Add style for rubric, initial
                if len(bits) == 5:
                    typ = int(bits[-1].strip())
                    if typ == 2:
                        # rubric
                        anno.stylesheet(rubricCss, "red")
                    elif typ == 1:  
                        # initial
                        anno.stylesheet(initialCss, "bold")

        # write out anno list
        fh = file(resDirectory + "list/text-%s.json" % folio, 'w')
        listdata = annol.toString(compact=False)
        fh.write(listdata)
        fh.close()

        # Add random comments
        annol2 = cvs.annotationList("comment-%s" % folio)
        for i in range(random.randint(1,20)+5):
            annoc = annol2.annotation()
            annoc.motivation = "oa:commenting"

            xc = random.randint(1, cvs.width-25)
            yc = random.randint(1, cvs.height-25)
            wc = random.randint(10, cvs.width - xc - 5)
            hc = random.randint(10, cvs.height - yc - 5)

            annoc.on += "#xywh=%s,%s,%s,%s" % (xc, yc, wc, hc)
            annoc.text("This is a sample comment annotation, left top corner is %s in and %s down, size is %s wide by %s high. Enjoy!" % (xc, yc, wc, hc))

            fh = file(resDirectory + "list/comment-%s.json" % folio, 'w')
            listdata = annol2.toString(compact=False)
            fh.write(listdata)
            fh.close()


fh = file(resDirectory + 'manifest.json', 'w')
output = mf.toString(compact=False)
fh.write(output)
fh.close()
