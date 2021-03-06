"""
Asynchronous HTTP Server.
"""

import datetime, time, threading
from ..http_support.request_parsing import Request
from ..http_support.responses import Response
from ..http_support.formats import reply_format
from ..http_support.parse_time import gettime as _gettime
from ..http_support.environ import get_environ
from .version import version
import uuid
from io import StringIO
import traceback, sys
if float(sys.version[:3]) < 3.3:
    raise DeprecationWarning('python {} deprecated'.format(sys.version[:5]))
try:
    import asyncio
except:
    raise ImportError("Can't find package 'asyncio'. "
                      "Make sure you have asyncio installed"
                      " before running this script again.")

__all__ = ("AsyncHTTPServer",)

coroutine = asyncio.coroutine

class IsNotACoroutineError(Exception):
    pass

class AsyncHTTPServer:
    """
    Async HTTP Server that supports Asynchronous IO Coroutines.
    Note: AsyncHTTPServer Only supports python 3.3 and above. 
    For python 3.3, you'll need to install asyncio from PyPI.
    Note: AsyncHTTPServer currently does not support running 
    on multiple CPU Cores.
    Usage:
    >>> from serverhttp import *
    >>> app = App(__name__)
    >>> @coroutine
    @app.route("/", ["GET"])
    def test(environ):
        return Response("200 OK")

    >>> s = AsyncHTTPServer(app=app)
    >>> s.serve_forever("127.0.0.1", 60000)
    """
    use_ipv6 = False
    def __init__(self, name='', app=None, debug=True, sslcontext=None,
    			# multicore=False,
				):
        # self.multicore = multicore
        self._debug_ = debug
        self.server = version
        self.functions = dict()
        self.threads = []
        self.reply_format = reply_format
        if app:
            self.app = app
            self.app.server = self.server
            self.name = self.app.name
            self.app.prepare_for_deploy(self)
        else:
            self.name = name
        self.sslcontext = sslcontext
        
    @asyncio.coroutine
    def _serve_one_client(self, reader, writer):
        import time
        sid = uuid.uuid4().hex
        addr = writer.get_extra_info('peername')
        reply_format = self.reply_format
        timeout = 0.1
        try:
            while True:
                txt = yield from reader.read(65535)
                txt = txt.decode()
                if not txt:
                    yield from asyncio.sleep(timeout)
                    timeout += 0.1
                    if timeout > 10:
                        break
                    continue
                req = Request(txt)
                reply_obj = yield from self._handle_request(req)
                cookie = 'session-id:{}'.format(sid)
                if len(reply_obj.cookies)==0:
                    reply_obj.cookies = cookie
                else:
                    reply_obj.cookies = reply_obj.cookies + ';' + cookie
                print(addr[0], '-', '"'+req.text+'"', '-', reply_obj.status)
                reply = str(reply_obj).encode()
                writer.write(reply)
                yield from writer.drain()
            writer.close()
            return
        except KeyboardInterrupt:
            writer.close()
            return

    # Server's default exception handler coroutines
    def _404(self, env):
        return Response('404 Not Found', 'text/html', '<h1>404 not found')
    def _405(self, env):
        return Response('405 Method Not Allowed')
    def _500(self, env):
        return Response("500 Server Error")

    @asyncio.coroutine
    def _handle_request(self, request):
        splitted = request.text.split()
        env = get_environ(request)
        try:
            path = splitted[1].split('?')[0]
        except:
            path = splitted[1]
        method = splitted[0]
        try:
            res = self.functions[path]
        except:
            res = self._404
        try:
            res = res[method]
        except:
            if res == self._404:
                pass
            else: res = self._405
        try:
            if asyncio.iscoroutine(res):
                res = yield from res(env)
            else: res = res(env)
        except BaseException as e:
            if self._debug_:
                i = StringIO()
                traceback.print_exc(file=i)
                traceback.print_exc()
                i.seek(0)
                d = i.read()
                res = Response('500 Server Error', 'text/plain', '500 server error:\r\n'+d)
            else:
                res = Response('500 Server Error', 'text/plain', '500 server error')
        return res
    def init(self, host, port):
        loop = asyncio.get_event_loop()
        coro = asyncio.start_server(
            self._serve_one_client, 
            host=host, port=port, loop=loop, 
            ssl=self.sslcontext)
        srv = loop.run_until_complete(coro)
        return srv, loop
    def serve_forever(self, host, port):
        srv, loop = self.init(host, port)
        print()
        if self.name:
            print('* Serving App {}'.format(self.name))
        print('* Serving On http://{host}:{port}'.format(host=host, port=port))
        print('* Press <CTRL-C> To Quit')
        workers = []
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            print()
            srv.close()
            loop.run_until_complete(srv.wait_closed())
            loop.close()
