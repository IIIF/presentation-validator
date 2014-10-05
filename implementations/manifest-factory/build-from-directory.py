from factory import ManifestFactory
import os

destdir = "/Users/azaroth/Data/images/britishmuseum"

fac = ManifestFactory()
fac.set_debug("error")
fac.set_base_image_uri("http://iiif-dev.localhost/services/2.0")
fac.set_base_image_dir(destdir)
fac.set_iiif_image_info()
fac.set_base_metadata_uri("http://iiif-dev.localhost/prezi/temp/")
fac.set_base_metadata_dir("/Users/azaroth/Dropbox/Rob/Web/iiif-dev/prezi/temp/")

mflbl = os.path.split(destdir)[1].replace("_", " ").title()

mfst = fac.manifest(label=mflbl)
seq = mfst.sequence()
for fn in os.listdir(destdir):
	ident = fn[:-4]
	title = ident.replace("_", " ").title()
	cvs = seq.canvas(ident=ident, label=title)
	cvs.add_image_annotation(ident, True)

mfst.toFile(compact=False)
