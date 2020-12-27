'''
A Simple HTTP Server.
Servers:
    AsyncHTTPServer:     Async HTTP server based on asyncio
    ThreadedHTTPServer:  Threaded HTTP Server(vulnerable to DDoS Attacks)
Apps:
    App:        A Simple Flask-like App class with @App.route(route, methods=['GET', 'POST'])
    Applicaion: Same as App
'''
from .app import *
from .srv import *
__version__ = 1.1
