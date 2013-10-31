Metadata Factory
================


Initialization
--------------

```python
	from factory import ManifestFactory

	fac = ManifestFactory()
	fac.set_base_metadata_uri("http://www.example.org/path/to/object/")
	fac.set_base_metdata_dir("/home/iiif/web/path/to/object/")

	fac.set_base_image_uri("http://www.example.org/path/to/image/api/")

	fac.set_iiif_image_conformance(1.1, 2) # Version, ComplianceLevel
	fac.set_debug("error") # warn will warn for recommendations, by default
```




