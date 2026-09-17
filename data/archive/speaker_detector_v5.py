import json
import re
from pathlib import Path


INPUT_FILE = "analyzed_story_v2.txt"
CONTEXT_FILE = "character_context.json"
CHARACTER_FILE = "characters.json"
OUTPUT_FILE = "speaker_analysis_v5.json"


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


def load_json(path):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Could not find {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_story():
    """
    Read analyzed_story_v2.txt and preserve:
    - segment number
    - paragraph number
    - segment type
    - text
    """

    path = Path(INPUT_FILE)

    if not path.exists():
        raise FileNotFoundError(f"Could not find {INPUT_FILE}")

    lines = path.read_text(encoding="utf-8").splitlines()

    segments = []

    current_segment = None
    current_paragraph = None
    current_type = None
    current_text = []

    def flush_segment():
        nonlocal current_text

        if (
            current_segment is not None
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

        match = re.fullmatch(
            r"SEGMENT\s+\[(\d+)\]",
            line,
            flags=re.IGNORECASE
        )

        if match:
            flush_segment()

            current_segment = int(match.group(1))
            current_paragraph = None
            current_type = None

            continue

        match = re.fullmatch(
            r"PARAGRAPH\s+\[(\d+)\]",
            line,
            flags=re.IGNORECASE
        )

        if match:
            current_paragraph = int(match.group(1))
            continue

        match = re.fullmatch(
            r"\[(NARRATION|DIALOGUE|SYSTEM|UNKNOWN)\]",
            line,
            flags=re.IGNORECASE
        )

        if match:
            current_type = match.group(1).upper()
            continue

        if current_type is not None:
            current_text.append(line)

    flush_segment()

    return segments


def get_character_names(characters):
    """
    Extract known character names from the actual
    Character Memory structure.

    characters.json structure:

        {
            "characters": {
                "pei_qian": {
                    "name": "Pei Qian"
                }
            }
        }
    """

    names = []

    if not isinstance(characters, dict):
        return names

    character_dict = characters.get("characters", {})

    if not isinstance(character_dict, dict):
        return names

    for character in character_dict.values():

        if not isinstance(character, dict):
            continue

        name = character.get("name")

        if name:
            names.append(name)

        aliases = character.get("aliases", [])

        if isinstance(aliases, list):
            names.extend(
                alias for alias in aliases
                if isinstance(alias, str) and alias.strip()
            )

    return list(dict.fromkeys(names))


def build_context_map(context_data):
    """
    Build:

        paragraph -> current narrative focus

    from the actual character_context.json structure.

    Character context stores the detailed records under:

        context_data["segments"]
    """

    context_map = {}

    if not isinstance(context_data, dict):
        return context_map

    records = context_data.get("segments", [])

    if not isinstance(records, list):
        return context_map

    for record in records:

        if not isinstance(record, dict):
            continue

        paragraph = record.get("paragraph")
        focus = record.get("current_focus")

        if paragraph is None or not focus:
            continue

        context_map[int(paragraph)] = focus

    return context_map

def get_nearest_context_focus(context_map, paragraph):
    """
    Find the nearest known narrative focus at or before
    the current paragraph.

    This allows dialogue to inherit the established
    narrative focus even when the dialogue paragraph
    itself has no current_focus.
    """

    previous_paragraphs = [
        p for p in context_map
        if p <= paragraph
    ]

    if not previous_paragraphs:
        return None

    nearest = max(previous_paragraphs)

    return context_map[nearest]


def normalize_name(name):
    return re.sub(r"\s+", " ", name.strip().lower())


def find_explicit_speaker(text, character_names):
    """
    Look for explicit dialogue attribution.

    Examples:

        Pei Qian said, "..."
        "..." Pei Qian said.
        Pei Qian asked.
    """

    text_lower = text.lower()

    for name in character_names:

        name_lower = normalize_name(name)

        escaped = re.escape(name_lower)

        for verb in SPEECH_VERBS:

            pattern_1 = rf"\b{escaped}\s+{verb}\b"

            if re.search(pattern_1, text_lower):
                return name, 0.95, "Explicit speaker attribution"

            pattern_2 = rf"\b{verb}\s+{escaped}\b"

            if re.search(pattern_2, text_lower):
                return name, 0.95, "Explicit speaker attribution"

    return None, 0.0, None


def find_nearby_speaker(segments, index, character_names):
    """
    Search nearby narration for explicit attribution.
    """

    start = max(0, index - 2)
    end = min(len(segments), index + 3)

    for i in range(start, end):

        if i == index:
            continue

        segment = segments[i]

        if segment["type"] != "NARRATION":
            continue

        speaker, confidence, reason = find_explicit_speaker(
            segment["text"],
            character_names
        )

        if speaker:
            return speaker, 0.85, "Nearby narration attribution"

    return None, 0.0, None


def find_previous_dialogue_speaker(results, current_paragraph):
    """
    Find the most recent identified dialogue speaker
    within the same paragraph.

    A dialogue chain should not cross into another paragraph.
    """

    for previous in reversed(results):

        if previous["type"] != "DIALOGUE":
            continue

        if previous.get("paragraph") != current_paragraph:
            break

        speaker = previous.get("speaker")

        if speaker and speaker != "UNKNOWN":
            return speaker

    return None


def resolve_speaker(
    segments,
    index,
    results,
    character_names,
    context_map
):
    segment = segments[index]

    text = segment["text"]
    paragraph = segment["paragraph"]

    # ---------------------------------------------------------
    # 1. Explicit attribution
    # ---------------------------------------------------------

    speaker, confidence, reason = find_explicit_speaker(
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

    # ---------------------------------------------------------
    # 2. Nearby narration
    # ---------------------------------------------------------

    speaker, confidence, reason = find_nearby_speaker(
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

    # ---------------------------------------------------------
    # 3. Active dialogue chain
    # ---------------------------------------------------------

    speaker = find_previous_dialogue_speaker(
        results,
        index
    )

    if speaker:
        return {
            "speaker": speaker,
            "confidence": 0.70,
            "method": "DIALOGUE_CHAIN",
            "reason": "Inherited from previous identified dialogue",
        }

    # ---------------------------------------------------------
    # 4. Narrative context / POV
    # ---------------------------------------------------------

    focus = get_nearest_context_focus(
        context_map,
        paragraph
    )

    if focus:

        return {
            "speaker": focus,
            "confidence": 0.60,
            "method": "POV_CONTEXT",
            "reason": "Current narrative focus",
        }

    # ---------------------------------------------------------
    # 5. UNKNOWN
    # ---------------------------------------------------------

    return {
        "speaker": "UNKNOWN",
        "confidence": 0.0,
        "method": "UNKNOWN",
        "reason": "No reliable speaker evidence",
    }


def analyze():
    print("=" * 70)
    print("ELIZA READER")
    print("Speaker Detector V5")
    print("=" * 70)

    print()

    segments = load_story()
    context_data = load_json(CONTEXT_FILE)
    character_data = load_json(CHARACTER_FILE)

    character_names = get_character_names(character_data)
    context_map = build_context_map(context_data)

    print(f"Loaded {len(segments)} segments.")
    print(f"Loaded {len(character_names)} known characters.")
    print(f"Loaded {len(context_map)} context records.")

    print()

    results = []

    for index, segment in enumerate(segments):

        if segment["type"] != "DIALOGUE":
            results.append({
                **segment,
                "speaker": None,
                "confidence": None,
                "method": None,
                "reason": None,
            })
            continue

        resolution = resolve_speaker(
            segments,
            index,
            results,
            character_names,
            context_map
        )

        result = {
            **segment,
            **resolution,
        }

        results.append(result)

    save_results(results)


def save_results(results):

    output = {
        "version": "Speaker Detector V5",
        "total_segments": len(results),
        "dialogue_segments": sum(
            1 for r in results
            if r["type"] == "DIALOGUE"
        ),
        "identified": sum(
            1 for r in results
            if r["type"] == "DIALOGUE"
            and r["speaker"] != "UNKNOWN"
        ),
        "unknown": sum(
            1 for r in results
            if r["type"] == "DIALOGUE"
            and r["speaker"] == "UNKNOWN"
        ),
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
            indent=2,
            ensure_ascii=False
        )

    print()
    print("=" * 70)
    print("SPEAKER DETECTION RESULTS")
    print("=" * 70)

    print()

    dialogue_results = [
        r for r in results
        if r["type"] == "DIALOGUE"
    ]

    for result in dialogue_results:

        print(
            f"[{result['segment']:03d}] "
            f"Paragraph [{result['paragraph']}]"
        )

        print(
            f"Dialogue: {result['text']}"
        )

        print(
            f"Speaker : {result['speaker']}"
        )

        print(
            f"Confidence: {result['confidence']}"
        )

        print(
            f"Method: {result['method']}"
        )

        print(
            f"Reason: {result['reason']}"
        )

        print("-" * 70)

    print()

    print(
        f"Dialogue segments : {len(dialogue_results)}"
    )

    identified = sum(
        1 for r in dialogue_results
        if r["speaker"] != "UNKNOWN"
    )

    unknown = sum(
        1 for r in dialogue_results
        if r["speaker"] == "UNKNOWN"
    )

    print(
        f"Identified         : {identified}"
    )

    print(
        f"Unknown            : {unknown}"
    )

    print()

    print(
        f"Results saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    analyze()