#!/usr/bin/python
# -*- coding: utf-8 -*-

from factory import ManifestFactory
from lxml import etree
import os

fh = file('web-view.html')
html = fh.read()
fh.close()
dom = etree.HTML(html)
subs = dom.xpath('//div[@class="related-records"]/dl[@class="return-art"]')

fac = ManifestFactory()
fac.set_base_metadata_uri("http://vm-imgrepo-tdp.nga.gov/public/manifests/")
fac.set_base_image_uri("http://vm-imgrepo-tdp.nga.gov/public/objects/")
fac.set_base_metadata_dir("/mnt/images/public/manifests")
fac.set_iiif_image_info(2.0, 2)
fac.set_debug("error") # warn will warn for recommendations, by default

label = "Cézanne Sketchbook"
mdhash = {"Dates": "c. 1877/1900", "Creator": "Cézanne, Paul (1839-1906)"}
mdhash["Inscription"] = "Various notations overall"
mdhash["Provenance"] = """
<div>Paul Cézanne (the artist's son), Paris;
<br/>Paul Guillaume, Paris;
<br/>Adrien Chappuis, Tresserve, Switzerland, 1933;
<br/>Paul Mellon, Upperville, VA, 1967;
<br/>gift to NGA, 1991
</div>"""

mdhash["Exhibition History"] = """<div>
<b>1991</b> NGA Anniversary 1991, 176.
<br/><b>1999</b> An Enduring Legacy: Masterpieces from the Collection of Mr. and Mrs. Paul Mellon, National Gallery of Art, Washington, 1999-2000.
</div>"""

mdhash["Bibliography"] = """<div>
<b>1936</b> Venturi, Lionello. Cézanne: son art, son oeuvre. 2 vols. Paris, 1936.
<b>1967</b> Chappuis, Adrien. Album de Paul Cézanne (sketchbook facsimile). Paris: Berggruen & Cie, 1967.
<b>1973</b> Chappuis, Adrien. The Drawings of Paul Cezanne. 2 vols. Greenwich: New York Graphic Society, 1973.
<b>1983</b> Rewald, John. Paul Cézanne: The Watercolors. Boston: Little, Brown & Company, 1983.
</div>"""

mdhash["Catalog Raisonné Ref"] = "Chappuis 1973, no. 1149, State and others"
mdhash["Accessioning Number"] = "1992.51.9"
mdhash["Page Size"] = "15.2 x 23.7 cm (6 x 9 5/16 in.)"

description = "Sketchbook with 71 drawings in graphite, pen and brown ink, and watercolor; the sketchbook contains 46 sheets, several which are blank; the end papers, the recto of the first page, and half the verso of the final page were used for notes, lists, and arithmetical figuring; a draft of a letter to the critic Octave Mirbeau is on page II (recto)"
attribution = "Held by the National Gallery of Art"


mf = fac.manifest(ident="manifest", label=label)
mf.set_metadata(mdhash)
mf.description = description

mf.viewingHint = "paged"
mf.viewingDirection = "left-to-right"

seq = mf.sequence(ident="normal", label="Normal Order")

cvs1 = seq.canvas(ident="cover", label="Cover")
cvs1.set_image_annotation("76219")

for s in subs:
	title = s.xpath('./dt[@class="title"]/a/text()')[0]
	date = s.xpath('./dd[@class="created"]/text()')[0]
	link = s.xpath('./dd/a/@href')[0][-10:-5]

	imgid = os.path.join(*[x for x in link])
	imgid = os.path.join(imgid, link)

	cvs = seq.canvas(ident=link, label=title)
	cvs.set_metadata({"Date": date})
	cvs.description = "Graphite on wove paper"
	cvs.set_image_annotation(imgid)

# cvs2label = {"en":"The Plaster Mill", "fr": "La Moulin à plâtre)"}

mf.toFile()


