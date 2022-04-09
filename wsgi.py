from Statistics import app
from asgiref.wsgi import WsgiToAsgi

app = WsgiToAsgi(app)
