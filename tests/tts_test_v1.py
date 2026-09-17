import subprocess
from pathlib import Path


MODEL = "models/en_US-lessac-medium.onnx"
OUTPUT = "audio_segments/test_001.wav"

TEXT = "2009?!"


def main():

    output_path = Path(OUTPUT)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    command = [
        "python",
        "-m",
        "piper",
        "--model",
        MODEL,
        "--output_file",
        str(output_path),
    ]

    print("=" * 60)
    print("ELIZA READER")
    print("Piper TTS Smoke Test")
    print("=" * 60)

    print()
    print(f"Model : {MODEL}")
    print(f"Text  : {TEXT}")
    print(f"Output: {OUTPUT}")
    print()

    result = subprocess.run(
        command,
        input=TEXT,
        text=True,
        capture_output=True
    )

    if result.returncode != 0:

        print("TTS FAILED")
        print()
        print(result.stderr)
        return

    if not output_path.exists():

        print(
            "TTS finished, but the WAV file "
            "was not created."
        )

        return

    print("TTS SUCCESS")
    print()
    print(
        f"Audio created: {OUTPUT}"
    )

    print(
        f"File size: "
        f"{output_path.stat().st_size:,} bytes"
    )


if __name__ == "__main__":
    main()