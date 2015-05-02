Metadata Factory
================

A quick code walk through for how to build manifests using the factory.

Requirements
------------

In order to automatically determine the dimensions of local image files, you will need to have either ImageMagick or the Python Image Library installed.  ImageMagick attempts to use a command line rather than module approach, which may not work under Windows (untested).  Neither will work with JPG 2000 files out of the box.  Alternatively, if the image is served from a IIIF Image API service, the info.json response can be used.  The library does not work with Python 3.X, but has been tested in various environments with 2.6+

For 2.6 and before, you must have the OrderedDict backport installed.  In Python 2.7 it is part of the base library.

You should have lxml installed, which is used to sanity check HTML values.  If it is not present, then the checks will just not be done.


Initialization
--------------

First import the Factory and configure it for your implementation.  This is the object that produces your Manifest, and from there we'll just walk down the tree.

```python
from factory import ManifestFactory

fac = ManifestFactory()
# Where the resources live on the web
fac.set_base_metadata_uri("http://www.example.org/path/to/object/")
# Where the resources live on disk
fac.set_base_metadata_dir("/home/user/web_root/path/to/object/")

# Default Image API information
fac.set_base_image_uri("http://www.example.org/path/to/image/api/")
fac.set_iiif_image_info(2.0, 2) # Version, ComplianceLevel

# 'warn' will print warnings, default level
# 'error' will turn off warnings
# 'error_on_warning' will make warnings into errors
fac.set_debug("warn") 

```

Object Creation
---------------

Only the top level object that you want to create is built from the factory.  All subsequent objects are created from the object that it should be a child of in the hierarchy.  So, first have the factory create a manifest and give it a label (which is required).

```python
manifest = factory.manifest(label="Example Manifest")
```

You could also explicitly set the identifier. The default will be `manifest.json` in the base metadata URI path.

```python
manifest = factory.manifest(ident="identifier/manifest", label="Example Manifest")
```

You can then add metadata and other fields to it:

```python
manifest.set_metadata({"Date": "Some Date", "Location": "Some Location"})
manifest.description = "This is a longer description of the manifest"
manifest.viewingDirection = "left-to-right"
```

To add metadata with languages, pass in a dictionary with `label` and `value` keys, and the language tagged content in the value like:

```python
manifest.set_metadata(
	{'label' : {'en':"Date", 'fr':'Date'}, 
	 'value': {'en':'15th Century', 'fr': 'Quinzieme Siecle'}
	})
```

Repeated calls to set_metadata will add new entries and leave the existing ones untouched.

The objects are then used to create subsequent objects underneath them.  To create a sequence within the manifest, and then 10 canvases, each with a single image:

```python
seq = manifest.sequence()  # unlabeled, anonymous sequence

for p in range(10):
	# Create a canvas with uri slug of page-1, and label of Page 1
	cvs = seq.canvas(ident="page-%s" % p, label="Page %s" % p)

	# Create an annotation on the Canvas
	anno = cvs.annotation()

	# Add Image: http://www.example.org/path/to/image/api/p1/full/full/0/native.jpg
	img = anno.image("p%s" % p, iiif=True)

	# Set image height and width, and canvas to same dimensions
	imagefile = "/path/to/images/p%s.jpg" % p
    img.set_hw_from_file(imagefile) 

    # OR if you have a IIIF service:
    img.set_hw_from_iiif()

    cvs.height = img.height
    cvs.width = img.width
```

A shorthand method for the above, if there's a IIIF service available:

```python

for p in pages:
    cvs = seq.canvas(ident="page-%s" % p, label="Page %s" % p)
    cvs.add_image_annotation(ident="p%s" % p, iiif=True)
```

And add_image_annotation will create the annotation, set the height and width of both image and canvas to the size retrieved from the info.json response.


Other Methods
-------------

You can also add existing objects to their parents with `add_<i>className</i>`:

```python
manifest = factory.manifest(label="A Manifest")
coll = factory.collection(ident='top', label="Topmost Collection")
coll.add_manifest(manifest)
```

And the same for add_collection, add_annotation, and so forth.

Note that Ranges do not allow the creation of Canvases, nor Layers the creation of AnnotationLists.  These are created from Sequences and the AnnotationLists, respectively.  Existing Canvases must then be added to a Range with add_canvas(), that takes an additional argument of `frag` with the fragment to add to the end of the canvas's identifier.

```python
r = manifest.range(ident="range1", "Chapter 1")
c = sequence.canvas(ident="canvas1", label="Page 1")
r.add_canvas(c, frag="xywh=100,100,640,480")
```

You can set the start canvas of a sequence or a range with the set_start_canvas() method:

```python
seq = manifest.sequence()
canvas1 = seq.canvas(ident="page1", label="First Page")
seq.set_start_canvas(canvas1)
```

Serialization
-------------

You can serialize directly to the file (with the base_metadata_dir set).  If you set compact, it will reduce the filesize by leaving out spaces, new lines and other unnecessary whitespace.  It is entirely unreadable by humans, however.

```python
manifest.toFile(compact=False)
```

`toFile` will return the string that was written to disk, in case you're using it as a caching mechanism.

You can also serialize to a string and write it out by hand:

```python
data = manifest.toString(compact=False)
fh = file('manifest.json')
fh.write(data)
fh.close()
```

Or if you really want to get into the JSON directly, you can get the full dict:
```python
# Have to tell the object to add @context with top=True
mfst = manifest.toJSON(top=True)
```

The serialization will attempt to add in any properties from the object that are set, even if they're not part of the model.  Implementations should ignore them, but be careful for typos!


Further Objects
---------------

The factory, and objects in the hierarchy, also support the following object types:

* collection(identity, label, metadataHash)
```python
coll = factory.collection("top", "Top Collection", {"Date":"1900"})
coll.manifest("first", "First Object")
coll.manifest("second", "Second Object")
coll.collection("sub1", "First SubCollection")
```

* annotationList(identity, label, metadataHash)
```python
annol = cvs.annotationList("text-1")
anno = annol.annotation()
# ...
annol.toFile(compact=False)
```

* choice(default, restList)
```python
img1 = fac.image("f1r.c", label="Color", iiif=True)
img1.set_hw_from_file("/path/to/f1r.c.jpg")
img2 = fac.image("f1r", label="Black and White", iiif=True)
img2.set_hw_from_file("/path/to/f1r.bw.jpg")
anno.choice(img1, [img2])
```

* text(content, language, mediaType)
```python
anno = annol.annotation()
anno.text("Ci commence li prologue", language="fr")
```

* range(identity, label, metadataHash) and layer(identity, label, metadataHash)
```python
rng = manifest.range("range-1", label="Introduction")
rng.add_canvas(cvs)
layer = annol.layer("transcription-1", label="2003 Transcription")
annol2.within = layer
```

Parsing
-------

Parsing requires the loader library, which imports the factory.  It implements a (equally poorly named) ManifestReader class that parses the data provided to it and returns the object hierarchy as if you had built it by hand with the ManifestFactory.

```python
from loader import ManifestReader

# Data is either a string or parsed JSON
reader = ManifestReader(data)
manifest = reader.read()
```

And that's all there is to it.

