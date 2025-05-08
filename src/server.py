from typing import Optional, Type
from datetime import datetime

import socket, logging, mimetypes, threading

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class HTTPServer:

    def __init__(
        self,
        server_address: tuple[str, int],
        RequestHandler: Optional[Type["HTTPRequestHandler"]] = None,
    ):
        self.server_address = server_address
        self.RequestHandler = RequestHandler or HTTPRequestHandler

    def serve(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(self.server_address)
            server_socket.listen(5)

            try:
                while True:
                    conn, addr = server_socket.accept()
                    threading.Thread(
                        target=self.RequestHandler(conn).handle_request, daemon=True
                    ).start()
            except KeyboardInterrupt:
                logging.info("server stopped manually")
            finally:
                server_socket.close()


class HTTPRequestHandler:

    def __init__(self, client_socket: socket.socket):
        self.client_socket = client_socket
        self.method = "GET"
        self.path: Optional[str] = "/"
        self.http_version: str = "HTTP/1.1"

    def handle_request(self) -> None:
        try:
            self.parse_request()
            if hasattr(self, f"do_{self.method}"):
                getattr(self, f"do_{self.method}")()
            else:
                self.send_error(501, f"Method {self.method} not implemented")
        finally:
            self.client_socket.close()

    def parse_request(self) -> None:
        try:
            request_line = self.client_socket.recv(1024).decode("utf-8").strip()
            self.method, self.path, self.http_version, *_ = request_line.split()
        except (IndexError, ValueError, UnicodeDecodeError, AttributeError):
            raise ValueError("Malformed HTTP request")

    def send_response(
        self, status_code: int = 200, content: str = "", content_type: str = "text/html"
    ) -> None:
        response = (
            f"{self.http_version} {status_code}\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(content)}\r\n"
            "\r\n"
        )
        if self.method != "HEAD":
            response += f"{content}\r\n"

        self.client_socket.sendall(response.encode("utf-8"))
        self.log_request("%s", status_code)

    def guess_mime_type(self, path: str) -> str:
        mime_type, _ = mimetypes.guess_type(path)
        return mime_type or "application/octet-stream"

    def send_error(self, status_code: int, content: str):
        self.send_response(status_code, content, self.guess_mime_type(self.path))

    def log_request(self, format, *args) -> None:
        logging.info(
            f"{self.address_str()} - - [{datetime.now().strftime('%d/%b/%Y %H:%M:%S')}] "
            f'"{self.method} {self.path} {self.http_version}" {format % args} -'
        )

    def get_path(self) -> str:
        return self.path or "/"

    def address_str(self) -> str:
        try:
            return next(iter(self.client_socket.getpeername()))
        except OSError:
            return "0.0.0.0"

    def do_GET(self):
        raise NotImplementedError("do_GET not implemented")

    def do_HEAD(self):
        self.do_GET()


class MyServer(HTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"

        try:
            with open("www" + self.path, "r", encoding="utf-8") as f:
                content = f.read()
            self.send_response(200, content, self.guess_mime_type(self.path))
        except FileNotFoundError:
            self.send_error(404, "<h1>404 Not Found</h1>")


if __name__ == "__main__":
    HTTPServer(("localhost", 8080), MyServer).serve()
