
from factory import ManifestFactory
import os

# Example script to build a manifest out of all the images in a directory

destdir = "/path/to/images"

fac = ManifestFactory()
fac.set_debug("error")
fac.set_base_image_uri("http://localhost/iiif")
fac.set_base_image_dir(destdir)
fac.set_iiif_image_info()
fac.set_base_metadata_uri("http://localhost/prezi/")
fac.set_base_metadata_dir("/path/to/prezi/")

mflbl = os.path.split(destdir)[1].replace("_", " ").title()

mfst = fac.manifest(label=mflbl)
seq = mfst.sequence()
for fn in os.listdir(destdir):
	ident = fn[:-4]
	title = ident.replace("_", " ").title()
	cvs = seq.canvas(ident=ident, label=title)
	cvs.add_image_annotation(ident, True)

mfst.toFile(compact=False)
