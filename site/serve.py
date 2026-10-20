#!/usr/bin/env python3
"""Preview site/public on http://127.0.0.1:8000 with the headers from site/public/_headers applied, so the
Content-Security-Policy is enforced the way Cloudflare Pages enforces it. Local preview only.

    python3 site/build.py && python3 site/serve.py [--port 8000] [--dir site/public]

Supports the subset of the _headers format this site uses: a path line ("/*", "/" or an exact path) followed by
indented "Name: value" lines.
"""
import argparse
import functools
import http.server
import os
import socketserver

HERE = os.path.dirname(os.path.abspath(__file__))


def parse_headers(path):
    rules, cur = [], None
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError:
        return rules
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[0].isspace():
            cur = (line.strip(), [])
            rules.append(cur)
        elif cur and ":" in line:
            k, v = line.strip().split(":", 1)
            cur[1].append((k.strip(), v.strip()))
    return rules


def matches(pattern, path):
    if pattern.endswith("*"):
        return path.startswith(pattern[:-1])
    return path == pattern


class Handler(http.server.SimpleHTTPRequestHandler):
    rules = []

    def end_headers(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        for pattern, headers in self.rules:
            if matches(pattern, path):
                for k, v in headers:
                    self.send_header(k, v)
        super().end_headers()

    def log_message(self, fmt, *args):
        pass


def make_server(directory, port=0):
    Handler.rules = parse_headers(os.path.join(directory, "_headers"))
    handler = functools.partial(Handler, directory=directory)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    return socketserver.ThreadingTCPServer(("127.0.0.1", port), handler)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--dir", default=os.path.join(HERE, "public"))
    a = ap.parse_args()
    httpd = make_server(os.path.abspath(a.dir), a.port)
    print("serving %s on http://127.0.0.1:%d/ (Ctrl+C to stop)" % (a.dir, httpd.server_address[1]))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
