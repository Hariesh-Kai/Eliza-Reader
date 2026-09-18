from pathlib import Path
import wave
import sys


AUDIO_DIR = Path("audio/segments")
OUTPUT_FILE = Path("audio/chapters/chapter_001.wav")


def read_wav_info(path):
    with wave.open(str(path), "rb") as wf:
        return {
            "channels": wf.getnchannels(),
            "sample_width": wf.getsampwidth(),
            "frame_rate": wf.getframerate(),
            "frames": wf.getnframes(),
        }


def stitch_audio():
    files = [
        f for f in AUDIO_DIR.glob("*.wav")
        if f.stem.split("_")[0].isdigit()
    ]

    files = sorted(
        files,
        key=lambda p: int(p.stem.split("_")[0])
    )

    if not files:
        print("No audio files found.")
        return False

    print("=" * 70)
    print("ELIZA READER")
    print("Audio Stitcher V1")
    print("=" * 70)
    print()

    print(f"Found {len(files)} audio segments.")
    print()

    first_info = read_wav_info(files[0])

    with wave.open(str(OUTPUT_FILE), "wb") as output:

        output.setnchannels(first_info["channels"])
        output.setsampwidth(first_info["sample_width"])
        output.setframerate(first_info["frame_rate"])

        for index, path in enumerate(files, start=1):

            info = read_wav_info(path)

            # Make sure every file has compatible WAV parameters
            if (
                info["channels"] != first_info["channels"]
                or info["sample_width"] != first_info["sample_width"]
                or info["frame_rate"] != first_info["frame_rate"]
            ):
                print(f"ERROR: Audio format mismatch: {path}")
                return False

            print(f"[{index:03}] Adding {path.name}")

            with wave.open(str(path), "rb") as input_wav:
                output.writeframes(input_wav.readframes(input_wav.getnframes()))

    print()
    print("=" * 70)
    print("AUDIO STITCHING COMPLETE")
    print("=" * 70)
    print()
    print(f"Segments : {len(files)}")
    print(f"Output   : {OUTPUT_FILE}")
    print(f"Size     : {OUTPUT_FILE.stat().st_size:,} bytes")
    print()

    return True


if __name__ == "__main__":
    success = stitch_audio()

    if not success:
        sys.exit(1)