import json
import wave
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

PAUSE_PLAN_FILE = Path("data/planning/pause_plan_v2.json")
AUDIO_DIR = Path("audio/segments")
OUTPUT_FILE = Path("audio/chapters/chapter_001.wav")


def load_pause_plan():
    with open(PAUSE_PLAN_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["segments"]


def get_audio_file(segment_number):
    """
    Find the Delivery V1 audio file for a segment.

    Only the current voice IDs are accepted so that
    old V1 audio files cannot accidentally be included.
    """

    matches = []

    for path in AUDIO_DIR.glob("*.wav"):

        stem = path.stem

        parts = stem.split("_")

        if not parts:
            continue

        if not parts[0].isdigit():
            continue

        if int(parts[0]) != segment_number:
            continue

        if (
            "_narrator_001" in stem
            or "_voice_001" in stem
            or "_system_001" in stem
        ):
            matches.append(path)

    if len(matches) == 0:
        raise FileNotFoundError(
            f"No Delivery V1 audio found for segment {segment_number:03d}"
        )

    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple Delivery V1 audio files found for "
            f"segment {segment_number:03d}: "
            f"{[p.name for p in matches]}"
        )

    return matches[0]


def read_audio(path):
    with wave.open(str(path), "rb") as wav:

        params = {
            "channels": wav.getnchannels(),
            "sample_width": wav.getsampwidth(),
            "frame_rate": wav.getframerate(),
            "frames": wav.readframes(wav.getnframes())
        }

    return params


def create_silence(frame_count, channels, sample_width):
    return b"\x00" * (
        frame_count *
        channels *
        sample_width
    )


def main():

    print("=" * 70)
    print("ELIZA READER")
    print("Audio Renderer V2")
    print("=" * 70)
    print()

    segments = load_pause_plan()

    print(f"Loaded {len(segments)} pause-planned segments.")
    print()

    output_audio = None

    audio_format = None

    total_pause = 0.0
    total_audio_frames = 0

    with wave.open(str(OUTPUT_FILE), "wb") as output:

        for index, segment in enumerate(segments, start=1):

            segment_number = segment["segment"]

            pause_before = float(
                segment["pause_before"]
            )

            audio_path = get_audio_file(
                segment_number
            )

            audio = read_audio(audio_path)

            current_format = (
                audio["channels"],
                audio["sample_width"],
                audio["frame_rate"]
            )

            # -------------------------------------------------
            # Establish output format
            # -------------------------------------------------

            if audio_format is None:

                audio_format = current_format

                output.setnchannels(
                    audio["channels"]
                )

                output.setsampwidth(
                    audio["sample_width"]
                )

                output.setframerate(
                    audio["frame_rate"]
                )

            # -------------------------------------------------
            # Validate audio compatibility
            # -------------------------------------------------

            if current_format != audio_format:

                raise RuntimeError(
                    f"Audio format mismatch at segment "
                    f"{segment_number:03d}\n"
                    f"Expected: {audio_format}\n"
                    f"Found:    {current_format}"
                )

            # -------------------------------------------------
            # Add pause
            # -------------------------------------------------

            pause_frames = round(
                pause_before *
                audio["frame_rate"]
            )

            if pause_frames > 0:

                silence = create_silence(
                    pause_frames,
                    audio["channels"],
                    audio["sample_width"]
                )

                output.writeframes(
                    silence
                )

                total_pause += pause_before

            # -------------------------------------------------
            # Add speech
            # -------------------------------------------------

            output.writeframes(
                audio["frames"]
            )

            total_audio_frames += len(
                audio["frames"]
            ) // audio["sample_width"] \
                // audio["channels"]

            print(
                f"[{index:03d}] "
                f"{segment['type']:<10} "
                f"Pause: {pause_before:.2f}s "
                f"Audio: {audio_path.name}"
            )

    # ---------------------------------------------------------
    # Calculate final duration
    # ---------------------------------------------------------

    if audio_format:

        frame_rate = audio_format[2]

        speech_duration = (
            total_audio_frames /
            frame_rate
        )

        final_duration = (
            speech_duration +
            total_pause
        )

    else:

        speech_duration = 0
        final_duration = 0

    print()
    print("=" * 70)
    print("AUDIO RENDERING V2 COMPLETE")
    print("=" * 70)
    print(f"Segments        : {len(segments)}")
    print(f"Speech duration : {speech_duration:.2f}s")
    print(f"Total pause     : {total_pause:.2f}s")
    print(f"Final duration  : {final_duration:.2f}s")
    print(f"Output          : {OUTPUT_FILE.name}")
    print()


if __name__ == "__main__":
    main()
