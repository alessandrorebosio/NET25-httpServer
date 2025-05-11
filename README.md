# Network Programming - Project

**70226 - Academic Year 2024/25, Bachelor's Degree in Computer Science and Engineering, University of Bologna - Cesena Campus**  
- **Instructors**: Professors Franco Callegati, Andrea Piroddi 
- **Programming Language**: Python

## Overview

This repository contains a simple HTTP server developed as part of the **Network Programming** course.  
The project aims to reinforce core concepts related to sockets, HTTP protocol, concurrency, and request handling, using Python.

The server is capable of:

- Handling multiple concurrent connections via `threading`
- Parsing and responding to basic HTTP requests (`GET`, `HEAD`)
- Serving static files from the `www/` directory
- Sending appropriate HTTP status codes (e.g., 200 OK, 404 Not Found)
- Logging each request in console
- Detecting MIME types using the built-in `mimetypes` module

## How to Run the Server
1. **Clone the Repository**
```bash
git clone https://github.com/alessandrorebosio/network-project.git
cd network-project
```

2. **Run the server:**
```bash
python3 src/server.py
```

3. **Access the server** in your browser:
```bash
http://localhost:8080/www/index.html
```

