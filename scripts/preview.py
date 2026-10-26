"""Design-only preview when Docker/PostgreSQL isn't available. Read-only, no fake API."""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--site',choices=['store','super','regional'],default='store')
parser.add_argument('--port',type=int,default=3000)
args=parser.parse_args()
class Handler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        from urllib.parse import urlsplit
        path=urlsplit(path).path
        if path.startswith('/shared/'):
            base=ROOT/'apps'/'shared'
            rel=path[len('/shared/'):]
        else:
            base=ROOT/'apps'/args.site
            rel=path.lstrip('/')
        candidate=(base/rel).resolve()
        if not candidate.is_relative_to(base.resolve()): return str(base/'__not_found__')
        if candidate.is_file():return str(candidate)
        return str(base/'index.html')
    def do_GET(self):
        if self.path.startswith('/api/'):
            self.send_response(503)
            self.send_header('Content-Type','application/json')
            self.end_headers()
            self.wfile.write(b'{"detail":"Preview only: connect local PostgreSQL via Docker Compose"}')
            return
        super().do_GET()
    def do_POST(self):
        self.send_response(503);self.end_headers()
print(f'READ-ONLY design preview: http://localhost:{args.port} (site={args.site}). Database actions unavailable.')
ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
