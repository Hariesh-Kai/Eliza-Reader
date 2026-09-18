import json
import subprocess
from pathlib import Path


# ============================================================
# ELIZA READER
# Delivery-aware TTS V1
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DELIVERY_FILE = Path("data/planning/delivery_plan_v1.json")
VOICE_PLAN_FILE = Path("data/planning/voice_plan_v1.json")

AUDIO_DIR = Path("audio/segments")


# ------------------------------------------------------------
# Female Piper voice models
# ------------------------------------------------------------

VOICE_MODELS = {
    "narrator_001": BASE_DIR / "models" / "en_US-lessac-medium.onnx",
    "voice_001": BASE_DIR / "models" / "en_US-kristin-medium.onnx",
    "system_001": BASE_DIR / "models" / "en_US-amy-medium.onnx",
}


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

FORCE_REGENERATE = True

DEFAULT_SPEED = 1.0
DEFAULT_VOLUME = 1.0


# ------------------------------------------------------------
# Load JSON
# ------------------------------------------------------------

def load_json(path):

    if not path.exists():
        raise FileNotFoundError(
            f"Missing file: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


# ------------------------------------------------------------
# Convert speed to Piper length scale
# ------------------------------------------------------------

def speed_to_length_scale(speed):

    """
    Piper uses length-scale:

        smaller = faster
        larger  = slower

    Our delivery system uses:

        larger speed = faster
        smaller speed = slower

    Therefore:

        length_scale = 1 / speed
    """

    if speed <= 0:
        speed = DEFAULT_SPEED

    length_scale = 1.0 / speed

    # Keep values within sensible limits.
    length_scale = max(
        0.75,
        min(1.30, length_scale)
    )

    return round(length_scale, 3)


# ------------------------------------------------------------
# Get voice ID
# ------------------------------------------------------------

def get_voice_id(segment, voice_plan_segment):

    # Prefer voice plan.
    if voice_plan_segment:

        voice_id = voice_plan_segment.get(
            "voice_id"
        )

        if voice_id:
            return voice_id

    # Fallback based on segment type.
    segment_type = segment.get(
        "type",
        "NARRATION"
    )

    if segment_type == "SYSTEM":
        return "system_001"

    if segment_type == "DIALOGUE":
        return "voice_001"

    return "narrator_001"


# ------------------------------------------------------------
# Generate one segment
# ------------------------------------------------------------

def generate_segment(
    segment,
    voice_plan_segment,
    output_path
):

    text = segment.get(
        "text",
        ""
    ).strip()

    if not text:
        raise ValueError(
            "Segment contains empty text."
        )

    voice_id = get_voice_id(
        segment,
        voice_plan_segment
    )

    if voice_id not in VOICE_MODELS:
        raise ValueError(
            f"Unknown voice ID: {voice_id}"
        )

    model_path = VOICE_MODELS[voice_id]

    if not model_path.exists():
        raise FileNotFoundError(
            f"Missing Piper model: {model_path}"
        )

    delivery = segment.get(
        "delivery",
        {}
    )

    speed = float(
        delivery.get(
            "speed",
            DEFAULT_SPEED
        )
    )

    volume = float(
        delivery.get(
            "volume",
            DEFAULT_VOLUME
        )
    )

    length_scale = speed_to_length_scale(
        speed
    )

    command = [
        "python",
        "-m",
        "piper",

        "-m",
        str(model_path),

        "--length-scale",
        str(length_scale),

        "--volume",
        str(volume),

        "-f",
        str(output_path),
    ]

    print(
        f"      Voice     : {voice_id}"
    )

    print(
        f"      Speed     : {speed:.2f}"
    )

    print(
        f"      Length    : {length_scale:.3f}"
    )

    print(
        f"      Emotion   : "
        f"{delivery.get('emotion', 'neutral')}"
    )

    print(
        f"      Emphasis  : "
        f"{delivery.get('emphasis', 'normal')}"
    )

    result = subprocess.run(
        command,
        input=text,
        text=True,
        capture_output=True
    )

    if result.returncode != 0:

        error = result.stderr.strip()

        raise RuntimeError(
            f"Piper failed:\n{error}"
        )

    if not output_path.exists():
        raise RuntimeError(
            "Piper completed but output WAV "
            "was not created."
        )


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    print("=" * 70)
    print("ELIZA READER")
    print("Delivery-aware TTS V1")
    print("=" * 70)
    print()

    # --------------------------------------------------------
    # Load delivery plan
    # --------------------------------------------------------

    delivery_data = load_json(
        DELIVERY_FILE
    )

    delivery_segments = delivery_data.get(
        "segments",
        []
    )

    print(
        f"Loaded {len(delivery_segments)} "
        f"delivery segments."
    )

    # --------------------------------------------------------
    # Load voice plan
    # --------------------------------------------------------

    voice_data = load_json(
        VOICE_PLAN_FILE
    )

    voice_segments = voice_data.get(
        "segments",
        []
    )

    print(
        f"Loaded {len(voice_segments)} "
        f"voice-planned segments."
    )

    # --------------------------------------------------------
    # Build voice lookup
    # --------------------------------------------------------

    voice_lookup = {}

    for item in voice_segments:

        segment_number = item.get(
            "segment"
        )

        if segment_number is not None:
            voice_lookup[
                int(segment_number)
            ] = item

    # --------------------------------------------------------
    # Prepare output directory
    # --------------------------------------------------------

    AUDIO_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print()

    completed = 0
    skipped = 0
    failed = 0

    # --------------------------------------------------------
    # Generate audio
    # --------------------------------------------------------

    for index, segment in enumerate(
        delivery_segments,
        start=1
    ):

        segment_number = segment.get(
            "segment"
        )

        if segment_number is None:
            segment_number = index

        segment_number = int(
            segment_number
        )

        segment_type = segment.get(
            "type",
            "UNKNOWN"
        )

        voice_plan_segment = voice_lookup.get(
            segment_number
        )

        if voice_plan_segment:

            voice_id = get_voice_id(
                segment,
                voice_plan_segment
            )

        else:

            voice_id = get_voice_id(
                segment,
                None
            )

        output_path = (
            AUDIO_DIR /
            f"{segment_number:03d}_"
            f"{segment_type.lower()}_"
            f"{voice_id}.wav"
        )

        print(
            f"[{segment_number:03d}] "
            f"{segment_type:<10}"
        )

        # ----------------------------------------------------
        # Skip existing files if force regeneration disabled
        # ----------------------------------------------------

        if (
            not FORCE_REGENERATE
            and output_path.exists()
        ):

            print(
                "      SKIPPED "
                "(already exists)"
            )

            skipped += 1

            continue

        try:

            generate_segment(
                segment,
                voice_plan_segment,
                output_path
            )

            completed += 1

            print(
                "      COMPLETED"
            )

        except Exception as exc:

            failed += 1

            print(
                f"      FAILED: {exc}"
            )

        print()

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("=" * 70)
    print("DELIVERY TTS COMPLETE")
    print("=" * 70)

    print(
        f"Completed : {completed}"
    )

    print(
        f"Skipped   : {skipped}"
    )

    print(
        f"Failed    : {failed}"
    )

    print()

    print(
        f"Output directory : {AUDIO_DIR}"
    )

    print()

    print(
        "NOTE:"
    )

    print(
        "Emotion and emphasis are currently "
        "delivery metadata."
    )

    print(
        "Speed and volume are applied to Piper."
    )

    print("=" * 70)


if __name__ == "__main__":
    main()