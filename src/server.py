from datetime import datetime
from typing import Optional, Type
import socket


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
                client_socket, client_address = self.server_socket.accept()
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
    def __init__(self, client_socket: socket.socket):
        self.client_socket = client_socket
        self.path: Optional[str] = None

    def handle_request(self):
        try:
            request = self.client_socket.recv(1024).decode("utf-8")
            if not request:
                return

            self.method, self.path = self.parse_request(request)

            if self.method == "GET":
                self.do_GET()
            else:
                self.send_response(501, "Method Not Implemented")
        except (UnicodeDecodeError, ConnectionError) as e:
            self.send_error(500, f"Internal Server Error: {e}")
        finally:
            self.client_socket.close()

    def parse_request(self, request: str) -> tuple[str, str]:
        self.request = request.splitlines()[0] if request else ""
        parts = self.request.split()

        return (parts[0], parts[1]) if len(parts) >= 2 else ("", "")

    def send_response(self, code: int, message=None):
        self.log_message(
            '"%s" %s %s',
            self.request,
            str(code),
            message if message is not None else "-",
        )

    def log_message(self, format, *args):
        timestamp = datetime.now().strftime("[%d/%b/%Y %H:%M:%S]")
        print(f"{self.address_string()} - - {timestamp} {format % args} ")

    def get_path(self):
        return self.path

    def address_string(self):
        try:
            return self.client_socket.getpeername()[0]
        except:
            return "0.0.0.0"

    def do_GET(self):
        raise NotImplementedError("Method do_GET, not implemented")


class MyServer(HTTPRequestHandler):
    def do_GET(self):
        self.send_response(200, "OK")


if __name__ == "__main__":

    server = HTTPServer(("localhost", 8080), MyServer)

    try:
        server.start()
    except Exception as e:
        print("Server error:", e)
        server.stop()
