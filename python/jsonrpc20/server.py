import json
from http.server import BaseHTTPRequestHandler, HTTPServer


def add(params):
    if isinstance(params, list) and len(params) == 2:
        return params[0] + params[1]
    return -1 # 에러 상황


class JSONRPCRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        request_obj = json.loads(post_data)

        response_obj = {
            "jsonrpc": "2.0",
            "id": request_obj.get("id")
        }

        try:
            method_name = request_obj["method"]
            params = request_obj.get("params", [])

            if method_name == "add":
                response_obj["result"] = add(params)
            else:
                response_obj["error"] = {
                    "code": -32601,
                    "message": "Method not found"
                }

        except KeyError:
            response_obj["error"] = {
                "code": -32600,
                "message": "Invalid Request"
            }

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response_obj).encode('utf-8'))


def run_server(server_class=HTTPServer, handler_class=JSONRPCRequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting JSON-RPC 2.0 server on port {port}...")
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()