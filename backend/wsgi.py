from toolmatching import create_app
from waitress import serve

serve(create_app(), listen='0.0.0.0:8080', url_prefix='/app')
