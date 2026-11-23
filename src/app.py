"""Máy chủ demo cục bộ: python src/app.py. Không dùng cho Internet công khai."""
import argparse
import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from core import RuleError, connect, init_db, mutate, snapshot

BASE = Path(__file__).resolve().parent


def make_handler(db_path):
    class Handler(BaseHTTPRequestHandler):
        def reply(self, code, payload, kind='application/json; charset=utf-8'):
            raw = json.dumps(payload,ensure_ascii=False).encode('utf-8') if not isinstance(payload,bytes) else payload
            self.send_response(code)
            self.send_header('Content-Type',kind)
            self.send_header('Content-Length',str(len(raw)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/api/state':
                with connect(db_path) as db:
                    # Một giao dịch đọc cho snapshot nhất quán.
                    db.execute('BEGIN')
                    state = snapshot(db)
                return self.reply(200,state)
            files = {'/':('index.html','text/html; charset=utf-8'),
                     '/app.js':('app.js','text/javascript; charset=utf-8'),
                     '/style.css':('style.css','text/css; charset=utf-8')}
            if path in files:
                filename,kind = files[path]
                return self.reply(200,(BASE/'static'/filename).read_bytes(),kind)
            self.reply(404,{'error':'Không tìm thấy tài nguyên.'})

        def do_POST(self):
            # Chỉ nhận JSON cùng origin; không bật CORS, giới hạn body 64 KiB.
            if self.headers.get('Origin') not in (None, f'http://{self.headers.get("Host")}'):
                return self.reply(403,{'error':'Origin không hợp lệ.'})
            if self.headers.get('Content-Type','').split(';')[0].strip() != 'application/json':
                return self.reply(415,{'error':'Yêu cầu application/json.'})
            path = urlsplit(self.path).path
            if not path.startswith('/api/'):
                return self.reply(404,{'error':'Không tìm thấy API.'})
            try:
                length = int(self.headers.get('Content-Length','0'))
                if length < 1 or length > 65536:
                    return self.reply(413,{'error':'Dung lượng yêu cầu không hợp lệ.'})
                data = json.loads(self.rfile.read(length))
                if not isinstance(data,dict):
                    raise RuleError('Nội dung JSON phải là object.')
                with connect(db_path) as db:
                    db.execute('BEGIN IMMEDIATE')
                    identifier = mutate(db,path[5:],data)
                self.reply(200,{'ok':True,'id':identifier})
            except (RuleError,ValueError,UnicodeDecodeError) as exc:
                self.reply(400,{'error':str(exc) if isinstance(exc,RuleError) else 'JSON hoặc dữ liệu không hợp lệ.'})
            except sqlite3.IntegrityError:
                self.reply(409,{'error':'Mã/ISBN đã tồn tại hoặc dữ liệu còn được tham chiếu.'})
            except sqlite3.OperationalError:
                self.reply(503,{'error':'Cơ sở dữ liệu đang bận hoặc chưa sẵn sàng; hãy thử lại.'})
    return Handler


def main():
    parser = argparse.ArgumentParser(description='Lab Quản lý thư viện - Dương Gia')
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--db',type=Path,default=BASE/'data'/'library.db')
    args = parser.parse_args()
    args.db.parent.mkdir(parents=True,exist_ok=True)
    init_db(args.db)
    server = ThreadingHTTPServer(('127.0.0.1',args.port),make_handler(args.db))
    print(f'Library Lab: http://127.0.0.1:{args.port} | Ctrl+C de dung',flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
