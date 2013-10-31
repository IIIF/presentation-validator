Metadata Factory
================

A quick code walk through for how to build manifests using the factory.

Initialization
--------------

First import the Factory and configure it for your implementation.  This is the object that produces your Manifest, and from there we'll just walk down the tree.

```python
from factory import ManifestFactory

fac = ManifestFactory()
fac.set_base_metadata_uri("http://www.example.org/path/to/object/")
fac.set_base_metdata_dir("/home/iiif/web/path/to/object/")

fac.set_base_image_uri("http://www.example.org/path/to/image/api/")

fac.set_iiif_image_conformance(1.1, 2) # Version, ComplianceLevel
fac.set_debug("warn") # 'error' will turn off warnings
```

Object Creation
---------------

First create a manifest and give it a label (which is required by the model).

```python
manifest = factory.manifest(label="Example Manifest")
```

You can then add metadata and other fields to it:

```python
manifest.set_metadata({"Date": "Some Date", "Location": "Some Location"})
manifest.description = "This is a longer description of the manifest"
manifest.viewingDirection = "left-to-right"
```

The objects are then used to create subsequent objects underneath them.  To create a sequence within the manifest, and then 10 canvases, each with a single image:

```python
seq = manifest.sequence()  # unlabeled, anonymous sequence

pages = range(10) # put your real page info here
for p in pages:
	cvs = seq.canvas(ident="page-%s" % p, label="Page %s" % p)
	anno = cvs.annotation()

	# http://www.example.org/path/to/image/api/p1/full/full/0/native.jpg
	img = anno.image("p%s" % p, iiif=True)

	# Set image height and width, and canvas to same dimensions
	imagefile = "/path/to/images/p%s.jpg" % p
    img.set_hw_from_file(imagefile)  
    cvs.height = img.height
    cvs.width = img.width
```


