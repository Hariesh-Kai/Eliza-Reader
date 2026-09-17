import json
import wave
from pathlib import Path


AUDIO_DIR = Path("audio_segments")
PAUSE_PLAN_FILE = "pause_plan_v1.json"
OUTPUT_FILE = Path("chapter_001.wav")


# ============================================================
# LOAD PAUSE PLAN
# ============================================================

def load_pause_plan():

    path = Path(PAUSE_PLAN_FILE)

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {PAUSE_PLAN_FILE}"
        )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    return data["segments"]


# ============================================================
# AUDIO FILE
# ============================================================

def find_audio_file(segment):

    segment_number = segment["segment"]

    matches = list(
        AUDIO_DIR.glob(
            f"{segment_number:03d}_*.wav"
        )
    )

    if not matches:

        raise FileNotFoundError(
            f"No audio file found for "
            f"segment {segment_number:03d}"
        )

    if len(matches) > 1:

        raise RuntimeError(
            f"Multiple audio files found "
            f"for segment {segment_number:03d}: "
            f"{matches}"
        )

    return matches[0]


# ============================================================
# SILENCE
# ============================================================

def create_silence(
    output,
    params,
    duration
):

    if duration <= 0:
        return

    frames = int(
        params.framerate * duration
    )

    silence = (
        b"\x00"
        * frames
        * params.nchannels
        * params.sampwidth
    )

    output.writeframes(
        silence
    )


# ============================================================
# RENDER AUDIO
# ============================================================

def render_audio():

    print("=" * 70)
    print("ELIZA READER")
    print("Audio Renderer V1")
    print("=" * 70)

    print()

    plan = load_pause_plan()

    print(
        f"Loaded {len(plan)} pause entries."
    )

    print()

    if not plan:

        raise RuntimeError(
            "Pause plan is empty."
        )

    first_audio = find_audio_file(
        plan[0]
    )

    with wave.open(
        str(first_audio),
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

    total_pause = 0.0

    with wave.open(
        str(OUTPUT_FILE),
        "wb"
    ) as output:

        output.setparams(
            params
        )

        for index, segment in enumerate(
            plan
        ):

            audio_file = find_audio_file(
                segment
            )

            pause = float(
                segment.get(
                    "pause_before",
                    0.0
                )
            )

            total_pause += pause

            print(
                f"[{index + 1:03d}] "
                f"Segment {segment['segment']:03d} "
                f"{segment['type']:<10} "
                f"Pause: {pause:.2f}s"
            )

            # ------------------------------------------------
            # Add silence before segment
            # ------------------------------------------------

            create_silence(
                output,
                params,
                pause
            )

            # ------------------------------------------------
            # Add actual audio
            # ------------------------------------------------

            with wave.open(
                str(audio_file),
                "rb"
            ) as input_audio:

                # Ensure audio compatibility
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
                        f"{audio_file}"
                    )

                output.writeframes(
                    input_audio.readframes(
                        input_audio.getnframes()
                    )
                )

    print()

    print("=" * 70)
    print("AUDIO RENDERING COMPLETE")
    print("=" * 70)

    print()

    print(
        f"Segments    : {len(plan)}"
    )

    print(
        f"Total pause : {total_pause:.2f}s"
    )

    print(
        f"Output      : {OUTPUT_FILE}"
    )

    print(
        f"Size        : "
        f"{OUTPUT_FILE.stat().st_size:,} bytes"
    )

    print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    render_audio()
