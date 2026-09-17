import re
from pathlib import Path

from character_memory import CharacterMemory


INPUT_FILE = "analyzed_story_v2.txt"
OUTPUT_FILE = "speaker_analysis_v3.txt"
MEMORY_FILE = "characters.json"


# ============================================================
# CONFIGURATION
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
    "told",
}

# Words that indicate a character is likely
# performing an action or thinking.
CHARACTER_ACTION_PATTERNS = [
    r"\b{character}\s+(?:was|is|had|has|did|would|could|began|started|looked|"
    r"thought|wondered|realized|decided|felt|smiled|laughed|nodded|"
    r"considered|contemplated|exclaimed|shouted|asked|said|replied)\b",

    r"\b{character}\b.*\b(?:thought|wondered|realized|decided|considered)\b",
]


# ============================================================
# STORY LOADING
# ============================================================

def load_story():

    path = Path(INPUT_FILE)

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_FILE}"
        )

    text = path.read_text(
        encoding="utf-8"
    )

    segments = []

    blocks = re.split(
        r"\n\s*\n",
        text.strip()
    )

    current_paragraph = None

    for block in blocks:

        lines = block.strip().splitlines()

        if not lines:
            continue

        paragraph_id = None
        segment_type = None
        content = []

        for line in lines:

            line = line.strip()

            match = re.search(
                r"PARAGRAPH\s+\[(\d+)\]",
                line,
                flags=re.IGNORECASE
            )

            if match:

                paragraph_id = match.group(1)

                cleaned = re.sub(
                    r"PARAGRAPH\s+\[\d+\]",
                    "",
                    line,
                    flags=re.IGNORECASE
                ).strip()

                if cleaned:
                    content.append(cleaned)

                continue

            if (
                line.startswith("[")
                and line.endswith("]")
            ):
                segment_type = (
                    line[1:-1].strip()
                )
                continue

            if line:
                content.append(line)

        if segment_type and content:

            segments.append({
                "paragraph": paragraph_id,
                "type": segment_type,
                "text": " ".join(content),
            })

    return segments


# ============================================================
# CHARACTER MEMORY
# ============================================================

def load_characters():

    memory = CharacterMemory(
        memory_file=MEMORY_FILE
    )

    characters = memory.list_characters()

    return memory, characters


# ============================================================
# CHARACTER SEARCH
# ============================================================

def find_character_mentions(
    text,
    characters
):

    found = []

    lower_text = text.lower()

    for character in characters:

        name = character.get(
            "name",
            ""
        ).strip()

        if not name:
            continue

        names = [name]

        names.extend(
            character.get(
                "aliases",
                []
            )
        )

        for alias in names:

            alias = alias.strip()

            if not alias:
                continue

            pattern = (
                r"\b"
                + re.escape(alias.lower())
                + r"\b"
            )

            if re.search(
                pattern,
                lower_text
            ):
                found.append(
                    character
                )
                break

    return found


# ============================================================
# EXPLICIT SPEAKER
# ============================================================

def detect_explicit_speaker(
    text,
    characters
):

    lower_text = text.lower()

    for character in characters:

        name = character.get(
            "name",
            ""
        ).strip()

        if not name:
            continue

        aliases = [
            name
        ]

        aliases.extend(
            character.get(
                "aliases",
                []
            )
        )

        for alias in aliases:

            alias = alias.strip()

            if not alias:
                continue

            for verb in SPEECH_VERBS:

                pattern = (
                    r"\b"
                    + re.escape(alias.lower())
                    + r"\b"
                    r".{0,40}\b"
                    + re.escape(verb)
                    + r"\b"
                )

                if re.search(
                    pattern,
                    lower_text
                ):
                    return character

                pattern_reverse = (
                    r"\b"
                    + re.escape(verb)
                    + r"\b"
                    r".{0,40}\b"
                    + re.escape(alias.lower())
                    + r"\b"
                )

                if re.search(
                    pattern_reverse,
                    lower_text
                ):
                    return character

    return None


# ============================================================
# CONTEXT SCORING
# ============================================================

def score_character_context(
    dialogue_index,
    segments,
    character
):

    score = 0
    reasons = []

    name = character.get(
        "name",
        ""
    ).lower()

    aliases = [
        name
    ]

    aliases.extend(
        alias.lower()
        for alias in character.get(
            "aliases",
            []
        )
    )

    # --------------------------------------------------------
    # Previous narration
    # --------------------------------------------------------

    previous_start = max(
        0,
        dialogue_index - 3
    )

    previous_segments = segments[
        previous_start:dialogue_index
    ]

    for distance, segment in enumerate(
        reversed(previous_segments),
        start=1
    ):

        if segment["type"] != "NARRATION":
            continue

        text = segment["text"].lower()

        mentioned = any(
            re.search(
                r"\b"
                + re.escape(alias)
                + r"\b",
                text
            )
            for alias in aliases
        )

        if not mentioned:
            continue

        # Immediate previous narration is
        # stronger than older narration.
        if distance == 1:
            score += 4
            reasons.append(
                "Character mentioned in immediately preceding narration"
            )

        elif distance == 2:
            score += 3
            reasons.append(
                "Character mentioned two segments before dialogue"
            )

        else:
            score += 1
            reasons.append(
                "Character mentioned in nearby narration"
            )

        # Look for action/thought context.
        for pattern in CHARACTER_ACTION_PATTERNS:

            formatted = pattern.format(
                character=re.escape(
                    character.get("name", "")
                )
            )

            if re.search(
                formatted,
                text,
                flags=re.IGNORECASE
            ):
                score += 2
                reasons.append(
                    "Character performs an action or thought nearby"
                )
                break

    # --------------------------------------------------------
    # Following narration
    # --------------------------------------------------------

    next_end = min(
        len(segments),
        dialogue_index + 4
    )

    next_segments = segments[
        dialogue_index + 1:next_end
    ]

    for distance, segment in enumerate(
        next_segments,
        start=1
    ):

        if segment["type"] != "NARRATION":
            continue

        text = segment["text"].lower()

        mentioned = any(
            re.search(
                r"\b"
                + re.escape(alias)
                + r"\b",
                text
            )
            for alias in aliases
        )

        if not mentioned:
            continue

        if distance == 1:
            score += 3
            reasons.append(
                "Character mentioned in immediately following narration"
            )

        else:
            score += 1
            reasons.append(
                "Character mentioned in nearby following narration"
            )

    return score, reasons


# ============================================================
# PREVIOUS SPEAKER CONTEXT
# ============================================================

def previous_speaker_context(
    dialogue_index,
    results
):

    # Search backwards for the most recent
    # confidently identified dialogue speaker.

    for index in range(
        len(results) - 1,
        -1,
        -1
    ):

        result = results[index]

        if result["segment_index"] >= dialogue_index:
            continue

        if result["speaker"] == "UNKNOWN":
            continue

        if result["confidence"] == "LOW":
            continue

        return result

    return None


# ============================================================
# MAIN SPEAKER DETECTION
# ============================================================

def detect_speaker(
    dialogue_index,
    segments,
    characters,
    previous_results
):

    dialogue = segments[
        dialogue_index
    ]

    text = dialogue["text"]

    # --------------------------------------------------------
    # 1. Explicit attribution
    # --------------------------------------------------------

    explicit = detect_explicit_speaker(
        text,
        characters
    )

    if explicit:

        return {
            "speaker": explicit["name"],
            "character_id": CharacterMemory.make_character_id(
                explicit["name"]
            ),
            "confidence": "HIGH",
            "reason": "Explicit speaker attribution",
            "voice_id": explicit.get(
                "voice",
                {}
            ).get(
                "voice_id"
            ),
        }

    # --------------------------------------------------------
    # 2. Score all characters using context
    # --------------------------------------------------------

    scored = []

    for character in characters:

        score, reasons = (
            score_character_context(
                dialogue_index,
                segments,
                character
            )
        )

        if score > 0:

            scored.append({
                "character": character,
                "score": score,
                "reasons": reasons,
            })

    scored.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    # --------------------------------------------------------
    # 3. Previous speaker continuity
    # --------------------------------------------------------

    previous = previous_speaker_context(
        dialogue_index,
        previous_results
    )

    if previous:

        previous_id = previous.get(
            "character_id"
        )

        for item in scored:

            candidate_id = (
                CharacterMemory.make_character_id(
                    item["character"]["name"]
                )
            )

            if candidate_id == previous_id:

                item["score"] += 2

                item["reasons"].append(
                    "Same speaker as recent identified dialogue"
                )

    # --------------------------------------------------------
    # 4. Evaluate evidence
    # --------------------------------------------------------

    if not scored:

        return {
            "speaker": "UNKNOWN",
            "character_id": None,
            "confidence": "LOW",
            "reason": "No reliable contextual speaker evidence",
            "voice_id": None,
        }

    best = scored[0]

    # Check whether two characters have
    # similar evidence.
    if len(scored) > 1:

        second = scored[1]

        if (
            best["score"]
            - second["score"]
            < 2
        ):

            return {
                "speaker": "UNKNOWN",
                "character_id": None,
                "confidence": "LOW",
                "reason": (
                    "Multiple characters have similar "
                    "contextual evidence"
                ),
                "voice_id": None,
            }

    character = best[
        "character"
    ]

    score = best[
        "score"
    ]

    reasons = best[
        "reasons"
    ]

    # Conservative confidence thresholds.
    if score >= 7:
        confidence = "HIGH"

    elif score >= 4:
        confidence = "MEDIUM"

    else:
        confidence = "LOW"

    if confidence == "LOW":

        return {
            "speaker": "UNKNOWN",
            "character_id": None,
            "confidence": "LOW",
            "reason": "Context evidence is too weak",
            "voice_id": None,
        }

    return {
        "speaker": character["name"],
        "character_id": CharacterMemory.make_character_id(
            character["name"]
        ),
        "confidence": confidence,
        "reason": "; ".join(
            dict.fromkeys(reasons)
        ),
        "voice_id": character.get(
            "voice",
            {}
        ).get(
            "voice_id"
        ),
    }


# ============================================================
# ANALYSIS
# ============================================================

def analyze_speakers(
    segments,
    characters
):

    dialogue_indices = [
        index
        for index, segment in enumerate(
            segments
        )
        if segment["type"] == "DIALOGUE"
    ]

    results = []

    for index in dialogue_indices:

        result = detect_speaker(
            index,
            segments,
            characters,
            results
        )

        result["segment_index"] = index
        result["paragraph"] = segments[
            index
        ]["paragraph"]

        result["dialogue"] = segments[
            index
        ]["text"]

        results.append(
            result
        )

    return results


# ============================================================
# OUTPUT
# ============================================================

def save_results(
    results
):

    lines = []

    lines.append(
        "=" * 70
    )

    lines.append(
        "ELIZA READER - SPEAKER DETECTION V3"
    )

    lines.append(
        "=" * 70
    )

    lines.append("")

    total = len(results)

    identified = sum(
        1
        for result in results
        if result["speaker"] != "UNKNOWN"
    )

    unknown = total - identified

    high = sum(
        1
        for result in results
        if result["confidence"] == "HIGH"
    )

    medium = sum(
        1
        for result in results
        if result["confidence"] == "MEDIUM"
    )

    low = sum(
        1
        for result in results
        if result["confidence"] == "LOW"
    )

    lines.append(
        f"Dialogue segments : {total}"
    )

    lines.append(
        f"Identified        : {identified}"
    )

    lines.append(
        f"Unknown           : {unknown}"
    )

    lines.append(
        f"High confidence   : {high}"
    )

    lines.append(
        f"Medium confidence : {medium}"
    )

    lines.append(
        f"Low confidence    : {low}"
    )

    lines.append("")
    lines.append("-" * 70)
    lines.append("DIALOGUE SPEAKER ANALYSIS")
    lines.append("-" * 70)

    for result in results:

        lines.append("")

        lines.append(
            f"PARAGRAPH [{result['paragraph']}]"
        )

        lines.append(
            "[DIALOGUE]"
        )

        lines.append(
            result["dialogue"]
        )

        lines.append(
            f"Speaker      : "
            f"{result['speaker']}"
        )

        lines.append(
            f"Character ID : "
            f"{result['character_id']}"
        )

        lines.append(
            f"Confidence   : "
            f"{result['confidence']}"
        )

        lines.append(
            f"Reason       : "
            f"{result['reason']}"
        )

        lines.append(
            f"Voice ID     : "
            f"{result['voice_id']}"
        )

    Path(
        OUTPUT_FILE
    ).write_text(
        "\n".join(lines),
        encoding="utf-8"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("ELIZA READER")
    print("Contextual Speaker Detector V3")
    print("=" * 70)

    print()

    print(
        f"Reading: {INPUT_FILE}"
    )

    segments = load_story()

    print(
        f"Loaded {len(segments)} segments."
    )

    memory, characters = (
        load_characters()
    )

    print(
        f"Loaded {len(characters)} "
        f"characters from memory."
    )

    print()
    print("=" * 70)
    print(
        "ELIZA READER - SPEAKER DETECTION V3"
    )
    print("=" * 70)

    results = analyze_speakers(
        segments,
        characters
    )

    total = len(results)

    identified = sum(
        1
        for result in results
        if result["speaker"] != "UNKNOWN"
    )

    unknown = total - identified

    high = sum(
        1
        for result in results
        if result["confidence"] == "HIGH"
    )

    medium = sum(
        1
        for result in results
        if result["confidence"] == "MEDIUM"
    )

    low = sum(
        1
        for result in results
        if result["confidence"] == "LOW"
    )

    print()
    print(
        f"Dialogue segments : {total}"
    )

    print(
        f"Identified        : {identified}"
    )

    print(
        f"Unknown           : {unknown}"
    )

    print(
        f"High confidence   : {high}"
    )

    print(
        f"Medium confidence : {medium}"
    )

    print(
        f"Low confidence    : {low}"
    )

    print()
    print("-" * 70)
    print("DIALOGUE SPEAKER ANALYSIS")
    print("-" * 70)

    for result in results:

        print()

        print(
            f"PARAGRAPH [{result['paragraph']}]"
        )

        print(
            "[DIALOGUE]"
        )

        print(
            result["dialogue"]
        )

        print(
            f"Speaker      : "
            f"{result['speaker']}"
        )

        print(
            f"Character ID : "
            f"{result['character_id']}"
        )

        print(
            f"Confidence   : "
            f"{result['confidence']}"
        )

        print(
            f"Reason       : "
            f"{result['reason']}"
        )

        print(
            f"Voice ID     : "
            f"{result['voice_id']}"
        )

    save_results(
        results
    )

    print()
    print(
        f"Speaker analysis saved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()