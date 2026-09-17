import json
from pathlib import Path


STORY_FILE = "analyzed_story_v3.txt"
CONTEXT_FILE = "character_context_v2.json"
SPEAKER_FILE = "speaker_analysis_v6.json"
CHARACTER_FILE = "characters.json"

OUTPUT_FILE = "chapter_interpretation.json"


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
# LOAD STORY
# ============================================================

def load_story():
    """
    Load the already-analyzed story.

    We intentionally do NOT re-analyze the text here.
    Analyzer V3 remains the authority for segment types.
    """

    path = Path(STORY_FILE)

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {STORY_FILE}"
        )

    lines = path.read_text(
        encoding="utf-8"
    ).splitlines()

    segments = []

    current_segment = None
    current_paragraph = None
    current_type = None
    current_text = []

    def flush_segment():

        nonlocal current_text

        if (
            current_segment is not None
            and current_paragraph is not None
            and current_type is not None
            and current_text
        ):

            text = " ".join(
                line.strip()
                for line in current_text
                if line.strip()
            )

            if text:

                segments.append({
                    "segment": current_segment,
                    "paragraph": current_paragraph,
                    "type": current_type,
                    "text": text
                })

        current_text = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # ----------------------------------------------------
        # SEGMENT
        # ----------------------------------------------------

        if line.startswith("SEGMENT ["):

            flush_segment()

            number = (
                line
                .replace("SEGMENT [", "")
                .replace("]", "")
            )

            current_segment = int(number)

            current_paragraph = None
            current_type = None

            continue

        # ----------------------------------------------------
        # PARAGRAPH
        # ----------------------------------------------------

        if line.startswith("PARAGRAPH ["):

            number = (
                line
                .replace("PARAGRAPH [", "")
                .replace("]", "")
            )

            current_paragraph = int(number)

            continue

        # ----------------------------------------------------
        # TYPE
        # ----------------------------------------------------

        if line in {
            "[NARRATION]",
            "[DIALOGUE]",
            "[SYSTEM]",
            "[UNKNOWN]"
        }:

            current_type = (
                line
                .replace("[", "")
                .replace("]", "")
            )

            continue

        # ----------------------------------------------------
        # TEXT
        # ----------------------------------------------------

        if current_type:

            current_text.append(line)

    flush_segment()

    return segments


# ============================================================
# CHARACTER MEMORY
# ============================================================

def load_characters(character_data):

    characters = character_data.get(
        "characters",
        {}
    )

    result = {}

    for character_id, character in characters.items():

        if not isinstance(
            character,
            dict
        ):
            continue

        name = character.get(
            "name"
        )

        if not name:
            continue

        result[character_id] = {
            "name": name,
            "aliases": character.get(
                "aliases",
                []
            ),
            "voice": character.get(
                "voice",
                {})
        }

    return result


# ============================================================
# CONTEXT MAP
# ============================================================

def build_context_map(
    context_data
):

    context_map = {}

    for item in context_data.get(
        "segments",
        []
    ):

        segment_number = item.get(
            "segment"
        )

        if segment_number is None:

            segment_number = item.get(
                "segment_index"
            )

        if segment_number is None:
            continue

        context_map[
            int(segment_number)
        ] = item.get(
            "current_focus"
        )

    return context_map


# ============================================================
# SPEAKER MAP
# ============================================================

def build_speaker_map(
    speaker_data
):

    speaker_map = {}

    for item in speaker_data.get(
        "segments",
        []
    ):

        segment_number = item.get(
            "segment"
        )

        if segment_number is None:
            continue

        speaker_map[
            int(segment_number)
        ] = {
            "speaker": item.get(
                "speaker"
            ),
            "confidence": item.get(
                "confidence"
            ),
            "method": item.get(
                "method"
            ),
            "reason": item.get(
                "reason"
            )
        }

    return speaker_map


# ============================================================
# CHARACTER ID LOOKUP
# ============================================================

def find_character_id(
    character_name,
    characters
):

    if not character_name:
        return None

    target = character_name.strip().lower()

    for character_id, character in characters.items():

        name = character.get(
            "name",
            ""
        )

        if name.strip().lower() == target:

            return character_id

        for alias in character.get(
            "aliases",
            []
        ):

            if (
                isinstance(alias, str)
                and alias.strip().lower()
                == target
            ):

                return character_id

    return None


# ============================================================
# INTERPRET SEGMENT
# ============================================================

def interpret_segment(
    segment,
    context_map,
    speaker_map,
    characters
):

    segment_number = segment[
        "segment"
    ]

    segment_type = segment[
        "type"
    ]

    context = context_map.get(
        segment_number
    )

    speaker_data = speaker_map.get(
        segment_number,
        {}
    )

    speaker = speaker_data.get(
        "speaker"
    )

    character = None

    # --------------------------------------------------------
    # DIALOGUE
    # --------------------------------------------------------

    if segment_type == "DIALOGUE":

        character = speaker

    # --------------------------------------------------------
    # NARRATION
    # --------------------------------------------------------

    elif segment_type == "NARRATION":

        # Narrative focus is retained separately.
        character = context

    # --------------------------------------------------------
    # SYSTEM
    # --------------------------------------------------------

    elif segment_type == "SYSTEM":

        character = None
        speaker = None

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    elif segment_type == "UNKNOWN":

        character = None

    character_id = find_character_id(
        character,
        characters
    )

    return {
        "segment": segment_number,
        "paragraph": segment[
            "paragraph"
        ],

        "type": segment_type,

        "text": segment[
            "text"
        ],

        "character": character,

        "character_id": character_id,

        "speaker": speaker,

        "speaker_confidence":
            speaker_data.get(
                "confidence"
            ),

        "speaker_method":
            speaker_data.get(
                "method"
            ),

        "speaker_reason":
            speaker_data.get(
                "reason"
            ),

        "narrative_focus": context
    }


# ============================================================
# BUILD INTERPRETATION
# ============================================================

def build_interpretation():

    print("=" * 70)
    print("ELIZA READER")
    print("Chapter Interpreter V1")
    print("=" * 70)

    print()

    # --------------------------------------------------------
    # Load all existing outputs
    # --------------------------------------------------------

    segments = load_story()

    context_data = load_json(
        CONTEXT_FILE
    )

    speaker_data = load_json(
        SPEAKER_FILE
    )

    character_data = load_json(
        CHARACTER_FILE
    )

    characters = load_characters(
        character_data
    )

    context_map = build_context_map(
        context_data
    )

    speaker_map = build_speaker_map(
        speaker_data
    )

    print(
        f"Loaded {len(segments)} story segments."
    )

    print(
        f"Loaded {len(context_map)} context records."
    )

    print(
        f"Loaded {len(speaker_map)} speaker records."
    )

    print(
        f"Loaded {len(characters)} characters."
    )

    print()

    # --------------------------------------------------------
    # Build canonical representation
    # --------------------------------------------------------

    interpreted_segments = []

    for segment in segments:

        interpreted = interpret_segment(
            segment,
            context_map,
            speaker_map,
            characters
        )

        interpreted_segments.append(
            interpreted
        )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    narration_count = sum(
        1
        for item in interpreted_segments
        if item["type"] == "NARRATION"
    )

    dialogue_count = sum(
        1
        for item in interpreted_segments
        if item["type"] == "DIALOGUE"
    )

    system_count = sum(
        1
        for item in interpreted_segments
        if item["type"] == "SYSTEM"
    )

    unknown_count = sum(
        1
        for item in interpreted_segments
        if item["type"] == "UNKNOWN"
    )

    identified_speakers = sum(
        1
        for item in interpreted_segments
        if (
            item["type"] == "DIALOGUE"
            and item["speaker"]
            and item["speaker"] != "UNKNOWN"
        )
    )

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    output = {

        "version":
            "Chapter Interpreter V1",

        "sources": {

            "story":
                STORY_FILE,

            "context":
                CONTEXT_FILE,

            "speaker_analysis":
                SPEAKER_FILE,

            "characters":
                CHARACTER_FILE
        },

        "statistics": {

            "total_segments":
                len(interpreted_segments),

            "narration":
                narration_count,

            "dialogue":
                dialogue_count,

            "system":
                system_count,

            "unknown":
                unknown_count,

            "identified_speakers":
                identified_speakers
        },

        "characters":
            characters,

        "segments":
            interpreted_segments
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
    # Print report
    # --------------------------------------------------------

    print("=" * 70)
    print("CHAPTER INTERPRETATION")
    print("=" * 70)

    print()

    print(
        f"Total segments      : {len(interpreted_segments)}"
    )

    print(
        f"Narration           : {narration_count}"
    )

    print(
        f"Dialogue            : {dialogue_count}"
    )

    print(
        f"System              : {system_count}"
    )

    print(
        f"Unknown             : {unknown_count}"
    )

    print(
        f"Identified speakers : {identified_speakers}"
    )

    print()

    # --------------------------------------------------------
    # Dialogue inspection
    # --------------------------------------------------------

    print("=" * 70)
    print("DIALOGUE INTERPRETATION")
    print("=" * 70)

    print()

    for item in interpreted_segments:

        if item["type"] != "DIALOGUE":
            continue

        print(
            f"[{item['segment']:03d}] "
            f"{item['speaker']}"
        )

        print(
            f"Text: {item['text']}"
        )

        print(
            f"Confidence: "
            f"{item['speaker_confidence']}"
        )

        print(
            f"Method: "
            f"{item['speaker_method']}"
        )

        print()

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    build_interpretation()