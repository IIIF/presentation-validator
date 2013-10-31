
from factory import ManifestFactory
from lxml import etree
import ljson as json

imageWidth = 693
imageHeight = 786

fh = file('../examples/ms_richardson_44-mets.xml')
data = fh.read()
fh.close()
dom = etree.XML(data)
metsNS = 'http://www.loc.gov/METS/'
modsNS = 'http://www.loc.gov/mods/v3'
xlinkNS = 'http://www.w3.org/1999/xlink'
ALLNS = {'mets':metsNS, 'mods':modsNS, 'xlink':xlinkNS}

# Extract basic info
identifier = dom.xpath('/mets:mets/mets:dmdSec/mets:mdWrap[@MDTYPE="MODS"]/mets:xmlData/mods:mods/mods:identifier/text()', namespaces=ALLNS)[0]
mflabel = dom.xpath('/mets:mets/@LABEL', namespaces=ALLNS)[0]
manifestType = dom.xpath('/mets:mets/@TYPE', namespaces=ALLNS)[0]

# Extract image info
images = dom.xpath('/mets:mets/mets:fileSec/mets:fileGrp/mets:file[@MIMETYPE="image/jp2"]', namespaces=ALLNS)
struct = dom.xpath('/mets:mets/mets:structMap/mets:div[@TYPE="CITATION"]/mets:div', namespaces=ALLNS)
imageHash = {}
for img in images:
	imageHash[img.xpath('./@ID', namespaces=ALLNS)[0]] = img.xpath('./mets:FLocat/@xlink:href', namespaces = ALLNS)[0]


# Configure the factory
fac = ManifestFactory()
fac.set_base_metadata_uri("http://ids.lib.harvard.edu/iiif/metadata/")
fac.set_base_image_uri("http://ids.lib.harvard.edu/ids/view/" + identifier + '/')
fac.set_iiif_image_conformance(1.1, 1)

# Build the Manifest
mf = fac.manifest(ident="manifest", label=mflabel)
mf.attribution = "Provided by the Houghton Library, Harvard University"
mf.viewingHint = "paged" if manifestType == "PAGEDOBJECT" else "individuals"
mf.description = "Description of Manuscript MS Richardson 44 Goes Here"

# And walk through the pages
seq = mf.sequence(ident="normal", label="Normal Order")
for st in struct:
	# Find label, and image ID
	label = st.xpath('./@LABEL')[0] 
	image = imageHash[st.xpath('./mets:div/mets:fptr[2]/@FILEID', namespaces=ALLNS)[0]]

	# Build the Canvas
	cvs = seq.canvas(ident="c%s" % image,label=label)
	cvs.set_hw(imageHeight, imageWidth)

	# Build the Image Annotation
	anno = cvs.annotation(ident="a%s" % image)
	img = anno.image(ident=image, iiif=True)
	img.set_hw(imageHeight, imageWidth)

# Serialize 
mfjs = mf.toJSON()
srlzd = json.dumps(mfjs, sort_keys=True, indent=2)
