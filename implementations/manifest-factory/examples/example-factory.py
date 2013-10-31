
from factory import ManifestFactory

imageWidth = 693
imageHeight = 786

identifier = "test"

# Configure the factory
fac = ManifestFactory()
fac.set_base_metadata_uri("http://ids.lib.harvard.edu/iiif/metadata/")
fac.set_base_image_uri("http://ids.lib.harvard.edu/ids/view/" + identifier + '/')
fac.set_iiif_image_conformance(1.1, 1)

# Build the Manifest
mf = fac.manifest(ident="manifest", label="Example Manifest")
mf.set_metadata({"test label":"test value", "next label":"next value"})
mf.attribution = "Provided by the Houghton Library, Harvard University"
mf.viewingHint = "paged"
mf.description = "Description of Manuscript MS Richardson 44 Goes Here"


# And walk through the pages
seq = mf.sequence(ident="normal", label="Normal Order")
for st in range(3):
	# Build the Canvas
	cvs = seq.canvas(ident="c%s" % st,label="Test Canvas %s" % st)
	cvs.set_hw(imageHeight, imageWidth)

	# Build the Image Annotation
	anno = cvs.annotation(ident="a%s" % st)
	img = anno.image(ident="image-%s" % st , iiif=True)
	img.set_hw(imageHeight, imageWidth)

	annoList = cvs.annotationList(ident="List-%s" % st)
	anno = annoList.annotation(ident ="a-list-%s" % st)
	anno.text("Testing")

# add in a Range

rng = mf.range(ident="rng-1", label="Example Range")
rng.add_canvas(seq.canvases[1])
rng.add_canvas(seq.canvases[2], "#xywh=10,10,100,100")


# Serialize 
js = mf.toString(compact=False)

