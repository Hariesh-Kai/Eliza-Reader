from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = "0.0.0.0"
PORT = 8000
AUDIO_FILE = Path("audio/chapters/chapter_001.wav")


class AudioHandler(SimpleHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/":
            html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Eliza Reader</title>
</head>

<body>
    <h1>🎧 Eliza Reader</h1>

    <p>Chapter 001</p>

    <audio controls style="width: 600px;">
        <source src="/audio/chapters/chapter_001.wav" type="audio/wav">
        Your browser does not support audio playback.
    </audio>

</body>
</html>
"""

            data = html.encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()

            try:
                self.wfile.write(data)
            except BrokenPipeError:
                pass

            return

        if self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        if self.path == "/audio/chapters/chapter_001.wav":

            if not AUDIO_FILE.exists():
                self.send_error(404, "Audio file not found")
                return

            try:
                file_size = AUDIO_FILE.stat().st_size

                self.send_response(200)
                self.send_header("Content-Type", "audio/wav")
                self.send_header("Content-Length", str(file_size))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

                with open(AUDIO_FILE, "rb") as audio:
                    while True:
                        chunk = audio.read(64 * 1024)

                        if not chunk:
                            break

                        self.wfile.write(chunk)

            except (BrokenPipeError, ConnectionResetError):
                pass

            return

        self.send_error(404)


if not AUDIO_FILE.exists():
    print("ERROR: chapter_001.wav not found.")
    raise SystemExit(1)


print("=" * 70)
print("ELIZA READER")
print("Audio Player V2")
print("=" * 70)
print()

print(f"Audio : {AUDIO_FILE}")
print(f"Size  : {AUDIO_FILE.stat().st_size:,} bytes")
print()

print(f"Server running on port {PORT}")
print("Open the forwarded port in your browser.")
print("Press CTRL+C to stop.")
print()


server = ThreadingHTTPServer((HOST, PORT), AudioHandler)

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped.")
    server.server_close()