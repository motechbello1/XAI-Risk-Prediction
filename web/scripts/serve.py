"""Local preview of the same static site and Python API used on Vercel."""
import sys
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'api'))
from index import handler


class LocalHandler(SimpleHTTPRequestHandler):
    respond = handler.respond

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'public'), **kwargs)

    def do_POST(self):
        if self.path == '/api/index':
            handler.do_POST(self)
        else:
            self.send_error(404)

    def do_GET(self):
        if self.path == '/api/index':
            handler.do_GET(self)
        else:
            super().do_GET()


if __name__ == '__main__':
    server = ThreadingHTTPServer(('0.0.0.0', 3000), LocalHandler)
    print('Clarity preview ready at http://localhost:3000', flush=True)
    server.serve_forever()
