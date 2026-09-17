from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = "0.0.0.0"
PORT = 8001

VOICE_DIR = Path("voice_tests")


class VoicePlayerHandler(SimpleHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/":
            html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Eliza Reader - Voice Test</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 700px;
            margin: 40px auto;
            padding: 20px;
        }

        .voice {
            margin: 25px 0;
        }

        audio {
            width: 100%;
        }
    </style>
</head>

<body>

    <h1>🎧 Eliza Reader</h1>

    <p>Female Voice Casting Test</p>

    <div class="voice">
        <h2>🎙 Narrator</h2>
        <audio controls>
            <source src="/narrator.wav" type="audio/wav">
        </audio>
    </div>

    <div class="voice">
        <h2>🎭 Pei Qian</h2>
        <audio controls>
            <source src="/pei_qian.wav" type="audio/wav">
        </audio>
    </div>

    <div class="voice">
        <h2>⚙️ System</h2>
        <audio controls>
            <source src="/system.wav" type="audio/wav">
        </audio>
    </div>

</body>
</html>
"""

            data = html.encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )
            self.send_header(
                "Content-Length",
                str(len(data))
            )
            self.end_headers()

            try:
                self.wfile.write(data)
            except BrokenPipeError:
                pass

            return

        filename = self.path.lstrip("/")

        if filename in {
            "narrator.wav",
            "pei_qian.wav",
            "system.wav"
        }:

            file_path = VOICE_DIR / filename

            if not file_path.exists():
                self.send_error(404, "Audio file not found")
                return

            try:
                file_size = file_path.stat().st_size

                self.send_response(200)
                self.send_header("Content-Type", "audio/wav")
                self.send_header("Content-Length", str(file_size))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

                with open(file_path, "rb") as audio:

                    while True:
                        chunk = audio.read(64 * 1024)

                        if not chunk:
                            break

                        self.wfile.write(chunk)

            except (BrokenPipeError, ConnectionResetError):
                pass

            return

        if self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        self.send_error(404)


if not VOICE_DIR.exists():
    print("ERROR: voice_tests directory not found.")
    raise SystemExit(1)


print("=" * 70)
print("ELIZA READER")
print("Female Voice Casting Test")
print("=" * 70)
print()

print("Narrator : en_US-lessac-medium")
print("Pei Qian : en_US-kristin-medium")
print("System   : en_US-amy-medium")
print()

print(f"Starting server on port {PORT}...")
print("Open the forwarded port in your browser.")
print("Press CTRL+C to stop.")
print()


server = ThreadingHTTPServer((HOST, PORT), VoicePlayerHandler)

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped.")
    server.server_close()