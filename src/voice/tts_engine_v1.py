import json
import re
from pathlib import Path
from datetime import datetime


INPUT_FILE = "data/planning/voice_plan_v1.json"

OUTPUT_DIR = Path("audio/segments")
MANIFEST_FILE = "data/planning/audio_manifest_v1.json"


# ============================================================
# LOAD JSON
# ============================================================

def load_json(path):

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# SAFE FILE NAME
# ============================================================

def safe_filename(text):

    text = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        text
    )

    text = text.strip("_")

    return text[:80]


# ============================================================
# AUDIO FILE PATH
# ============================================================

def build_audio_path(segment):

    segment_number = segment[
        "segment"
    ]

    segment_type = segment[
        "type"
    ].lower()

    speaker = segment.get(
        "speaker"
    )

    if speaker:

        speaker_name = safe_filename(
            speaker
        )

    else:

        speaker_name = segment[
            "voice_plan"
        ]["voice_role"].lower()

    filename = (
        f"{segment_number:03d}_"
        f"{segment_type}_"
        f"{speaker_name}.wav"
    )

    return OUTPUT_DIR / filename


# ============================================================
# BUILD TTS JOB
# ============================================================

def build_tts_job(segment):

    voice_plan = segment[
        "voice_plan"
    ]

    voice = voice_plan[
        "voice"
    ]

    delivery = voice_plan[
        "delivery"
    ]

    return {

        "segment":
            segment["segment"],

        "paragraph":
            segment["paragraph"],

        "type":
            segment["type"],

        "text":
            segment["text"],

        "voice_role":
            voice_plan["voice_role"],

        "speaker":
            segment.get("speaker"),

        "character":
            segment.get("character"),

        "voice": {

            "voice_id":
                voice.get(
                    "voice_id"
                ),

            "gender":
                voice.get(
                    "voice_gender"
                ),

            "style":
                voice.get(
                    "voice_style"
                ),

            "speed":
                voice.get(
                    "speed",
                    1.0
                ),

            "pitch":
                voice.get(
                    "pitch",
                    0
                ),

            "emotion":
                voice.get(
                    "emotion",
                    "neutral"
                )
        },

        "delivery": {

            "speed":
                delivery.get(
                    "speed",
                    1.0
                ),

            "pause_before":
                delivery.get(
                    "pause_before",
                    0.0
                ),

            "pause_after":
                delivery.get(
                    "pause_after",
                    0.0
                ),

            "emphasis":
                delivery.get(
                    "emphasis",
                    "normal"
                )
        },

        "audio_file":
            str(
                build_audio_path(
                    segment
                )
            ),

        "status":
            "PENDING"
    }


# ============================================================
# BUILD MANIFEST
# ============================================================

def build_manifest():

    print("=" * 70)
    print("ELIZA READER")
    print("TTS Engine V1")
    print("=" * 70)

    print()

    data = load_json(
        INPUT_FILE
    )

    segments = data.get(
        "segments",
        []
    )

    print(
        f"Loaded {len(segments)} voice-planned segments."
    )

    print()

    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    jobs = []

    for segment in segments:

        job = build_tts_job(
            segment
        )

        jobs.append(
            job
        )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    pending = sum(
        1
        for job in jobs
        if job["status"] == "PENDING"
    )

    narrator_jobs = sum(
        1
        for job in jobs
        if job["voice_role"] == "NARRATOR"
    )

    character_jobs = sum(
        1
        for job in jobs
        if job["voice_role"] == "CHARACTER"
    )

    system_jobs = sum(
        1
        for job in jobs
        if job["voice_role"] == "SYSTEM"
    )

    # --------------------------------------------------------
    # Manifest
    # --------------------------------------------------------

    manifest = {

        "version":
            "TTS Engine V1",

        "created_at":
            datetime.now().isoformat(),

        "source":
            INPUT_FILE,

        "output_directory":
            str(OUTPUT_DIR),

        "statistics": {

            "total_jobs":
                len(jobs),

            "pending":
                pending,

            "narrator":
                narrator_jobs,

            "character":
                character_jobs,

            "system":
                system_jobs
        },

        "jobs":
            jobs
    }

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

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    print("=" * 70)
    print("TTS JOB MANIFEST")
    print("=" * 70)

    print()

    print(
        f"Total jobs      : {len(jobs)}"
    )

    print(
        f"Narrator jobs   : {narrator_jobs}"
    )

    print(
        f"Character jobs  : {character_jobs}"
    )

    print(
        f"System jobs     : {system_jobs}"
    )

    print(
        f"Pending         : {pending}"
    )

    print()

    # --------------------------------------------------------
    # Show first few jobs
    # --------------------------------------------------------

    print("=" * 70)
    print("JOB PREVIEW")
    print("=" * 70)

    print()

    for job in jobs[:10]:

        print(
            f"[{job['segment']:03d}] "
            f"{job['type']}"
        )

        print(
            f"Role     : "
            f"{job['voice_role']}"
        )

        print(
            f"Speaker  : "
            f"{job['speaker']}"
        )

        print(
            f"Voice ID : "
            f"{job['voice']['voice_id']}"
        )

        print(
            f"Speed    : "
            f"{job['voice']['speed']}"
        )

        print(
            f"Audio    : "
            f"{job['audio_file']}"
        )

        print()

    print(
        f"Manifest saved to: "
        f"{MANIFEST_FILE}"
    )

    print(
        f"Audio directory: "
        f"{OUTPUT_DIR}/"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    build_manifest()