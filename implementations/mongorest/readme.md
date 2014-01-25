

Heavily modified from https://github.com/fatiherikli/kule

Backend is MongoDB:
* http://www.mongodb.org/downloads

* Download, unpack, mkdir -p data/db
* Startup: ./bin/mongod -dbpath data/db

Python Library Requirements:
* bottle
* pymongo (+ bson)

Usage:
* Stand alone server: python ./kule.py --database annotations
* Or with mod_wsgi in apache or other, see: http://bottlepy.org/docs/dev/deployment.html

Handles GET, POST, PUT, DELETE for json following the URI patterns in the metadata api recommendations.

Extras -- a simple "ResourceList" when you GET a resource type without an identifier, eg:
    GET http://localhost:8000/iiif/book1/annotation 
will return all of the known annotations (up to limit of 1000)

Some useful CURL command lines:

* curl http://localhost:8000/iiif/book1/list/p1.json
* curl -X POST -H "Content-Type: application/json" --data @anno2.json http://localhost:8000/iiif/book1/annotation
* curl -X PUT  -H "Content-Type: application/json" --data @anno.json http://localhost:8000/iiif/book1/annotation/af78b7418-ee92-4ebd-ae86-4783c9e73b65
* curl -X DELETE http://localhost:8000/iiif/book1/annotation/aa57702cf-7043-40d7-a42d-20232000f6dd.json


Things to do:
* Validate the JSON
* Allow content negotiation based on JSON-LD frames
* _md5 property to check for duplicates
* Handle media fragment searches
* Suggestions?

Notes as to why I didn't just use Kule:
* No support for JSON-LD media type
* Jsonify was harder than necessary to override, and needed significant changes
* Desirable to use custom sort order JSON hack.
* Added support for human readable vs compressed JSON serialization
* Much of the magic in Kule is weak... for example get_collection could be overridden to handle GET on /collection ... but is needed for the internals to get the MongoDB collection from the database. Duh.
* Didn't support PUT to create new resource with identifier.
* Magic added for JSONLD @id / mongodb _id mapping, with app side assignment.
* It was a good learning experience :)





