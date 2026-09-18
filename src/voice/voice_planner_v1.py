import json
from pathlib import Path


INPUT_FILE = "data/analysis/chapter_interpretation.json"
CHARACTER_FILE = "data/analysis/characters.json"
OUTPUT_FILE = "data/planning/voice_plan_v1.json"


# ============================================================
# LOAD JSON
# ============================================================

def load_json(path):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {path}"
        )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# DEFAULT VOICE SETTINGS
# ============================================================

DEFAULT_NARRATOR = {
    "voice_id": "narrator_001",
    "voice_gender": "neutral",
    "voice_style": "natural",
    "speed": 1.0,
    "pitch": 0,
    "emotion": "neutral"
}


DEFAULT_SYSTEM = {
    "voice_id": "system_001",
    "voice_gender": "neutral",
    "voice_style": "synthetic",
    "speed": 1.0,
    "pitch": 0,
    "emotion": "neutral"
}


# ============================================================
# LOAD CHARACTER VOICES
# ============================================================

def load_character_voices(character_data):

    characters = character_data.get(
        "characters",
        {}
    )

    voices = {}

    for character_id, character in characters.items():

        if not isinstance(character, dict):
            continue

        name = character.get("name")

        if not name:
            continue

        voice = character.get(
            "voice",
            {}
        )

        voices[name] = {
            "voice_id": voice.get(
                "voice_id",
                f"voice_{character_id}"
            ),

            "voice_gender": voice.get(
                "voice_gender",
                "neutral"
            ),

            "voice_style": voice.get(
                "voice_style",
                "natural"
            ),

            "speed": voice.get(
                "speed",
                1.0
            ),

            "pitch": voice.get(
                "pitch",
                0
            ),

            "emotion": voice.get(
                "emotion",
                "neutral"
            )
        }

    return voices


# ============================================================
# NARRATION VOICE
# ============================================================

def get_narrator_voice():

    return {
        **DEFAULT_NARRATOR
    }


# ============================================================
# SYSTEM VOICE
# ============================================================

def get_system_voice():

    return {
        **DEFAULT_SYSTEM
    }


# ============================================================
# CHARACTER VOICE
# ============================================================

def get_character_voice(
    character_name,
    character_voices
):

    if not character_name:
        return None

    voice = character_voices.get(
        character_name
    )

    if voice:
        return {
            **voice
        }

    return None


# ============================================================
# SEGMENT PLANNING
# ============================================================

def plan_segment(
    segment,
    character_voices
):

    segment_type = segment["type"]

    # --------------------------------------------------------
    # NARRATION
    # --------------------------------------------------------

    if segment_type == "NARRATION":

        return {
            "voice_role": "NARRATOR",

            "voice": get_narrator_voice(),

            "speaker": None,

            "character": segment.get(
                "character"
            ),

            "emotion_source": "DEFAULT",

            "delivery": {
                "speed": 1.0,
                "pause_before": 0.0,
                "pause_after": 0.15,
                "emphasis": "normal"
            }
        }

    # --------------------------------------------------------
    # DIALOGUE
    # --------------------------------------------------------

    if segment_type == "DIALOGUE":

        speaker = segment.get(
            "speaker"
        )

        voice = get_character_voice(
            speaker,
            character_voices
        )

        if voice is None:

            voice = {
                "voice_id": "unknown_001",
                "voice_gender": "neutral",
                "voice_style": "natural",
                "speed": 1.0,
                "pitch": 0,
                "emotion": "neutral"
            }

        return {
            "voice_role": "CHARACTER",

            "voice": voice,

            "speaker": speaker,

            "character": segment.get(
                "character"
            ),

            "emotion_source": "CHARACTER_DEFAULT",

            "delivery": {
                "speed": voice.get(
                    "speed",
                    1.0
                ),

                "pause_before": 0.10,

                "pause_after": 0.20,

                "emphasis": "normal"
            }
        }

    # --------------------------------------------------------
    # SYSTEM
    # --------------------------------------------------------

    if segment_type == "SYSTEM":

        return {
            "voice_role": "SYSTEM",

            "voice": get_system_voice(),

            "speaker": None,

            "character": None,

            "emotion_source": "SYSTEM_DEFAULT",

            "delivery": {
                "speed": 0.95,
                "pause_before": 0.15,
                "pause_after": 0.25,
                "emphasis": "normal"
            }
        }

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    return {
        "voice_role": "UNKNOWN",

        "voice": get_narrator_voice(),

        "speaker": None,

        "character": None,

        "emotion_source": "UNKNOWN",

        "delivery": {
            "speed": 1.0,
            "pause_before": 0.0,
            "pause_after": 0.15,
            "emphasis": "normal"
        }
    }


# ============================================================
# BUILD VOICE PLAN
# ============================================================

def build_voice_plan():

    print("=" * 70)
    print("ELIZA READER")
    print("Voice Planner V1")
    print("=" * 70)

    print()

    interpretation = load_json(
        INPUT_FILE
    )

    character_data = load_json(
        CHARACTER_FILE
    )

    character_voices = load_character_voices(
        character_data
    )

    segments = interpretation.get(
        "segments",
        []
    )

    print(
        f"Loaded {len(segments)} interpreted segments."
    )

    print(
        f"Loaded {len(character_voices)} character voices."
    )

    print()

    planned_segments = []

    for segment in segments:

        voice_plan = plan_segment(
            segment,
            character_voices
        )

        planned_segments.append({

            "segment":
                segment["segment"],

            "paragraph":
                segment["paragraph"],

            "type":
                segment["type"],

            "text":
                segment["text"],

            "speaker":
                segment.get("speaker"),

            "character":
                segment.get("character"),

            "narrative_focus":
                segment.get(
                    "narrative_focus"
                ),

            "speaker_confidence":
                segment.get(
                    "speaker_confidence"
                ),

            "voice_plan":
                voice_plan
        })

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    narrator_count = sum(
        1
        for item in planned_segments
        if item["voice_plan"]["voice_role"]
        == "NARRATOR"
    )

    character_count = sum(
        1
        for item in planned_segments
        if item["voice_plan"]["voice_role"]
        == "CHARACTER"
    )

    system_count = sum(
        1
        for item in planned_segments
        if item["voice_plan"]["voice_role"]
        == "SYSTEM"
    )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    output = {

        "version":
            "Voice Planner V1",

        "source":
            INPUT_FILE,

        "character_source":
            CHARACTER_FILE,

        "statistics": {

            "total_segments":
                len(planned_segments),

            "narrator_segments":
                narrator_count,

            "character_segments":
                character_count,

            "system_segments":
                system_count
        },

        "voice_assignments":
            character_voices,

        "segments":
            planned_segments
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=4,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    print("=" * 70)
    print("VOICE PLAN")
    print("=" * 70)

    print()

    print(
        f"Total segments      : "
        f"{len(planned_segments)}"
    )

    print(
        f"Narrator segments   : "
        f"{narrator_count}"
    )

    print(
        f"Character segments  : "
        f"{character_count}"
    )

    print(
        f"System segments     : "
        f"{system_count}"
    )

    print()

    # --------------------------------------------------------
    # Dialogue voice inspection
    # --------------------------------------------------------

    print("=" * 70)
    print("CHARACTER VOICE ASSIGNMENTS")
    print("=" * 70)

    print()

    for item in planned_segments:

        if item["type"] != "DIALOGUE":
            continue

        voice = item[
            "voice_plan"
        ]["voice"]

        print(
            f"[{item['segment']:03d}] "
            f"{item['speaker']}"
        )

        print(
            f"Voice ID : "
            f"{voice['voice_id']}"
        )

        print(
            f"Style    : "
            f"{voice['voice_style']}"
        )

        print(
            f"Speed    : "
            f"{voice['speed']}"
        )

        print(
            f"Emotion  : "
            f"{voice['emotion']}"
        )

        print()

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    build_voice_plan()