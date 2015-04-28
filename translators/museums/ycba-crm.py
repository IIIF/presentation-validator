from factory import ManifestFactory
from SPARQLWrapper import SPARQLWrapper, JSON 
import os
import urllib

fac = ManifestFactory()
fac.set_base_image_uri("http://iiif-dev.localhost/services/2.0")
fac.set_iiif_image_info(version="2.0")

dest = "/path/to/images/britishmuseum"

sparql = SPARQLWrapper("http://collection.britishart.yale.edu/openrdf-sesame/repositories/ycba")
sparql.setReturnFormat(JSON)

prefixes = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX bmo: <http://collection.britishmuseum.org/id/ontology/>
PREFIX crm: <http://erlangen-crm.org/current/>
PREFIX bbcpont: <http://purl.org/ontology/po/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX qudt: <http://qudt.org/schema/qudt#>
PREFIX ycbat: <http://collection.britishart.yale.edu/id/thesauri/event/type/>
PREFIX ycbao: <http://collection.britishart.yale.edu/id/object/>
"""

q = """
SELECT DISTINCT ?exhibition ?name {
 ?obj crm:P12i_was_present_at ?exhibition .
 ?exhibition rdfs:label ?name .
}
"""

queries = {
      'comment' : 'bmo:PX_curatorial_comment ?comment',
      'conceptLabel' : 'crm:P128_carries ?c1 . ?c1 crm:P129_is_about ?concept . ?concept skos:prefLabel ?conceptLabel .',
      'placeLabel' : 'crm:P55_has_current_location ?place . ?place rdfs:label ?placeLabel .',
      'title' : 'crm:P102_has_title ?t . ?t rdfs:label ?title',
      'label' : 'rdfs:label ?label'
}

qt = """
SELECT DISTINCT ?%s {
<%s> %s    
}
"""

# Each object has only one image, so pointless having object as manifest
# Take exhibitions as Manifests, with individual canvases

imagePattern = "http://deliver.odai.yale.edu/content/repository/YCBA/object/%s/type/2/format/3"

sparql.setQuery(prefixes + q)
results = sparql.query().convert()

for result in results["results"]["bindings"]:
      exhib = result['exhibition']['value']
      name = result['name']['value']

      eident = os.path.split(exhib)[1] 
      basemd = "http://iiif-dev.localhost/prezi/yale/" + eident
      basedir = "/Users/azaroth/Dropbox/Rob/Web/iiif-dev/prezi/yale/" + eident
      # Make Manifest & Sequence
      try:
            os.mkdir(basedir)
      except:
            pass # already exists
      fac.set_base_metadata_uri(basemd)
      fac.set_base_metadata_dir(basedir)

      mfst = fac.manifest(label=name)
      seq = mfst.sequence()

      # Now find all objects in that exhibition to be canvases
      q2 = """
      SELECT DISTINCT ?obj ?label {
       ?obj crm:P12i_was_present_at <%s> ;
            rdfs:label ?label .
      }
      """ % exhib

      sparql.setQuery(prefixes + q2)
      results2 = sparql.query().convert()

      for res2 in results2["results"]["bindings"]:
            uri = res2['obj']['value']
            label = res2['label']['value']
            ident = os.path.split(uri)[1]

            # Terrible code, just fetches individual results

            # should be for example "499"
            lident = "ycba_%s" % ident
            destimg = os.path.join(dest, lident) + '.jpg'
            imguri = imagePattern % ident
            if not os.path.exists(destimg):
                  print "Fetching: %s" % imguri
                  fh = urllib.urlopen(imguri)
                  data = fh.read()
                  fh.close()
                  if data:
                        fh = file(destimg, 'w')
                        fh.write(data)
                        fh.close()
                  else:
                        continue
            cvs = seq.canvas(ident=ident, label=label)
            anno = cvs.annotation()
            image = anno.image(lident, iiif=True)
            image.set_hw_from_iiif()
            cvs.set_hw(image.height, image.width) 

      mfst.toFile(compact=False)
      print "Finished %s" % name


