from pathlib import Path
import wave


AUDIO_DIR = Path("audio_segments")
OUTPUT_FILE = Path("chapter_001.wav")


def get_audio_segments():

    files = [
        f
        for f in AUDIO_DIR.glob("*.wav")
        if (
            f.stem.split("_")[0].isdigit()
            and (
                "_narrator_001" in f.stem
                or "_voice_001" in f.stem
                or "_system_001" in f.stem
            )
        )
    ]

    files.sort(
        key=lambda p: int(
            p.stem.split("_")[0]
        )
    )

    return files


def stitch_audio():

    print("=" * 70)
    print("ELIZA READER")
    print("Audio Stitcher V1")
    print("=" * 70)

    print()

    files = get_audio_segments()

    if not files:
        raise FileNotFoundError(
            "No numbered audio segments found."
        )

    print(
        f"Found {len(files)} audio segments."
    )

    print()

    first_file = files[0]

    with wave.open(
        str(first_file),
        "rb"
    ) as first:

        params = first.getparams()

        print(
            f"Audio format : "
            f"{params.nchannels} channel(s), "
            f"{params.sampwidth * 8}-bit, "
            f"{params.framerate} Hz"
        )

    print()

    with wave.open(
        str(OUTPUT_FILE),
        "wb"
    ) as output:

        output.setparams(params)

        for index, file in enumerate(files, start=1):

            print(
                f"[{index:03d}] Adding "
                f"{file.name}"
            )

            with wave.open(
                str(file),
                "rb"
            ) as input_audio:

                # Make sure all segments have
                # compatible audio parameters.
                if (
                    input_audio.getnchannels()
                    != params.nchannels
                    or
                    input_audio.getsampwidth()
                    != params.sampwidth
                    or
                    input_audio.getframerate()
                    != params.framerate
                    or
                    input_audio.getcomptype()
                    != params.comptype
                ):

                    raise ValueError(
                        f"Incompatible audio format: "
                        f"{file}"
                    )

                output.writeframes(
                    input_audio.readframes(
                        input_audio.getnframes()
                    )
                )

    print()

    print("=" * 70)
    print("AUDIO STITCHING COMPLETE")
    print("=" * 70)

    print()

    print(
        f"Segments : {len(files)}"
    )

    print(
        f"Output   : {OUTPUT_FILE}"
    )

    print(
        f"Size     : "
        f"{OUTPUT_FILE.stat().st_size:,} bytes"
    )

    print()


if __name__ == "__main__":
    stitch_audio()