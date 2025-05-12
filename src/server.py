"""
@author: Alessandro Rebosio
@email: alessandro.rebosio@studio.unibo.it

@studentID: 0001130557
"""

from typing import Optional, Type
from datetime import datetime

import socket, logging, mimetypes, threading

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class HTTPServer:
    """A simple HTTP server that handles incoming connections and routes them to request handlers."""

    def __init__(
        self,
        server_address: tuple[str, int],
        RequestHandler: Optional[Type["HTTPRequestHandler"]] = None,
    ):
        """Initialize the server with the given address and request handler class."""
        self.server_address = server_address
        self.RequestHandler = RequestHandler or HTTPRequestHandler

    def serve(self) -> None:
        """Start the server and listen for incoming connections indefinitely."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(self.server_address)
            server_socket.listen(5)

            try:
                while True:
                    threading.Thread(
                        target=self.RequestHandler(
                            next(iter(server_socket.accept()))
                        ).handle_request,
                        daemon=True,
                    ).start()
            except KeyboardInterrupt:
                logging.info("server stopped manually")
            finally:
                server_socket.close()


class HTTPRequestHandler:
    """Base class for handling HTTP requests and generating responses."""

    HTTP_STATUS_MESSAGES = {
        200: "OK",
        201: "Created",
        204: "No Content",
        301: "Moved Permanently",
        302: "Found",
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Internal Server Error",
        501: "Not Implemented",
        502: "Bad Gateway",
        503: "Service Unavailable",
    }

    def __init__(self, client_socket: socket.socket):
        """Initialize the handler with a client socket connection."""
        self.client_socket = client_socket
        self.method = "GET"
        self.path: Optional[str] = "/www/index.html"
        self.http_version: str = "HTTP/1.1"

    def handle_request(self) -> None:
        """Handle an incoming HTTP request by parsing it and routing to the appropriate method."""
        try:
            self.parse_request()
            if hasattr(self, f"do_{self.method}"):
                getattr(self, f"do_{self.method}")()
            else:
                self.send_error(501)
        except ValueError:
            self.send_error(400)
        except Exception:
            self.send_error(500)
        finally:
            self.client_socket.close()

    def parse_request(self) -> None:
        """Parse the HTTP request line into method, path, and version."""
        try:
            request_line = self.client_socket.recv(1024).decode("utf-8").strip()
            self.method, self.path, self.http_version, *_ = request_line.split()
        except (IndexError, ValueError, UnicodeDecodeError, AttributeError):
            raise ValueError("Malformed HTTP request")

    def send_response(self, status_code: int = 200, content: bytes = "") -> None:
        """
        Send an HTTP response with the given status code and content.

        Args:
            status_code: HTTP status code
            content: Response body content
            content_type: MIME type of the content
        """
        headers = (
            f"{self.http_version} {status_code} {self.status_message(status_code)}\r\n"
            f"Content-Type: {self.guess_mime_type(self.path)}\r\n"
            f"Content-Length: {len(content)}\r\n"
            "\r\n"
        ).encode("utf-8")

        self.client_socket.sendall(headers)
        if self.method != "HEAD":
            if isinstance(content, str):
                content = content.encode("utf-8")
            self.client_socket.sendall(content)

        self.log_request("%s", status_code)

    def send_error(self, status_code: int):
        """Send an error response with the given status code."""
        content = f"""<!DOCTYPE html>
                    <html lang="en">
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>Error {status_code} ({self.status_message(status_code)})</title>
                            
                            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.6/dist/css/bootstrap.min.css" rel="stylesheet">
                            
                            <style>.full-height {{ height: 100vh; }}</style>
                        </head>
                        
                        <body>
                            <div class="container-fluid full-height d-flex justify-content-center align-items-center">
                                <div class="text-center">
                                    <h1 class="text-danger"><b>{status_code} - {self.status_message(status_code)}</b></h1>
                                    <p class="text-muted"><strong>Client IP:</strong> {self.address_str()}</p>
                                    <p>The requested resource was {self.status_message(status_code).lower()} on this server.</p>
                                </div>
                            </div>
                        </body>
                    </html>"""

        self.send_response(status_code, content.encode("utf-8"))

    def log_request(self, format, *args) -> None:
        """Log the request in Apache Common Log Format."""
        logging.info(
            f"{self.address_str()} - - [{datetime.now().strftime('%d/%b/%Y %H:%M:%S')}] "
            f'"{self.method} {self.path} {self.http_version}" {format % args} -'
        )

    def guess_mime_type(self, path: str) -> str:
        """Guess the MIME type based on the file extension."""
        return next(iter(mimetypes.guess_type(path))) or "text/html"

    def get_path(self) -> str:
        """Get the normalized request path."""
        return self.path or "/"

    def address_str(self) -> str:
        """Get the client address as a string."""
        try:
            return next(iter(self.client_socket.getpeername()))
        except OSError:
            return "0.0.0.0"

    def status_message(self, code: int) -> str:
        """Get the standard HTTP status message for a given code."""
        return self.HTTP_STATUS_MESSAGES.get(code, "Unknown")

    def do_GET(self) -> None:
        """Handle GET requests (to be implemented by subclasses)."""
        raise NotImplementedError("do_GET not implemented")

    def do_HEAD(self) -> None:
        """Handle HEAD requests (same as GET but without body)."""
        self.do_GET()


class MyServer(HTTPRequestHandler):
    """Custom HTTP request handler that serves files from the local filesystem."""

    def do_GET(self):
        try:
            safe_path = self.path.lstrip("/").replace("../", "").replace("..\\", "")

            with open(safe_path, "rb") as f:
                content = f.read()
            self.send_response(200, content)
        except (FileNotFoundError, IsADirectoryError):
            self.send_error(404)
        except PermissionError:
            self.send_error(403)
        except Exception:
            self.send_error(500)


if __name__ == "__main__":
    HTTPServer(("localhost", 8080), MyServer).serve()
