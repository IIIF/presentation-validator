import json
from presentation_validator.validator import check_manifest, fetch_manifest

from bottle import Bottle, request, response, template,static_file

def create_app():
    app = Bottle()

    @app.hook('after_request')
    def add_headers():
        methods = 'GET,POST,OPTIONS'
        headers = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = methods
        response.headers['Access-Control-Allow-Headers'] = headers
        response.headers['Allow'] = methods

    @app.route('/validate', method='OPTIONS')
    def empty_response():
        return ''

    @app.route('/validate', method='GET')
    def get_response():
        url = request.query.get('url', '')
        version = request.query.get('version', None)
        accept = True if request.query.get('accept') and request.query.get('accept') == 'true' else False

        url = url.strip()

        try:
            data, warnings = fetch_manifest(url, accept, version)
        except Exception as error:
            return {
                'okay': 0, 
                'error': f'Cannot fetch url. Got "{error}"', 
                'url': url
            }

        result = check_manifest(data, version, url, warnings)  

        response.content_type = 'application/json'
        return result

    @app.route('/validate', method='POST')
    def post_response():
        data = request.json

        if data is None:
            try:
                body = request.body.read()
                data = json.loads(body.decode('utf-8'))
            except Exception:
                response.status = 400
                return {"error": "Invalid JSON"}
        # Extract version 
        version = request.query.get('version')

        # If still not present → None
        if not version:
            version = None        

        result = check_manifest(data, version)  

        response.content_type = 'application/json'
        return result

    @app.route('/')
    def index():
        return template('views/index.html')

    @app.route('/css/<filepath:path>')
    def css(filepath):
        return static_file(filepath, root='./static/css')    

    @app.route('/img/<filepath:path>')
    def img(filepath):
        return static_file(filepath, root='./static/img')

    @app.route('/favicon.ico')
    def favicon():
        return static_file('favicon.ico', root='./static/img')
    
    return app    
