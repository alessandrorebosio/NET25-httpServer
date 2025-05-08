from typing import Optional, Type
from datetime import datetime

import socket, logging

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
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(self.server_address)
        server_socket.listen(5)

        try:
            while True:
                conn, addr = server_socket.accept()
                self.RequestHandler(conn).handle_request()
        except KeyboardInterrupt:
            return "server stopped"
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
            request_line = self.client_socket.recv(1024).decode("utf-8").splitlines()[0]
            self.method, self.path, self.http_version, *_ = request_line.split()
        except (IndexError, ValueError, UnicodeDecodeError, AttributeError):
            pass

    def send_response(self, status_code: int = 200, content: str = "") -> None:
        response = (
            f"HTTP/1.1 {status_code}\r\n"
            f"Content-Type: text/html\r\n"
            f"Content-Length: {len(content)}\r\n\r\n"
            f"{content}"
        )
        self.client_socket.sendall(response.encode("utf-8"))
        self.log_request("%s", status_code)

    def send_error(self, status_code: int, message: str):
        self.send_response(status_code)

    def log_request(self, format, *args) -> None:
        logging.info(
            f"{self.address_str()} - - [{datetime.now().strftime('%d/%b/%Y %H:%M:%S')}]] "
            f'"{self.method} {self.path} {self.http_version}" {format % args} -'
        )

    def get_path(self) -> str:
        return self.path or "/"

    def address_str(self) -> str:
        try:
            return self.client_socket.getpeername()[0]
        except OSError:
            return "0.0.0.0"

    def do_GET(self):
        raise NotImplementedError("do_GET not implemented")


class MyServer(HTTPRequestHandler):
    def do_GET(self) -> None:
        response_content = f"""
        <html>
            <body>
                <h1>Hello World</h1>
                <p>Path: {self.get_path()}</p>
                <p>Client IP: {self.address_str()}</p>
            </body>
        </html>
        """
        self.send_response(200, response_content)


if __name__ == "__main__":
    HTTPServer(("localhost", 8080), MyServer).serve()
