import json
import subprocess
from pathlib import Path


MANIFEST_FILE = "data/planning/audio_manifest_v1.json"

# Piper model paths.
# We will configure these after downloading the actual models.
VOICE_MODELS = {
    "narrator_001": "models/en_US-lessac-medium.onnx",
    "voice_001": "models/en_US-kristin-medium.onnx",
    "system_001": "models/en_US-amy-medium.onnx",
}
# ============================================================
# LOAD MANIFEST
# ============================================================

def load_manifest():

    path = Path(MANIFEST_FILE)

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {MANIFEST_FILE}"
        )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# SAVE MANIFEST
# ============================================================

def save_manifest(manifest):

    with open(
        MANIFEST_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            manifest,
            f,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# MODEL LOOKUP
# ============================================================

def get_model(voice_id):

    model = VOICE_MODELS.get(
        voice_id
    )

    if not model:

        raise ValueError(
            f"No TTS model configured "
            f"for voice: {voice_id}"
        )

    return Path(model)


# ============================================================
# SYNTHESIZE ONE SEGMENT
# ============================================================

def synthesize(job):

    voice = job[
        "voice"
    ]

    voice_id = voice[
        "voice_id"
    ]

    model_path = get_model(
        voice_id
    )

    if not model_path.exists():

        raise FileNotFoundError(
            f"TTS model not found: "
            f"{model_path}"
        )

    output_path = Path(
        job["audio_file"]
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    text = job[
        "text"
    ]

    print(
        f"Generating segment "
        f"{job['segment']:03d}..."
    )

    print(
        f"Voice: {voice_id}"
    )

    print(
        f"Text : {text[:100]}"
        + ("..." if len(text) > 100 else "")
    )

    speed = voice.get(
        "speed",
        1.0
    )

    # Piper length-scale:
    # < 1.0 = faster
    #   1.0 = normal
    # > 1.0 = slower
    length_scale = 1.0 / speed

    command = [
        "python",
        "-m",
        "piper",

        "--model",
        str(model_path),

        "--output_file",
        str(output_path),

        "--length-scale",
        str(length_scale),
    ]

    process = subprocess.run(
        command,
        input=text,
        text=True,
        capture_output=True
    )

    if process.returncode != 0:

        raise RuntimeError(
            "Piper failed:\n"
            + process.stderr
        )

    if not output_path.exists():

        raise RuntimeError(
            f"Piper completed but "
            f"audio file was not created: "
            f"{output_path}"
        )

    return output_path


# ============================================================
# PROCESS JOBS
# ============================================================

def process_jobs():

    print("=" * 70)
    print("ELIZA READER")
    print("TTS Provider V1")
    print("=" * 70)

    print()

    manifest = load_manifest()

    jobs = manifest.get(
        "jobs",
        []
    )

    print(
        f"Loaded {len(jobs)} TTS jobs."
    )

    print()

    # ========================================================
    # FORCE REGENERATE
    # ========================================================
    # Set to True when voice models or voice assignments change.
    # This will regenerate existing COMPLETED audio files.
    #
    # Set to False later when you want normal resume behavior.
    # ========================================================

    FORCE_REGENERATE = True

    completed = 0
    skipped = 0
    failed = 0

    for job in jobs:

        output_path = Path(
            job["audio_file"]
        )

        # ----------------------------------------------------
        # RESUME SUPPORT
        # ----------------------------------------------------

        if (
            not FORCE_REGENERATE
            and job["status"] == "COMPLETED"
            and output_path.exists()
        ):

            print(
                f"[{job['segment']:03d}] "
                f"Already completed. Skipping."
            )

            skipped += 1

            continue

        # ----------------------------------------------------
        # Generate
        # ----------------------------------------------------

        job["status"] = "GENERATING"

        # Remove previous error if one exists
        job.pop(
            "error",
            None
        )

        save_manifest(
            manifest
        )

        try:

            synthesize(
                job
            )

            job["status"] = "COMPLETED"

            completed += 1

            print(
                f"[{job['segment']:03d}] "
                f"COMPLETED"
            )

        except Exception as error:

            job["status"] = "FAILED"

            job["error"] = str(
                error
            )

            failed += 1

            print(
                f"[{job['segment']:03d}] "
                f"FAILED"
            )

            print(
                f"Error: {error}"
            )

        save_manifest(
            manifest
        )

        print()

    # --------------------------------------------------------
    # Final statistics
    # --------------------------------------------------------

    total_completed = sum(
        1
        for job in jobs
        if job["status"] == "COMPLETED"
    )

    total_failed = sum(
        1
        for job in jobs
        if job["status"] == "FAILED"
    )

    total_pending = sum(
        1
        for job in jobs
        if job["status"] == "PENDING"
    )

    print("=" * 70)
    print("TTS PROCESSING COMPLETE")
    print("=" * 70)

    print()

    print(
        f"Completed : {total_completed}"
    )

    print(
        f"Failed    : {total_failed}"
    )

    print(
        f"Pending   : {total_pending}"
    )

    print()

    print(
        f"Manifest updated: "
        f"{MANIFEST_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    process_jobs()