from typing import Optional, Type
import socket


class HTTPServer:

    def __init__(
        self,
        server_address: tuple[str, int],
        RequestHandler: Optional[Type["HTTPRequestHandler"]] = None,
    ):
        self.server_address = server_address
        self.RequestHandler = RequestHandler

    def serve(self):
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

    def handle_request(self):
        self.do_GET()

    def do_GET(self):
        raise NotImplementedError("Method do_GET not implemented")


class MyServer(HTTPRequestHandler):
    def do_GET(self):
        print("OK")


if __name__ == "__main__":
    HTTPServer(("localhost", 8080), MyServer).serve()
