import os
import socket
from datetime import datetime
from typing import Optional, Type


class HTTPServer:
    def __init__(
        self,
        server_address: tuple[str, int],
        RequestHandlerClass: Type["HTTPRequestHandler"],
    ):
        self.server_address = server_address
        self.RequestHandlerClass = RequestHandlerClass
        self.server_socket = None
        self.running = False

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(self.server_address)
        self.server_socket.listen(5)
        self.running = True

        try:
            while self.running:
                client_socket, _ = self.server_socket.accept()
                self.RequestHandlerClass(client_socket).handle_request()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        if self.server_socket:
            self.running = False
            self.server_socket.close()


class HTTPRequestHandler:
    def __init__(self, client_socket: socket.socket, log_file="log/server.log"):
        self.client_socket = client_socket
        self.path: Optional[str] = None
        self.log_file = log_file

    def handle_request(self):
        try:
            request = self.client_socket.recv(1024).decode("utf-8")
            if not request:
                return

            self.method, self.path = self.parse_request(request)

            if self.method == "GET":
                self.do_GET()
            else:
                self.send_error(501, "Method Not Implemented")
        except Exception as e:
            self.send_error(500, f"Internal Server Error: {e}")
        finally:
            self.client_socket.close()

    def parse_request(self, request: str) -> tuple[str, str]:
        self.request = request.splitlines()[0] if request else ""
        parts = self.request.split()
        return (parts[0], parts[1]) if len(parts) >= 2 else ("", "")

    def send_response(self, code: int, content: bytes, message: Optional[str] = None):
        header = (
            f"HTTP/1.1 {code} {message or ''}\r\n"
            f"Content-Type: text/html\r\n"
            f"Content-Length: {len(content)}\r\n"
            f"\r\n"
        )
        self.client_socket.sendall(header.encode("utf-8") + content)

        self.log_message('"%s" %s %s', self.request, str(code), message or "-")

    def send_error(self, code: int, message: str):
        body = f"<h1>{code} {message}</h1>".encode("utf-8")
        self.send_response(code, body, message)

    def log_message(self, format, *args):
        timestamp = datetime.now().strftime("[%d/%b/%Y %H:%M:%S]")
        log_entry = f"{self.address_string()} - - {timestamp} {format % args}\n"
        print(log_entry, end="")

        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        try:
            with open(self.log_file, "a") as log_file:
                log_file.write(log_entry)
        except IOError as e:
            print(f"Unable to write to log: {e}")

    def get_path(self) -> str:
        return self.path

    def address_string(self):
        try:
            return self.client_socket.getpeername()[0]
        except:
            return "0.0.0.0"

    def do_GET(self):
        raise NotImplementedError("do_GET non implementato")


class MyServer(HTTPRequestHandler):
    BASE_DIR = "www"

    def do_GET(self):
        path = self.get_path()
        if path == "/":
            path = "/index.html"

        file_path = os.path.join(self.BASE_DIR, path.lstrip("/"))

        if os.path.isfile(file_path):
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200, content, "OK")
        else:
            self.send_error(404, "File Not Found")


if __name__ == "__main__":
    HTTPServer(("localhost", 8080), MyServer).start()
