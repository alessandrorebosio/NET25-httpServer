import socket


class HTTPServer:
    def __init__(self, server_address, RequestHandlerClass):
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
    def __init__(self, client_socket):
        self.client_socket = client_socket
        self.www_dir = "www"

    def handle_request(self):
        request = self.client_socket.recv(1024).decode("utf-8")
        method, path = self.parse_request(request)

        if not request:
            self.client_socket.close()
            return

        if method == "GET":
            self.do_GET()
        else:
            self.send_response(501)

        self.client_socket.close()

    def parse_request(self, request):
        print(request)
        return request, None

    def log(self):
        pass

    def send_response(self):
        pass

    def do_GET(self):
        raise


class MyServer(HTTPRequestHandler):
    def do_GET(self):
        pass


if __name__ == "__main__":

    server = HTTPServer(("localhost", 8080), MyServer)

    try:
        server.start()
    except Exception as e:
        print("Server error:", e)
        server.stop()
