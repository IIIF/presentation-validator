from factory import ManifestFactory
from SPARQLWrapper import SPARQLWrapper, JSON 
import os
import urllib

fac = ManifestFactory()
fac.set_base_image_uri("http://iiif-dev.localhost/services/2.0")
fac.set_iiif_image_info(version="2.0")

basemd = "http://localhost/prezi/"
basedir = "/path/to/htdocs/prezi"

sparql = SPARQLWrapper("http://collection.britishmuseum.org/sparql")
sparql.setReturnFormat(JSON)

dest = "/path/to/images/britishmuseum"

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
SELECT DISTINCT ?obj ?prefid {
 ?obj crm:P46i_forms_part_of <http://collection.britishmuseum.org/id/collection/Lewis-Chessmen> ; 
      crm:P48_has_preferred_identifier ?prefid ;
      crm:P138i_has_representation ?image .
}
"""

queries = {
      'mainImage' : 'bmo:PX_has_main_representation ?mainImage',
      'desc' : 'bmo:PX_physical_description ?desc',
      'comment' : 'bmo:PX_curatorial_comment ?comment',
      'hist' : 'bmo:PX_exhibition_history ?hist',
      'typeLabel' : 'bmo:PX_object_type ?otype . ?otype skos:prefLabel ?typeLabel .',
      'conceptLabel' : 'crm:P128_carries ?c1 . ?c1 crm:P129_is_about ?concept . ?concept skos:prefLabel ?conceptLabel .',
      'placeLabel' : 'crm:P55_has_current_location ?place . ?place rdfs:label ?placeLabel .',
      'title' : 'crm:P102_has_title ?t . ?t rdfs:label ?title'
}

qt = """
SELECT DISTINCT ?%s {
<%s> %s    
}
"""

# Each object in the collection is a Manifest, with multiple images
# Then we create a Collection for those Manifests

sparql.setQuery(prefixes + q)
results = sparql.query().convert()

coll = fac.collection()

for result in results["results"]["bindings"]:
      uri = result['obj']['value']
      prefid = result['prefid']['value']
      if not prefid.startswith(uri):
            continue

      # Terrible code, just fetches individual results
      thing = {'id': uri}

      # first get the images and check that they're not depicting more than one thing
      q2 = qt % ('image', uri, 'crm:P138i_has_representation ?image')
      sparql.setQuery(q2)
      imgres = sparql.query().convert()
      imagelist = []
      for i in imgres['results']['bindings']:
            imguri = i['image']['value']
            # Now check if it's P138i_has_representation for more than one thing
            q3 = "SELECT DISTINCT ?obj { ?obj crm:P138i_has_representation <%s> }" % imguri
            sparql.setQuery(q3)
            objres = sparql.query().convert()

            okay = 1

            if okay:
                  ident = os.path.split(imguri)[1]
                  destimg = os.path.join(dest, ident)
                  if not os.path.exists(destimg):
                        fh = urllib.urlopen(imguri)
                        data = fh.read()
                        fh.close()
                        fh = file(destimg, 'w')
                        fh.write(data)
                        fh.close()

      for (k,v) in queries.items():
            thing[k] = []
            q2 = qt % (k, uri, v)
            sparql.setQuery(q2)
            results2 = sparql.query().convert()
            for r2 in results2['results']['bindings']:
                  thing[k].append(r2[k]['value'])


      # And now make the Manifest
      objid = os.path.split(uri)[-1]
      try:
            os.mkdir(basedir + '/' + objid)
      except:
            pass # already exists
      fac.set_base_metadata_uri(basemd + objid)
      fac.set_base_metadata_dir(basedir + '/' + objid)

      mfst = fac.manifest()
      # Most British Museum objects don't have titles
      lbl = thing.get('title')
      # Maybe there's some with more than one?
      if len(lbl) > 1:
            mfst.label = lbl
      elif len(lbl):
            mfst.label = lbl[0]
      else: 
            mfst.label = thing.get('typeLabel', [''])[0]

      desc = thing.get('desc')
      if len(desc) > 1:
            desc.sort(key=lambda x: len(x), reverse=True)
            # longest description first
            mfst.description = desc
      elif len(desc):
            mfst.description = desc[0]

      # curatorial comment --> metadata
      comment = thing.get('comment')
      if len(comment) > 1:
            comment.sort(key=lambda x: len(x), reverse=True)
            mfst.set_metadata({"Curatorial Comment": comment})
      elif len(comment):
            mfst.set_metadata({"Curatorial Comment": comment[0]})
      # exhibition history --> metadata
      hist = thing.get('hist')
      if len(hist) > 1:
            mfst.set_metadata({"Exhibition History": hist})
      elif len(hist):
            mfst.set_metadata({"Exhibition History": hist[0]})

      subj = thing.get('conceptLabel')
      if len(subj) > -1:
            mfst.set_metadata({"Subject": subj})
      elif len(subj):
            mfst.set_metadata({"Subject": subj[0]})
      
      place = thing.get('placeLabel')
      if len(place):
            mfst.set_metadata({"Location": place[0]})

      # Okay, do we have a main representation?
      main = thing.get('mainImage')
      rest = imagelist
      if main:
            images = [main[0]]
            rest.remove(main[0])
            images.extend(rest)
      else:
            images = rest

      seq = mfst.sequence()
      c = 1
      for img in images:
            ident = 'view%s' % c
            cvs = seq.canvas(ident, label="View %s" % c)
            anno = cvs.annotation()
            imgid = os.path.split(img)[1][:-4]
            image = anno.image(imgid, iiif=True)
            image.set_hw_from_iiif()
            cvs.set_hw(image.height, image.width) 
            c += 1

      mfst.toFile(compact=False)
      print "Finished %s" % objid
      col.add_manifest(mfst)


### Notes
# Example collections
# http://collection.britishmuseum.org/id/collection/Lewis-Chessmen
# total: 8694 collections with 1,686,430 images
# eg object:
# http://collection.britishmuseum.org/resource?uri=http%3A%2F%2Fcollection.britishmuseum.org%2Fid%2Fobject%2FMCM7485
# NB -- Items have multiple identifiers so will appear multiple times in queries.
