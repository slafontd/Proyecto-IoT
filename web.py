from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        try:
            with open("data.txt", "r") as f:
                data = f.read()
        except:
            data = "No hay datos aún"

        html = f"""
        <html>
        <head>
            <meta http-equiv="refresh" content="2">
        </head>
        <body>
            <h1>Sistema IoT en tiempo real</h1>
            <h2>{data}</h2>
        </body>
        </html>
        """

        self.wfile.write(html.encode())

server = HTTPServer(("0.0.0.0", 8000), Handler)
server.serve_forever()