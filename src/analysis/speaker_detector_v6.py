import json
import re
from pathlib import Path


INPUT_FILE = "data/analysis/analyzed_story_v3.txt"
CONTEXT_FILE = "data/analysis/character_context_v2.json"
CHARACTER_FILE = "data/analysis/characters.json"
OUTPUT_FILE = "data/analysis/speaker_analysis_v6.json"


# ============================================================
# SPEECH VERBS
# ============================================================

SPEECH_VERBS = {
    "said",
    "asked",
    "replied",
    "answered",
    "shouted",
    "exclaimed",
    "whispered",
    "cried",
    "called",
    "muttered",
    "remarked",
    "continued",
    "added",
    "responded",
    "yelled",
    "screamed",
    "stated",
    "murmured",
}


# ============================================================
# JSON LOADING
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
# STORY LOADING
# ============================================================

def load_story():
    """
    Load analyzed_story_v3.txt.

    Structure:

        SEGMENT [001]
        PARAGRAPH [001]
        [NARRATION]

        Text
    """

    path = Path(INPUT_FILE)

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_FILE}"
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
                    "text": text,
                })

        current_text = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # ----------------------------------------------------
        # SEGMENT
        # ----------------------------------------------------

        match = re.fullmatch(
            r"SEGMENT\s+\[(\d+)\]",
            line,
            flags=re.IGNORECASE
        )

        if match:

            flush_segment()

            current_segment = int(
                match.group(1)
            )

            current_paragraph = None
            current_type = None

            continue

        # ----------------------------------------------------
        # PARAGRAPH
        # ----------------------------------------------------

        match = re.fullmatch(
            r"PARAGRAPH\s+\[(\d+)\]",
            line,
            flags=re.IGNORECASE
        )

        if match:

            current_paragraph = int(
                match.group(1)
            )

            continue

        # ----------------------------------------------------
        # TYPE
        # ----------------------------------------------------

        match = re.fullmatch(
            r"\[(NARRATION|DIALOGUE|SYSTEM|UNKNOWN)\]",
            line,
            flags=re.IGNORECASE
        )

        if match:

            current_type = match.group(1).upper()

            continue

        # ----------------------------------------------------
        # TEXT
        # ----------------------------------------------------

        if current_type is not None:
            current_text.append(line)

    flush_segment()

    return segments


# ============================================================
# CHARACTER MEMORY
# ============================================================

def load_character_names(character_data):
    """
    Load character names and aliases from the actual
    characters.json structure.
    """

    characters = character_data.get(
        "characters",
        {}
    )

    if not isinstance(
        characters,
        dict
    ):
        return []

    names = []

    for character in characters.values():

        if not isinstance(
            character,
            dict
        ):
            continue

        name = character.get(
            "name"
        )

        if name:
            names.append(name)

        aliases = character.get(
            "aliases",
            []
        )

        if isinstance(
            aliases,
            list
        ):

            for alias in aliases:

                if (
                    isinstance(alias, str)
                    and alias.strip()
                ):
                    names.append(alias)

    return list(
        dict.fromkeys(names)
    )


# ============================================================
# CONTEXT LOADING
# ============================================================

def load_context(context_data):
    """
    Load persistent narrative focus from:

        character_context_v2.json

    Returns:

        {
            paragraph_number: focus_name
        }
    """

    context_map = {}

    segments = context_data.get(
        "segments",
        []
    )

    if not isinstance(
        segments,
        list
    ):
        return context_map

    for segment in segments:

        if not isinstance(
            segment,
            dict
        ):
            continue

        paragraph = segment.get(
            "paragraph"
        )

        focus = segment.get(
            "current_focus"
        )

        if (
            paragraph is not None
            and focus
        ):

            context_map[
                int(paragraph)
            ] = focus

    return context_map


def get_context_focus(
    context_map,
    paragraph
):
    """
    Get the most recent known narrative focus
    at or before the current paragraph.
    """

    available = [
        p
        for p in context_map
        if p <= paragraph
    ]

    if not available:
        return None

    nearest = max(
        available
    )

    return context_map[
        nearest
    ]


# ============================================================
# NAME NORMALIZATION
# ============================================================

def normalize_name(name):

    return re.sub(
        r"\s+",
        " ",
        name.strip().lower()
    )


# ============================================================
# EXPLICIT ATTRIBUTION
# ============================================================

def find_explicit_speaker(
    text,
    character_names
):
    """
    Detect explicit attribution such as:

        Pei Qian said...

        Pei Qian asked...

        ... Pei Qian replied.
    """

    text_lower = text.lower()

    for name in character_names:

        escaped = re.escape(
            normalize_name(name)
        )

        for verb in SPEECH_VERBS:

            # ------------------------------------------------
            # Character + speech verb
            # ------------------------------------------------

            pattern_1 = (
                rf"\b{escaped}\s+{verb}\b"
            )

            if re.search(
                pattern_1,
                text_lower
            ):

                return (
                    name,
                    0.95,
                    "Explicit speaker attribution"
                )

            # ------------------------------------------------
            # Speech verb + character
            # ------------------------------------------------

            pattern_2 = (
                rf"\b{verb}\s+{escaped}\b"
            )

            if re.search(
                pattern_2,
                text_lower
            ):

                return (
                    name,
                    0.95,
                    "Explicit speaker attribution"
                )

    return (
        None,
        0.0,
        None
    )


# ============================================================
# NEARBY NARRATION
# ============================================================

def find_nearby_speaker(
    segments,
    index,
    character_names
):
    """
    Search nearby narration for explicit attribution.

    Only narration is considered.
    System text is ignored.
    """

    start = max(
        0,
        index - 2
    )

    end = min(
        len(segments),
        index + 3
    )

    for i in range(
        start,
        end
    ):

        if i == index:
            continue

        segment = segments[i]

        if segment["type"] != "NARRATION":
            continue

        speaker, confidence, reason = (
            find_explicit_speaker(
                segment["text"],
                character_names
            )
        )

        if speaker:

            return (
                speaker,
                0.85,
                "Nearby narration attribution"
            )

    return (
        None,
        0.0,
        None
    )


# ============================================================
# DIALOGUE CHAIN
# ============================================================

def find_previous_dialogue_speaker(
    results,
    current_paragraph
):
    """
    Find the most recent identified speaker in the
    same paragraph.

    Dialogue chains should not cross paragraph boundaries.
    """

    for previous in reversed(
        results
    ):

        if previous["type"] != "DIALOGUE":
            continue

        if (
            previous.get("paragraph")
            != current_paragraph
        ):
            break

        speaker = previous.get(
            "speaker"
        )

        if (
            speaker
            and speaker != "UNKNOWN"
        ):

            return speaker

    return None


# ============================================================
# SPEAKER RESOLUTION
# ============================================================

def resolve_speaker(
    segments,
    index,
    results,
    character_names,
    context_map
):

    segment = segments[index]

    paragraph = segment[
        "paragraph"
    ]

    text = segment[
        "text"
    ]

    # --------------------------------------------------------
    # 1. EXPLICIT ATTRIBUTION
    # --------------------------------------------------------

    (
        speaker,
        confidence,
        reason
    ) = find_explicit_speaker(
        text,
        character_names
    )

    if speaker:

        return {
            "speaker": speaker,
            "confidence": confidence,
            "method": "EXPLICIT",
            "reason": reason,
        }

    # --------------------------------------------------------
    # 2. NEARBY NARRATION
    # --------------------------------------------------------

    (
        speaker,
        confidence,
        reason
    ) = find_nearby_speaker(
        segments,
        index,
        character_names
    )

    if speaker:

        return {
            "speaker": speaker,
            "confidence": confidence,
            "method": "NEARBY_NARRATION",
            "reason": reason,
        }

    # --------------------------------------------------------
    # 3. DIALOGUE CHAIN
    # --------------------------------------------------------

    speaker = find_previous_dialogue_speaker(
        results,
        paragraph
    )

    if speaker:

        return {
            "speaker": speaker,
            "confidence": 0.70,
            "method": "DIALOGUE_CHAIN",
            "reason": (
                "Inherited from previous "
                "identified dialogue"
            ),
        }

    # --------------------------------------------------------
    # 4. PERSISTENT NARRATIVE FOCUS
    # --------------------------------------------------------

    focus = get_context_focus(
        context_map,
        paragraph
    )

    if focus:

        return {
            "speaker": focus,
            "confidence": 0.60,
            "method": "POV_CONTEXT",
            "reason": (
                "Inherited from persistent "
                "narrative focus"
            ),
        }

    # --------------------------------------------------------
    # 5. UNKNOWN
    # --------------------------------------------------------

    return {
        "speaker": "UNKNOWN",
        "confidence": 0.0,
        "method": "UNKNOWN",
        "reason": (
            "No reliable speaker evidence"
        ),
    }


# ============================================================
# ANALYSIS
# ============================================================

def analyze():

    print("=" * 70)
    print("ELIZA READER")
    print("Speaker Detector V6")
    print("=" * 70)

    print()

    segments = load_story()

    character_data = load_json(
        CHARACTER_FILE
    )

    context_data = load_json(
        CONTEXT_FILE
    )

    character_names = (
        load_character_names(
            character_data
        )
    )

    context_map = load_context(
        context_data
    )

    print(
        f"Loaded {len(segments)} segments."
    )

    print(
        f"Loaded {len(character_names)} "
        f"known characters."
    )

    print(
        f"Loaded {len(context_map)} "
        f"context records."
    )

    results = []

    for index, segment in enumerate(
        segments
    ):

        # ----------------------------------------------------
        # Non-dialogue
        # ----------------------------------------------------

        if segment["type"] != "DIALOGUE":

            results.append({
                **segment,
                "speaker": None,
                "confidence": None,
                "method": None,
                "reason": None,
            })

            continue

        # ----------------------------------------------------
        # Dialogue
        # ----------------------------------------------------

        resolution = resolve_speaker(
            segments,
            index,
            results,
            character_names,
            context_map
        )

        results.append({
            **segment,
            **resolution,
        })

    save_results(
        results
    )


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(
    results
):

    dialogue_results = [
        result
        for result in results
        if result["type"] == "DIALOGUE"
    ]

    identified = sum(
        1
        for result in dialogue_results
        if result["speaker"] != "UNKNOWN"
    )

    unknown = sum(
        1
        for result in dialogue_results
        if result["speaker"] == "UNKNOWN"
    )

    output = {
        "version": "Speaker Detector V6",
        "source": INPUT_FILE,
        "context_source": CONTEXT_FILE,
        "character_source": CHARACTER_FILE,

        "total_segments": len(
            results
        ),

        "dialogue_segments": len(
            dialogue_results
        ),

        "identified": identified,

        "unknown": unknown,

        "segments": results,
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
    # Console report
    # --------------------------------------------------------

    print()

    print("=" * 70)
    print("SPEAKER DETECTION RESULTS")
    print("=" * 70)

    print()

    for result in dialogue_results:

        print(
            f"[{result['segment']:03d}] "
            f"Paragraph "
            f"[{result['paragraph']:03d}]"
        )

        print(
            f"Dialogue: "
            f"{result['text']}"
        )

        print(
            f"Speaker : "
            f"{result['speaker']}"
        )

        print(
            f"Confidence: "
            f"{result['confidence']}"
        )

        print(
            f"Method: "
            f"{result['method']}"
        )

        print(
            f"Reason: "
            f"{result['reason']}"
        )

        print(
            "-" * 70
        )

    print()

    print(
        f"Dialogue segments : "
        f"{len(dialogue_results)}"
    )

    print(
        f"Identified         : "
        f"{identified}"
    )

    print(
        f"Unknown            : "
        f"{unknown}"
    )

    print()

    print(
        f"Results saved to: "
        f"{OUTPUT_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    analyze()
