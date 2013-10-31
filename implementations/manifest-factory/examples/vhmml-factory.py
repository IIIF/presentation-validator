#!/home/cheshire/install/bin/python -i

import sys, os, re
import ljson as json

from factory import ManifestFactory


# Read in CSV file
# ... by hand :P

fh = file('MsLatOct121.txt')
lines = fh.read()
lines = lines.replace('\xa9', '')
lines = lines.replace('\x8a', '')
lines = lines.split('\r')
fh.close()

fields = []
for l in lines:
    row = {}
    cells = l.split('\t')
    for r in range(len(cells)):
        row[r] = cells[r]
    fields.append(row)

fields = fields[1:]


resDirectory = "/Users/azaroth/Dropbox/IIIF/demos/mirador/data/vhmml/"

fac = ManifestFactory()
fac.set_base_metadata_uri("http://localhost/demos/mirador/data/vhmml/")
fac.set_base_image_uri("http://localhost/services/image/iiif2/")
fac.set_debug("error") # warn will warn for recommendations, by default

mf = fac.manifest(label=fields[0][0])
mf.set_metadata({"Date": fields[0][6], "City": fields[0][19],
                    "Library": fields[0][20], "Country of Origin": fields[0][21],
                    "Genre": fields[0][22], "Total Folios": fields[0][28]})

mf.attribution = fields[0][14] + "\n" + fields[0][18]
mf.viewingHint = "paged"
mf.viewingDirection = "left-to-right"

seq = mf.sequence(ident="normal", label="Normal Order")

imageHeight = 1239
imageWidth = 800

for row in fields:
        folio = row[28]
        folioUri = folio.replace(' ', '_')

        cvs = seq.canvas(ident=folioUri, label=folio)
        anno = cvs.annotation()
        img = anno.image(row[34], iiif=True)
        cvs.height = imageHeight
        cvs.width = imageWidth
        cvs.description = row[2]

fh = file(resDirectory + 'manifest.json', 'w')
output = mf.toString(compact=False)
fh.write(output)
fh.close()
