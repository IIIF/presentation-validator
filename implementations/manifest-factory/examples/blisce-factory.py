#!/home/cheshire/install/bin/python -i

import sys, os, re
from factory import ManifestFactory

# -----------------------------------------------------------------------------
# Audio bits
audioInfo = [
             ['1,15', '1070,425,871,100'],
             ['15,32', '1105,554,841,94'],
             ['32,55', '974,674,967,99'],
             ['55,01:17', '986,793,946,109'],
             ['01:17,01:40', '992,931,943,97'],
             ['01:40,02:03', '996,1046,948,86'],
             ['02:03,02:26', '990,1174,954,96'],
             ['02:26,02:40', '988,1294,444,90']
            ];

# Text bits
textInfo = [
            [1,'0,1',  '914,394,257,274'],
            [1,'1,29', '1090,514,332,48'],
            [2,'',     '1419,514,425,48'],
            [3,'0,7',  '1835,514,108,48'],
            [3, '7,35',  '1090,630,344,50'],
            [4, '',    '1432,630,333,50'],
            [5, '0,14',    '1765,630,177,50'],
            [5, '14,29', '989,757,157,50'],
            [6, '', '1140,757,271,50'],
            [7, '', '1412,757,339,50'],
            [8, '0,14', '1750,757,191,50'],
            [8, '14,23', '990,878,100,50'],
            [9, '', '1090,878,255,50'],
            [10, '', '1346,878,390,50'],
            [11, '0,20', '1733,878,209,50'],
            [11, '20,29', '994,1002,85,50'],
            [12, '', '1076,1002,415,50'],
            [13, '', '1488,1002,222,50'],
            [14, '0,19', '1713,1002,224,50'],
            [14, '19,32', '988,1122,152,50'],
            [15, '', '1139,1122,217,50'],
            [16, '', '1358,1122,253,50'],
            [17, '', '1614,1122,271,50'],
            [18, '0,4', '1884,1122,71,50'],
            [18, '4,18', '987,1252,148,50'],
            [19, '', '1136,1252,260,50'],
            [20, '', '1396,1252,243,50'],
            [21, '0,26',  '1638,1252,308,50'],
            [21, '26,30', '989,1372,47,50'],
            [22, '', '1038,1372,401,50']
            ];

factory = ManifestFactory()
fac.set_base_metadata_uri("http://www.shared-canvas.org/impl/demo2c/")

mf = factory.manifest(label="Worldes Blisce")
mf.description = "The only remaining leaf of a 300+ folio music manuscript that was split up and used as fly leaves for other manuscripts.  This leaf contains the only copy of this particular song, World's Bliss."
mf.attribution = "Provided by the Parker Library, University of Cambridge"

seq = mf.sequence(label="Single Leaf")
cvs = seq.canvas(ident="c1", label="Worldes Blisce")
cvs.set_hw(1480, 2288)

anno = cvs.annotation()
cvs.image("http://www.shared-canvas.org/mss/iiif/2/res/blisce-rc.jpg")
texts = cvs.annotationList("text-f1", label="Transcription")
audios = cvs.annotationList("audio-f1", label="Performance")

              
mp3fn = 'blisce.mp3#t=npt:'
for a in audioInfo:
    aanno = audios.annotation()
    mp3 = aanno.audio(ident = 'blisce.mp3#t=npt:%s' % a[0])
    aanno.on += ("#xywh=%s" % a[1])
    # --- Does the player need this info still?
    # mp3.extent = "02:45"

          
for t in textInfo:
    xptr = '//l[n="%s"]' % t[0];
    if t[1]:
        xptr = "string-range(%s,%s)" % (xptr, t[1])

    tanno = texts.annotation()
    tanno.xmlPtr(ident="http://www.shared-canvas.org/mss/iiif/2/res/blisce.xml#xpointer(%s)" % xptr)
    tanno.on += ("#xywh=%s" % t[2])
  
    # Add style for initial W
    if t[1] == '0,1':
        ta['resource'] = {
            "@type" : "oa:SpecificResource",
            "style" : "initial",
            "full" : {
                "@id": "http://www.shared-canvas.org/mss/iiif/2/res/blisce.xml#xpointer(%s)" % xptr,
                "@type":"dctypes:Text"
            }
        }
        ta['stylesheet'] = {
            "@type": ["oa:CssStyle", "cnt:ContentAsText"],
            "chars": ".initial {font-size: 80px; color: #4040ff; }"     
        }
    textAnnos.append(ta)

textList['resources'] = textAnnos
textList['@context'] = context
textstr = json.dumps(textList, sort_keys=True, indent=4)
fh = file('text.json', 'w')
fh.write(textstr)
fh.close()

